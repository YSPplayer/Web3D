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
from Agent.tools.archive_tools import (
    CreateArchiveTool,
    ExtractArchiveTool,
    ListArchiveTool,
)
from Agent.tools.file_mutation_tools import (
    AppendTextFileTool,
    BulkReplaceTextTool,
    CopyPathTool,
    CreateDirectoryTool,
    DeleteDirectoryContentsTool,
    DeletePathTool,
    MovePathTool,
    RenamePathTool,
    ReplaceTextInFileTool,
    WriteTextFileTool,
)
from Agent.tools.integrity_tools import CalculateFileHashTool, CompareFilesTool
from Agent.tools.network_tools import (
    CheckTcpPortTool,
    DownloadFileTool,
    HttpGetTool,
    PingHostTool,
    ResolveHostTool,
)
from Agent.tools.process_tools import (
    GetProcessDetailTool,
    GetProcessListTool,
    KillProcessTool,
    KillProcessTreeTool,
)
from Agent.tools.system_tools import (
    GetCurrentTimeTool,
    GetCurrentUserTool,
    GetHostnameTool,
    GetOsInfoTool,
    GetPythonRuntimeInfoTool,
    GetSystemMetricsTool,
)


def default_tools():
    return [
        GetCurrentTimeTool(),
        GetHostnameTool(),
        GetCurrentUserTool(),
        GetOsInfoTool(),
        GetPythonRuntimeInfoTool(),
        GetSystemMetricsTool(),
        ListDirectoryTool(),
        FileStatTool(),
        ReadTextFileTool(),
        ReadFileHeadTool(),
        ReadFileTailTool(),
        FindFilesTool(),
        SearchTextTool(),
        GetDiskUsageTool(),
        GetDirectorySizeTool(),
        CalculateFileHashTool(),
        CompareFilesTool(),
        ListArchiveTool(),
        GetProcessListTool(),
        GetProcessDetailTool(),
        KillProcessTool(),
        KillProcessTreeTool(),
        PingHostTool(),
        CheckTcpPortTool(),
        ResolveHostTool(),
        HttpGetTool(),
        CreateDirectoryTool(),
        CopyPathTool(),
        RenamePathTool(),
        WriteTextFileTool(),
        AppendTextFileTool(),
        ReplaceTextInFileTool(),
        CreateArchiveTool(),
        ExtractArchiveTool(),
        DownloadFileTool(),
        MovePathTool(),
        DeletePathTool(),
        DeleteDirectoryContentsTool(),
        BulkReplaceTextTool(),
    ]


__all__ = ["default_tools"]
