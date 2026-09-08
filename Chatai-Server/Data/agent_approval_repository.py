import json


class AgentApprovalRepository:
    """持久化高风险工具审批记录，运行期唤醒由 ApprovalManager 负责。"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def cancel_stale_pending(self) -> None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                now = self.db_manager.now_time()
                connection.execute(
                    """
                    UPDATE agent_tool_approvals
                    SET status = 'cancelled',
                        decision_reason = 'server_restarted',
                        decided_at = ?
                    WHERE status = 'pending'
                    """,
                    (now,),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def create(
        self,
        *,
        approval_id: str,
        request_id: str,
        user_id: int,
        conversation_id: int,
        message_id: int | None,
        tool_id: int,
        tools_name: str,
        display_name: str,
        description: str,
        arguments: dict,
    ) -> None:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                connection.execute(
                    """
                    INSERT INTO agent_tool_approvals (
                        approval_id,
                        request_id,
                        user_id,
                        conversation_id,
                        message_id,
                        tool_id,
                        tools_name,
                        display_name,
                        description,
                        arguments_json,
                        status,
                        requested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """,
                    (
                        approval_id,
                        request_id,
                        user_id,
                        conversation_id,
                        message_id,
                        tool_id,
                        tools_name,
                        display_name,
                        description,
                        json.dumps(arguments, ensure_ascii=False, default=str),
                        self.db_manager.now_time(),
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def resolve(self, approval_id: str, status: str, reason: str) -> bool:
        with self.db_manager.lock:
            connection = self.db_manager.get_db_connection()
            try:
                cursor = connection.execute(
                    """
                    UPDATE agent_tool_approvals
                    SET status = ?,
                        decision_reason = ?,
                        decided_at = ?
                    WHERE approval_id = ? AND status = 'pending'
                    """,
                    (
                        status,
                        reason,
                        self.db_manager.now_time(),
                        approval_id,
                    ),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise
