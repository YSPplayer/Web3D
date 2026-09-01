from dataclasses import dataclass

from Model.token_manager import ModelTokenProfile, TokenManager, token_manager


class ContextWindowExceeded(ValueError):
    pass


@dataclass(slots=True)
class PreparedContext:
    messages: list[dict]
    input_tokens: int
    truncated_messages: int = 0
    summary_used: bool = False
    dropped_messages: list[dict] | None = None


class ContextBudgetManager:
    def __init__(self, counter: TokenManager):
        self.counter = counter

    async def prepare_chat(
        self,
        runtime: dict,
        profile: ModelTokenProfile,
        history_messages: list[dict],
        current_user_message: str,
        summary_text: str = "",
    ) -> PreparedContext:
        summary_messages = []
        if summary_text:
            summary_messages.append({
                "role": "system",
                "content": "以下是更早对话的摘要：\n" + summary_text,
            })
        current_message = {
            "role": "user",
            "content": current_user_message,
        }
        mandatory = [*summary_messages, current_message]
        mandatory_tokens = await self.counter.count_messages(runtime, mandatory)
        if mandatory_tokens > profile.input_budget:
            raise ContextWindowExceeded(
                "当前用户消息和必要系统上下文超过模型输入上限"
            )

        turns = self._group_turns(history_messages)
        selected_turn_count = 0
        low = 1
        high = len(turns)
        while low <= high:
            candidate_count = (low + high) // 2
            candidate_turns = turns[-candidate_count:]
            candidate = [
                *summary_messages,
                *self._flatten(candidate_turns),
                current_message,
            ]
            candidate_tokens = await self.counter.count_messages(
                runtime,
                candidate,
            )
            if candidate_tokens <= profile.input_budget:
                selected_turn_count = candidate_count
                low = candidate_count + 1
            else:
                high = candidate_count - 1

        selected_turns = (
            turns[-selected_turn_count:]
            if selected_turn_count
            else []
        )

        selected_count = sum(len(turn) for turn in selected_turns)
        dropped_count = len(history_messages) - selected_count
        dropped_messages = history_messages[:dropped_count]
        messages = [
            *summary_messages,
            *self._flatten(selected_turns),
            current_message,
        ]
        input_tokens = await self.counter.count_messages(runtime, messages)
        return PreparedContext(
            messages=messages,
            input_tokens=input_tokens,
            truncated_messages=dropped_count,
            summary_used=bool(summary_text),
            dropped_messages=dropped_messages,
        )

    async def prepare_agent(
        self,
        runtime: dict,
        profile: ModelTokenProfile,
        messages: list[dict],
    ) -> PreparedContext:
        if not messages:
            return PreparedContext(messages=[], input_tokens=0)

        mandatory_indices = {
            index
            for index, message in enumerate(messages)
            if message.get("role") == "system"
        }
        mandatory_indices.add(len(messages) - 1)

        real_user_indices = [
            index
            for index, message in enumerate(messages)
            if message.get("role") == "user"
            and not self._is_tool_result(message)
            and not self._is_internal_instruction(message)
        ]
        if real_user_indices:
            mandatory_indices.add(real_user_indices[-1])

        tool_result_indices = [
            index
            for index, message in enumerate(messages)
            if self._is_tool_result(message)
        ]
        if tool_result_indices:
            mandatory_indices.add(tool_result_indices[-1])
        selected_indices = set(mandatory_indices)
        mandatory = [
            message
            for index, message in enumerate(messages)
            if index in selected_indices
        ]
        mandatory_tokens = await self.counter.count_messages(runtime, mandatory)
        if mandatory_tokens > profile.input_budget:
            raise ContextWindowExceeded(
                "Agent Skill、当前问题或必要工具结果超过模型输入上限"
            )

        for index in reversed(tool_result_indices[:-1]):
            candidate_indices = selected_indices | {index}
            candidate = [
                message
                for message_index, message in enumerate(messages)
                if message_index in candidate_indices
            ]
            candidate_tokens = await self.counter.count_messages(
                runtime,
                candidate,
            )
            if candidate_tokens <= profile.input_budget:
                selected_indices.add(index)

        optional_indices = [
            index
            for index in range(len(messages))
            if index not in mandatory_indices
            and index not in tool_result_indices
        ]
        optional_turns = self._group_indices_by_turn(
            messages,
            optional_indices,
        )
        for turn_indices in reversed(optional_turns):
            candidate_indices = selected_indices | set(turn_indices)
            candidate = [
                message
                for message_index, message in enumerate(messages)
                if message_index in candidate_indices
            ]
            candidate_tokens = await self.counter.count_messages(
                runtime,
                candidate,
            )
            if candidate_tokens <= profile.input_budget:
                selected_indices.update(turn_indices)

        selected_messages = [
            message
            for index, message in enumerate(messages)
            if index in selected_indices
        ]
        input_tokens = await self.counter.count_messages(
            runtime,
            selected_messages,
        )
        return PreparedContext(
            messages=selected_messages,
            input_tokens=input_tokens,
            truncated_messages=len(messages) - len(selected_messages),
            summary_used=any(
                message.get("role") == "system"
                and str(message.get("content", "")).startswith(
                    "以下是更早对话的摘要"
                )
                for message in selected_messages
            ),
        )

    @staticmethod
    def _group_turns(messages: list[dict]) -> list[list[dict]]:
        turns: list[list[dict]] = []
        current_turn: list[dict] = []
        for message in messages:
            normalized = {
                "role": message["role"],
                "content": message["content"],
            }
            if normalized["role"] == "user" and current_turn:
                turns.append(current_turn)
                current_turn = []
            current_turn.append(normalized)
        if current_turn:
            turns.append(current_turn)
        return turns

    @staticmethod
    def _flatten(turns: list[list[dict]]) -> list[dict]:
        return [message for turn in turns for message in turn]

    @staticmethod
    def _group_indices_by_turn(
        messages: list[dict],
        indices: list[int],
    ) -> list[list[int]]:
        turns: list[list[int]] = []
        current_turn: list[int] = []
        for index in indices:
            if messages[index].get("role") == "user" and current_turn:
                turns.append(current_turn)
                current_turn = []
            current_turn.append(index)
        if current_turn:
            turns.append(current_turn)
        return turns

    @staticmethod
    def _is_tool_result(message: dict) -> bool:
        return str(message.get("content", "")).startswith("<tool_result>")

    @staticmethod
    def _is_internal_instruction(message: dict) -> bool:
        content = str(message.get("content", ""))
        return content.startswith(
            "上一个决策不符合要求"
        ) or content.startswith(
            "请基于上面的真实对话和工具结果"
        )


context_budget_manager = ContextBudgetManager(token_manager)
