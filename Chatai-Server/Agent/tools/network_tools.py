import asyncio
import os
import socket
import struct
import time
import urllib.parse
import urllib.request

from pydantic import BaseModel, ConfigDict, Field

from Agent.base import PythonTool
from Agent.context import ToolContext


class PingHostArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str
    count: int = Field(default=2, ge=1, le=4)


class CheckTcpPortArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: str
    port: int = Field(ge=1, le=65_535)
    timeout_seconds: int = Field(default=3, ge=1, le=10)


class HttpGetArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    timeout_seconds: int = Field(default=5, ge=1, le=15)
    max_bytes: int = Field(default=20_000, ge=1, le=65_536)


def _icmp_checksum(payload: bytes) -> int:
    if len(payload) % 2:
        payload += b"\0"
    total = 0
    for index in range(0, len(payload), 2):
        total += payload[index] + (payload[index + 1] << 8)
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return socket.htons((~total) & 0xFFFF)


def _ping_ipv4(host: str, count: int) -> dict:
    address = socket.gethostbyname(host)
    identifier = os.getpid() & 0xFFFF
    latencies: list[float] = []

    try:
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError as exc:
        raise PermissionError("当前系统不允许创建 ICMP 原始套接字") from exc

    with icmp_socket:
        icmp_socket.settimeout(1.5)
        for sequence in range(1, count + 1):
            sent_at = time.perf_counter()
            body = struct.pack("!d", sent_at) + b"ChataiAgent"
            header = struct.pack("!BBHHH", 8, 0, 0, identifier, sequence)
            checksum = _icmp_checksum(header + body)
            packet = struct.pack("!BBHHH", 8, 0, checksum, identifier, sequence) + body
            icmp_socket.sendto(packet, (address, 0))

            deadline = time.perf_counter() + 1.5
            while True:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    break
                icmp_socket.settimeout(remaining)
                try:
                    response, _ = icmp_socket.recvfrom(65_535)
                except socket.timeout:
                    break
                ip_header_length = (response[0] & 0x0F) * 4
                icmp_header = response[ip_header_length : ip_header_length + 8]
                if len(icmp_header) < 8:
                    continue
                response_type, _, _, response_id, response_sequence = struct.unpack(
                    "!BBHHH", icmp_header
                )
                if response_type == 0 and response_id == identifier and response_sequence == sequence:
                    latencies.append(round((time.perf_counter() - sent_at) * 1000, 2))
                    break

    received = len(latencies)
    return {
        "host": host,
        "address": address,
        "sent": count,
        "received": received,
        "lost": count - received,
        "loss_percent": round((count - received) / count * 100, 2),
        "latency_ms": {
            "min": min(latencies) if latencies else None,
            "avg": round(sum(latencies) / received, 2) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
    }


class PingHostTool(PythonTool[PingHostArguments]):
    name = "ping_host"
    display_name = "Ping 主机"
    description = "使用 Python ICMP 原始套接字检测 IPv4 主机，不调用系统 ping 命令。"
    args_model = PingHostArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: PingHostArguments) -> dict:
        return await asyncio.to_thread(_ping_ipv4, arguments.host, arguments.count)


class CheckTcpPortTool(PythonTool[CheckTcpPortArguments]):
    name = "check_tcp_port"
    display_name = "检测 TCP 端口"
    description = "使用 Python 异步套接字检测指定主机和端口是否可连接。"
    args_model = CheckTcpPortArguments
    timeout_seconds = 10
    max_output_bytes = 32_768

    async def execute(self, context: ToolContext, arguments: CheckTcpPortArguments) -> dict:
        started_at = time.perf_counter()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(arguments.host, arguments.port),
                timeout=arguments.timeout_seconds,
            )
            del reader
            writer.close()
            await writer.wait_closed()
            connected = True
            error = None
        except Exception as exc:
            connected = False
            error = str(exc)
        return {
            "host": arguments.host,
            "port": arguments.port,
            "connected": connected,
            "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "error": error,
        }


class HttpGetTool(PythonTool[HttpGetArguments]):
    name = "http_get"
    display_name = "HTTP GET 请求"
    description = "使用 Python HTTP 客户端发起 GET 请求并限制响应体大小。"
    args_model = HttpGetArguments
    risk_level = "medium"
    timeout_seconds = 15

    async def execute(self, context: ToolContext, arguments: HttpGetArguments) -> dict:
        parsed = urllib.parse.urlparse(arguments.url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("只允许 http 和 https URL")
        if not parsed.hostname:
            raise ValueError("URL 缺少主机名")
        if parsed.username or parsed.password:
            raise ValueError("URL 中不允许携带用户名或密码")

        def request_url() -> dict:
            request = urllib.request.Request(
                arguments.url,
                method="GET",
                headers={"User-Agent": "Chatai-Agent/1.0"},
            )
            with urllib.request.urlopen(request, timeout=arguments.timeout_seconds) as response:
                payload = response.read(arguments.max_bytes + 1)
                truncated = len(payload) > arguments.max_bytes
                payload = payload[: arguments.max_bytes]
                content_type = response.headers.get_content_type()
                charset = response.headers.get_content_charset() or "utf-8"
                return {
                    "url": response.geturl(),
                    "status": response.status,
                    "content_type": content_type,
                    "content": payload.decode(charset, errors="replace"),
                    "truncated": truncated,
                }

        return await asyncio.to_thread(request_url)
