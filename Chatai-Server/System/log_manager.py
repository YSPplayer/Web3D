import atexit
import logging
import queue
import sys
import threading
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

from Config.config import config


_LOGGER_NAME = "chatai"
_log_queue: queue.SimpleQueue = queue.SimpleQueue()
_listener: QueueListener | None = None
_lock = threading.Lock()
_base_logger = logging.getLogger(_LOGGER_NAME)
_base_logger.addHandler(logging.NullHandler())
_base_logger.propagate = False


def setup_logging() -> None:
    """初始化非阻塞日志：业务线程入队，监听线程写控制台和滚动文件。"""
    global _listener

    with _lock:
        if _listener is not None:
            return

        config.log_path.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "pid=%(process)d | thread=%(threadName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            config.log_path / "chatai.log",
            maxBytes=20 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        app_logger = logging.getLogger(_LOGGER_NAME)
        app_logger.setLevel(logging.DEBUG)
        app_logger.handlers.clear()
        app_logger.addHandler(QueueHandler(_log_queue))
        app_logger.propagate = False

        _listener = QueueListener(
            _log_queue,
            console_handler,
            file_handler,
            respect_handler_level=True,
        )
        _listener.start()


def get_logger(module_name: str) -> logging.Logger:
    """返回当前模块使用的应用日志器。"""
    return logging.getLogger(f"{_LOGGER_NAME}.{module_name}")


def shutdown_logging() -> None:
    """刷新队列并停止日志监听线程。"""
    global _listener

    with _lock:
        if _listener is None:
            return
        _listener.stop()
        _listener = None


atexit.register(shutdown_logging)
