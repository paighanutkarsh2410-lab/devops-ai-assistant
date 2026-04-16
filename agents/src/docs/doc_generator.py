"""
Agent Documentation Generator: Auto-generates comprehensive documentation
from code inspection, docstrings, and configuration files.
"""
import os
import ast
import inspect
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AgentDocGenerator:
    """
    Auto-generates agent documentation from source code.
    Extracts docstrings, function signatures, class hierarchies, and config references.
    """

    def __init__(self, agents_dir: str = "agents/src"):
        self._agents_dir = Path(agents_dir)
        self._docs_cache: Dict[str, Dict[str, Any]] = {}

    def generate_all(self) -> Dict[str, Any]:
        """Generate docs for all agent modules."""
        docs = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "modules": [],
        }

        # Scan for Python files
        if self._agents_dir.exists():
            for py_file in sorted(self._agents_dir.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                module_doc = self._analyze_module(py_file)
                if module_doc:
                    docs["modules"].append(module_doc)

        docs["total_modules"] = len(docs["modules"])
        docs["total_classes"] = sum(len(m.get("classes", [])) for m in docs["modules"])
        docs["total_functions"] = sum(len(m.get("functions", [])) for m in docs["modules"])

        return docs

    def _analyze_module(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Analyze a Python module and extract documentation."""
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as e:
            logger.warning(f"[DocGen] Could not parse {filepath}: {e}")
            return None

        module_doc = {
            "name": filepath.stem,
            "file": str(filepath),
            "docstring": ast.get_docstring(tree) or "",
            "classes": [],
            "functions": [],
            "imports": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_doc = self._analyze_class(node)
                module_doc["classes"].append(cls_doc)

            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                fn_doc = self._analyze_function(node)
                module_doc["functions"].append(fn_doc)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module_doc["imports"].append(self._format_import(node))

        return module_doc

    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract class documentation."""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._analyze_function(item))

        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id if isinstance(base.value, ast.Name) else '?'}.{base.attr}")

        return {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "bases": bases,
            "methods": methods,
            "line_number": node.lineno,
        }

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract function documentation."""
        args = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            annotation = ""
            if arg.annotation:
                annotation = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
            args.append({"name": arg.arg, "type": annotation})

        return_type = ""
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)

        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)

        return {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "args": args,
            "return_type": return_type,
            "decorators": decorators,
            "line_number": node.lineno,
            "is_private": node.name.startswith("_"),
        }

    def _format_import(self, node) -> str:
        if isinstance(node, ast.Import):
            return f"import {', '.join(a.name for a in node.names)}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ', '.join(a.name for a in node.names)
            return f"from {module} import {names}"
        return ""

    # ── Markdown Generation ───────────────────────────────────────────

    def generate_markdown(self, module_name: str) -> str:
        """Generate markdown documentation for a specific module."""
        docs = self.generate_all()
        module = next((m for m in docs["modules"] if m["name"] == module_name), None)
        if not module:
            return f"# {module_name}\n\nNo documentation found."

        lines = [f"# {module_name}\n"]
        if module["docstring"]:
            lines.append(f"{module['docstring']}\n")

        for cls in module["classes"]:
            lines.append(f"## Class: `{cls['name']}`")
            if cls["bases"]:
                lines.append(f"Inherits from: {', '.join(cls['bases'])}\n")
            if cls["docstring"]:
                lines.append(f"{cls['docstring']}\n")

            public_methods = [m for m in cls["methods"] if not m["is_private"]]
            if public_methods:
                lines.append("### Methods\n")
                for method in public_methods:
                    args_str = ", ".join(
                        f"{a['name']}: {a['type']}" if a["type"] else a["name"]
                        for a in method["args"]
                    )
                    ret = f" -> {method['return_type']}" if method["return_type"] else ""
                    lines.append(f"#### `{method['name']}({args_str}){ret}`")
                    if method["docstring"]:
                        lines.append(f"{method['docstring']}\n")

        return "\n".join(lines)

    # ── Configuration Reference ───────────────────────────────────────

    def generate_config_reference(self) -> Dict[str, Any]:
        """Generate configuration reference from config files."""
        config_dir = self._agents_dir.parent / "config"
        configs = {}

        if config_dir.exists():
            for yaml_file in config_dir.glob("*.yaml"):
                try:
                    import yaml
                    with open(yaml_file) as f:
                        data = yaml.safe_load(f) or {}
                    configs[yaml_file.stem] = {
                        "file": str(yaml_file),
                        "options": self._flatten_config(data),
                    }
                except Exception:
                    configs[yaml_file.stem] = {"file": str(yaml_file), "options": {}}

        return configs

    def _flatten_config(self, data: dict, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested config into dot-notation keys."""
        result = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten_config(value, full_key))
            else:
                result[full_key] = {
                    "value": value,
                    "type": type(value).__name__,
                }
        return result

    # ── Troubleshooting Guide ─────────────────────────────────────────

    @staticmethod
    def get_troubleshooting_guide() -> List[Dict[str, Any]]:
        return [
            {
                "category": "Agent Not Starting",
                "issues": [
                    {"problem": "Agent fails to initialize", "solution": "Check configuration YAML for syntax errors. Verify all required environment variables are set."},
                    {"problem": "Import errors on startup", "solution": "Run `pip install -r agents/requirements.txt` to ensure all dependencies are installed."},
                    {"problem": "Database connection failed", "solution": "Verify DATABASE_URL environment variable. Check PostgreSQL is running."},
                ],
            },
            {
                "category": "Performance Issues",
                "issues": [
                    {"problem": "Agent processing too slowly", "solution": "Enable caching in performance optimizer. Check LLM API rate limits."},
                    {"problem": "High memory usage", "solution": "Reduce batch sizes in config. Enable incremental processing mode."},
                    {"problem": "API timeouts from Claude", "solution": "Increase timeout settings. Enable LLM response caching."},
                ],
            },
            {
                "category": "Accuracy Issues",
                "issues": [
                    {"problem": "Too many false positive alerts", "solution": "Increase anomaly detection z-score threshold in monitor agent config."},
                    {"problem": "Incorrect root cause analysis", "solution": "Ensure sufficient historical data. Check correlation engine data sources."},
                    {"problem": "Failed remediations", "solution": "Review safety rules. Enable dry-run mode for testing. Check agent permissions."},
                ],
            },
        ]
