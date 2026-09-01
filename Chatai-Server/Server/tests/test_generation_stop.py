import asyncio
import unittest

from Server.server import (
    active_generation_lock,
    active_generation_tasks,
    stop_chat_generation,
)


class GenerationStopTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        async with active_generation_lock:
            active_generation_tasks.clear()

    async def test_stop_endpoint_cancels_matching_user_task(self):
        started = asyncio.Event()

        async def wait_forever():
            started.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(wait_forever())
        await started.wait()
        entry = {
            "user_id": 3,
            "task": task,
            "cancel_reason": None,
        }
        async with active_generation_lock:
            active_generation_tasks["request-1"] = entry

        response = await stop_chat_generation(3, "request-1")
        with self.assertRaises(asyncio.CancelledError):
            await task

        self.assertTrue(response["data"]["stopped"])
        self.assertEqual(entry["cancel_reason"], "user_cancelled")

    async def test_stop_endpoint_does_not_cancel_another_users_task(self):
        task = asyncio.create_task(asyncio.sleep(10))
        async with active_generation_lock:
            active_generation_tasks["request-2"] = {
                "user_id": 3,
                "task": task,
                "cancel_reason": None,
            }

        response = await stop_chat_generation(4, "request-2")

        self.assertFalse(response["data"]["stopped"])
        self.assertFalse(task.done())
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task


if __name__ == "__main__":
    unittest.main()
