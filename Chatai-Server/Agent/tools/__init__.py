from Agent.tools.file_tools import (
    FileStatTool,
    FindFilesTool,
    GetDirectorySizeTool,
    GetDiskUsageTool,
    ListDirectoryTool,
    ReadFileHeadTool,
    ReadFileTailTool,
    ReadTextFileTool,
    SearchTextTool,
)
from Agent.tools.network_tools import CheckTcpPortTool, HttpGetTool, PingHostTool
from Agent.tools.process_tools import (
    GetProcessDetailTool,
    GetProcessListTool,
    KillProcessTool,
)
from Agent.tools.system_tools import (
    GetCurrentTimeTool,
    GetCurrentUserTool,
    GetHostnameTool,
    GetOsInfoTool,
)


def default_tools():
    return [
        GetCurrentTimeTool(),
        GetHostnameTool(),
        GetCurrentUserTool(),
        GetOsInfoTool(),
        ListDirectoryTool(),
        FileStatTool(),
        ReadTextFileTool(),
        ReadFileHeadTool(),
        ReadFileTailTool(),
        FindFilesTool(),
        SearchTextTool(),
        GetDiskUsageTool(),
        GetDirectorySizeTool(),
        GetProcessListTool(),
        GetProcessDetailTool(),
        KillProcessTool(),
        PingHostTool(),
        CheckTcpPortTool(),
        HttpGetTool(),
    ]


__all__ = ["default_tools"]
