import asyncio
import time
import psutil

try:
    import pynvml
except Exception:
    pynvml = None

class SystemMonitor:
    def __init__(self):
        self.snapshot = {}
        self.running = False
        self.task = None
        self.gpu_available = False
    
    def init_gpu(self):
        if pynvml is None:
            self.gpu_available = False
            return
        try:
            pynvml.nvmlInit()
            self.gpu_available = pynvml.nvmlDeviceGetCount() > 0
        except Exception:
            self.gpu_available = False

    def collect_gpu(self):
        if not self.gpu_available:
            return None

        gpus = []

        try:
            count = pynvml.nvmlDeviceGetCount()

            for index in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(index)

                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")

                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                gpus.append({
                    "index": index,
                    "name": name,
                    "gpu_percent": utilization.gpu,
                    "memory_percent": round(memory.used / memory.total * 100, 2),
                    "memory_used_mb": round(memory.used / 1024 / 1024, 2),
                    "memory_total_mb": round(memory.total / 1024 / 1024, 2),
                })

        except Exception as exc:
            return {
                "error": str(exc)
            }

        return gpus
        
    def collect_once(self):
            memory = psutil.virtual_memory()

            return {
                "timestamp": int(time.time()),
                "cpu": {
                    "percent": psutil.cpu_percent(interval=None),
                    "count": psutil.cpu_count(),
                },
                "memory": {
                    "percent": memory.percent,
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                },
                "gpu": self.collect_gpu()
            }
    
    async def start(self):
        if self.running:
            return

        self.running = True
        self.init_gpu()

        # 预热一次，否则 psutil.cpu_percent 第一次可能不准
        psutil.cpu_percent(interval=None)

        self.task = asyncio.create_task(self.loop())
    print('已启动硬件资源检测服务')
    async def loop(self):
        while self.running:
            self.snapshot = self.collect_once()
            await asyncio.sleep(1)

    async def stop(self):
        self.running = False

        if self.task:
            self.task.cancel()
            self.task = None
        print('已关闭硬件资源检测服务')
    def get_snapshot(self):
        return self.snapshot
    
system_monitor = SystemMonitor()