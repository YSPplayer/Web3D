import ast

from Agent.user_tools.contract import UserToolUploadMetadata, ValidationReport


def _node_name(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _node_name(node.value)
    return ""


def _class_assignments(class_node: ast.ClassDef) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for node in class_node.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                assignments[node.target.id] = node.value
    return assignments


def _constant_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _validate_top_level(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef)):
            continue
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant) and isinstance(
                node.value.value,
                str,
            ):
                continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
            if (
                isinstance(target, ast.Name)
                and target.id == "tool"
                and isinstance(value, ast.Call)
                and not value.args
                and not value.keywords
            ):
                continue
        errors.append(
            f"第 {getattr(node, 'lineno', 0)} 行包含不允许的模块级执行语句"
        )
    return errors


def validate_user_tool_source(
    source: str,
    metadata: UserToolUploadMetadata,
) -> ValidationReport:
    try:
        tree = ast.parse(source, filename="tool.py", mode="exec")
    except SyntaxError as exc:
        return ValidationReport(
            valid=False,
            errors=(f"Python 语法错误，第 {exc.lineno or 0} 行：{exc.msg}",),
        )

    errors = _validate_top_level(tree)
    classes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    argument_classes = {
        name: node
        for name, node in classes.items()
        if any(_node_name(base) == "BaseModel" for base in node.bases)
    }
    tool_classes = [
        node
        for node in classes.values()
        if any(_node_name(base) == "PythonTool" for base in node.bases)
    ]

    if len(tool_classes) != 1:
        errors.append("必须且只能定义一个继承 PythonTool 的工具类")
        tool_class = None
    else:
        tool_class = tool_classes[0]

    if not argument_classes:
        errors.append("必须定义一个继承 BaseModel 的参数模型")

    arguments_class_name = ""
    if tool_class is not None:
        if tool_class.decorator_list or tool_class.keywords:
            errors.append("工具类不允许使用装饰器或自定义 metaclass")
        assignments = _class_assignments(tool_class)
        expected_strings = {
            "name": metadata.tools_name,
            "display_name": metadata.display_name,
            "description": metadata.description,
            "platform": metadata.platform,
        }
        for field_name, expected_value in expected_strings.items():
            actual_value = _constant_string(assignments.get(field_name))
            if actual_value != expected_value:
                errors.append(f"工具类字段 {field_name} 必须与上传表单一致")

        arguments_class_name = _node_name(assignments.get("args_model"))
        if arguments_class_name not in argument_classes:
            errors.append("args_model 必须引用本文件中的 BaseModel 参数类")

        execute_method = next(
            (
                node
                for node in tool_class.body
                if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "execute"
            ),
            None,
        )
        if execute_method is None:
            errors.append("工具类必须实现 async def execute(...) 方法")
        elif len(execute_method.args.args) < 3:
            errors.append("execute 方法至少需要 self、context、arguments 三个参数")

    exported_class_name = ""
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "tool":
            continue
        if isinstance(node.value, ast.Call):
            exported_class_name = _node_name(node.value.func)

    if tool_class is None or exported_class_name != tool_class.name:
        errors.append("文件末尾必须使用 tool = ToolClass() 导出工具实例")

    return ValidationReport(
        valid=not errors,
        errors=tuple(errors),
        tool_class_name=tool_class.name if tool_class else "",
        arguments_class_name=arguments_class_name,
        entrypoint="tool:tool" if not errors else "",
    )
