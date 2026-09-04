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
from Agent.tools.patch_tools import ApplyTextPatchTool, PreviewTextPatchTool
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
from Agent.tools.repository_tools import GetFileDiffTool, GetRepositoryStatusTool
from Agent.tools.task_tools import (
    GetTaskStatusTool,
    ListRegisteredTasksTool,
    RunRegisteredTaskTool,
)
from Agent.tools.validation_tools import (
    InspectSqliteSchemaTool,
    ValidateJsonTool,
    ValidatePythonSyntaxTool,
)
from Agent.tools.workspace_tools import (
    CompareDirectorySnapshotsTool,
    GetDirectorySnapshotTool,
    ReadFileRangeTool,
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
        ReadFileRangeTool(),
        GetDirectorySnapshotTool(),
        CompareDirectorySnapshotsTool(),
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
        ValidatePythonSyntaxTool(),
        ValidateJsonTool(),
        InspectSqliteSchemaTool(),
        GetRepositoryStatusTool(),
        GetFileDiffTool(),
        ListRegisteredTasksTool(),
        GetTaskStatusTool(),
        PreviewTextPatchTool(),
        CreateDirectoryTool(),
        CopyPathTool(),
        RenamePathTool(),
        WriteTextFileTool(),
        AppendTextFileTool(),
        ReplaceTextInFileTool(),
        CreateArchiveTool(),
        ExtractArchiveTool(),
        DownloadFileTool(),
        ApplyTextPatchTool(),
        RunRegisteredTaskTool(),
        MovePathTool(),
        DeletePathTool(),
        DeleteDirectoryContentsTool(),
        BulkReplaceTextTool(),
    ]


__all__ = ["default_tools"]
