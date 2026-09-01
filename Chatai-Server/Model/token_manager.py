import asyncio
import json
import math
from dataclasses import dataclass
from pathlib import Path

import litellm

from Config.config import config
from Model.local_model_manager import local_model_manager
from System.log_manager import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ModelTokenProfile:
    context_window: int
    max_output_tokens: int
    safety_margin_tokens: int

    @property
    def input_budget(self) -> int:
        return max(
            1,
            self.context_window
            - self.max_output_tokens
            - self.safety_margin_tokens,
        )


class TokenManager:
    """统一在线模型与本地模型的 token 计数和上下文配置。"""

    DEFAULT_CONTEXT_WINDOW = 32_768
    DEFAULT_MAX_OUTPUT_TOKENS = 1_024
    DEFAULT_SAFETY_MARGIN_TOKENS = 512

    def resolve_profile(
        self,
        runtime: dict,
        model_config: dict,
    ) -> ModelTokenProfile:
        context_window = None
        max_output_tokens = None

        if runtime["is_local_model"]:
            context_window = self._local_context_window(
                model_config["model_name"]
            )
            max_output_tokens = self.DEFAULT_MAX_OUTPUT_TOKENS
        else:
            try:
                model_info = litellm.get_model_info(runtime["model_name"])
                context_window = model_info.get("max_input_tokens")
                max_output_tokens = (
                    model_info.get("max_output_tokens")
                    or model_info.get("max_tokens")
                )
            except Exception as exc:
                logger.warning(
                    "模型 token 元数据不可用，model=%s error=%s",
                    runtime["model_name"],
                    exc,
                )

        context_window = self._positive_int(
            model_config.get("context_window")
        ) or self._positive_int(context_window) or self.DEFAULT_CONTEXT_WINDOW
        max_output_tokens = self._positive_int(
            model_config.get("max_output_tokens")
        ) or self._positive_int(max_output_tokens) or self.DEFAULT_MAX_OUTPUT_TOKENS
        safety_margin_tokens = self._positive_int(
            model_config.get("safety_margin_tokens")
        ) or self.DEFAULT_SAFETY_MARGIN_TOKENS

        if max_output_tokens + safety_margin_tokens >= context_window:
            max_output_tokens = min(
                self.DEFAULT_MAX_OUTPUT_TOKENS,
                max(1, context_window // 4),
            )
            safety_margin_tokens = min(
                self.DEFAULT_SAFETY_MARGIN_TOKENS,
                max(1, context_window // 16),
            )

        return ModelTokenProfile(
            context_window=context_window,
            max_output_tokens=max_output_tokens,
            safety_margin_tokens=safety_margin_tokens,
        )

    async def count_messages(
        self,
        runtime: dict,
        messages: list[dict],
    ) -> int:
        try:
            if runtime["is_local_model"]:
                return await asyncio.to_thread(
                    local_model_manager.get_token_count,
                    messages=messages,
                )
            return int(litellm.token_counter(
                model=runtime["model_name"],
                messages=messages,
            ))
        except Exception as exc:
            logger.warning(
                "消息 token 精确计数失败，使用安全估算，model=%s error=%s",
                runtime["model_name"],
                exc,
            )
            return self._estimate_payload_tokens(messages)

    async def count_text(self, runtime: dict, text: str) -> int:
        if not text:
            return 0
        try:
            if runtime["is_local_model"]:
                return await asyncio.to_thread(
                    local_model_manager.get_token_count,
                    text=text,
                )
            return int(litellm.token_counter(
                model=runtime["model_name"],
                text=text,
            ))
        except Exception as exc:
            logger.warning(
                "文本 token 精确计数失败，使用安全估算，model=%s error=%s",
                runtime["model_name"],
                exc,
            )
            return self._estimate_payload_tokens(text)

    @staticmethod
    def _positive_int(value) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _estimate_payload_tokens(payload) -> int:
        if not isinstance(payload, str):
            payload = json.dumps(payload, ensure_ascii=False, default=str)
        return max(1, math.ceil(len(payload.encode("utf-8")) / 4))

    @staticmethod
    def _local_context_window(model_name: str) -> int | None:
        config_path = Path(config.local_model_path) / model_name / "config.json"
        try:
            model_data = json.loads(config_path.read_text(encoding="utf-8"))
            value = int(model_data.get("max_position_embeddings", 0))
            return value if value > 0 else None
        except Exception as exc:
            logger.warning(
                "本地模型上下文配置读取失败，path=%s error=%s",
                config_path,
                exc,
            )
            return None


token_manager = TokenManager()
