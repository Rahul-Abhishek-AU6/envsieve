"""Python AST visitor extracting environment variable lookups."""
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class EnvVarLookup:
    key: str
    file_path: str
    line_number: int
    raw_statement: str
    is_required: bool  # True if subscript os.environ["KEY"] without default, False if .get() with default
    has_default: bool = False
    default_value: Optional[str] = None


class PythonEnvVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.lookups: List[EnvVarLookup] = []

    def _get_raw_line(self, lineno: int) -> str:
        idx = max(0, lineno - 1)
        return self.source_lines[idx].strip() if idx < len(self.source_lines) else ""

    def visit_Subscript(self, node: ast.Subscript):
        # Matches: os.environ["KEY"] or environ["KEY"]
        is_environ = False
        if isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "os":
                is_environ = True
        elif isinstance(node.value, ast.Name) and node.value.id == "environ":
            is_environ = True

        if is_environ:
            key_name = self._extract_string_literal(node.slice)
            if key_name:
                self.lookups.append(
                    EnvVarLookup(
                        key=key_name,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        raw_statement=self._get_raw_line(node.lineno),
                        is_required=True,
                        has_default=False,
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Matches: os.environ.get("KEY", default), os.getenv("KEY", default), getenv("KEY")
        target_name = None
        has_default = len(node.args) > 1

        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name == "get":
                # os.environ.get() or environ.get()
                val = node.func.value
                if isinstance(val, ast.Attribute) and val.attr == "environ":
                    target_name = "environ.get"
                elif isinstance(val, ast.Name) and val.id == "environ":
                    target_name = "environ.get"
            elif attr_name == "getenv":
                # os.getenv()
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                    target_name = "os.getenv"
        elif isinstance(node.func, ast.Name):
            if node.func.id == "getenv":
                target_name = "getenv"

        if target_name and len(node.args) >= 1:
            key_name = self._extract_string_literal(node.args[0])
            if key_name:
                self.lookups.append(
                    EnvVarLookup(
                        key=key_name,
                        file_path=self.file_path,
                        line_number=node.lineno,
                        raw_statement=self._get_raw_line(node.lineno),
                        is_required=not has_default,
                        has_default=has_default,
                    )
                )

        self.generic_visit(node)

    def _extract_string_literal(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        # Older Python 3.7 ast.Str compatibility
        if hasattr(ast, "Str") and isinstance(node, ast.Str):
            return node.s
        return None


def extract_python_env_vars(file_path: Path | str) -> List[EnvVarLookup]:
    """Parse a Python source file and extract environment variable accesses."""
    path = Path(file_path)
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    try:
        tree = ast.parse(content, filename=str(path))
    except (SyntaxError, ValueError):
        return []

    source_lines = content.splitlines()
    visitor = PythonEnvVisitor(str(path), source_lines)
    visitor.visit(tree)
    return visitor.lookups
