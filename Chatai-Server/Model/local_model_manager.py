import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from Config.config import config


class LocalModelManager:
    def __init__(self):
        self.status = "stopped"  # stopped / starting / ready / stopping / error
        self.error = ""
        self.lock = threading.RLock()
        self.chat_lock = threading.Lock()
        self.process: subprocess.Popen | None = None
        self.stdout_thread: threading.Thread | None = None
        self.stderr_thread: threading.Thread | None = None
        self.events: queue.Queue[dict] = queue.Queue()
        self.current_modelname = ""
        self.request_id = 0

    def _is_process_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _set_error(self, message: str):
        self.status = "error"
        self.error = message

    def _reader_stdout(self, process: subprocess.Popen):
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    self.events.put({
                        "type": "log",
                        "message": line
                    })
                    continue

                event_type = event.get("type")
                with self.lock:
                    if event_type == "ready":
                        self.status = "ready"
                        self.error = ""
                    elif event_type == "startup_error":
                        self._set_error(event.get("message", "本地模型启动失败"))

                self.events.put(event)
        except Exception as exc:
            with self.lock:
                if self.status not in ("stopped", "stopping"):
                    self._set_error(str(exc))

    def _reader_stderr(self, process: subprocess.Popen):
        try:
            for line in process.stderr:
                line = line.strip()
                if line:
                    print(f"本地模型子进程: {line}")
        except Exception:
            pass

    def _cleanup_process_refs(self):
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.current_modelname = ""
        self.events = queue.Queue()

    def get_status(self):
        with self.lock:
            if self.process is not None and self.process.poll() is not None:
                if self.status not in ("stopped", "error"):
                    self._set_error(f"本地模型进程已退出，退出码: {self.process.returncode}")
                self.process = None

            return {
                "status": self.status,
                "error": self.error
            }

    def start(self, modelname: str):
        with self.lock:
            if self._is_process_alive():
                if self.status == "ready":
                    return {"code": 200, "message": "模型已经启动"}
                if self.status == "starting":
                    return {"code": 200, "message": "模型正在启动"}
                return {"code": 500, "message": "模型进程状态异常，请先停止后再启动"}

            model_path = config.local_model_path / modelname
            if not model_path.exists():
                self.status = "error"
                self.error = f"本地模型路径不存在: {model_path}"
                return {
                    "code": 500,
                    "message": self.error
                }

            worker_path = Path(__file__).resolve().parent / "local_model_worker.py"
            if not worker_path.exists():
                self.status = "error"
                self.error = f"本地模型工作进程文件不存在: {worker_path}"
                return {
                    "code": 500,
                    "message": self.error
                }

            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            try:
                process = subprocess.Popen(
                    [sys.executable, str(worker_path), str(model_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=env,
                    creationflags=creationflags
                )
            except Exception as exc:
                self.status = "error"
                self.error = str(exc)
                return {
                    "code": 500,
                    "message": f"模型进程启动失败: {exc}"
                }

            self.process = process
            self.status = "starting"
            self.error = ""
            self.current_modelname = modelname
            self.events = queue.Queue()

            self.stdout_thread = threading.Thread(
                target=self._reader_stdout,
                args=(process,),
                daemon=True
            )
            self.stderr_thread = threading.Thread(
                target=self._reader_stderr,
                args=(process,),
                daemon=True
            )
            self.stdout_thread.start()
            self.stderr_thread.start()

        deadline = time.time() + 50
        while time.time() < deadline:
            with self.lock:
                if self.status == "ready":
                    return {"code": 200, "message": "模型启动成功"}
                if self.status == "error":
                    return {"code": 500, "message": self.error}
                if process.poll() is not None:
                    self._set_error(f"本地模型进程已退出，退出码: {process.returncode}")
                    return {"code": 500, "message": self.error}
            time.sleep(0.2)

        return {"code": 200, "message": "模型进程已启动，正在加载模型"}

    def stop(self):
        with self.lock:
            process = self.process
            if process is None:
                self.status = "stopped"
                self.error = ""
                self._cleanup_process_refs()
                return {"code": 200, "message": "模型已关闭"}

            self.status = "stopping"
            self.error = ""

        try:
            if process.poll() is None and process.stdin:
                process.stdin.write(json.dumps({"type": "shutdown"}, ensure_ascii=False) + "\n")
                process.stdin.flush()
        except Exception:
            pass

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception:
                    pass

        with self.lock:
            self.status = "stopped"
            self.error = ""
            self._cleanup_process_refs()

        return {"code": 200, "message": "模型已关闭"}

    def _send_command(self, command: dict):
        process = self.process
        if process is None or process.poll() is not None or process.stdin is None:
            raise RuntimeError("本地模型进程未启动")
        process.stdin.write(json.dumps(command, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def chat_stream(self, messages: list[dict]):
        if not self.chat_lock.acquire(blocking=False):
            raise RuntimeError("本地模型正在生成中")

        request_id = None
        try:
            with self.lock:
                if self.status != "ready" or not self._is_process_alive():
                    raise RuntimeError("本地模型未启动")
                self.request_id += 1
                request_id = self.request_id
                self._send_command({
                    "type": "chat",
                    "id": request_id,
                    "messages": messages
                })

            while True:
                with self.lock:
                    if not self._is_process_alive():
                        raise RuntimeError(self.error or "本地模型进程已退出")

                try:
                    event = self.events.get(timeout=1)
                except queue.Empty:
                    continue

                event_id = event.get("id")
                event_type = event.get("type")

                if event_type in ("ready", "log"):
                    continue

                if event_id != request_id:
                    continue

                if event_type == "delta":
                    yield event.get("content", "")
                elif event_type == "done":
                    break
                elif event_type == "error":
                    raise RuntimeError(event.get("message", "本地模型生成失败"))
        finally:
            self.chat_lock.release()


local_model_manager = LocalModelManager()
