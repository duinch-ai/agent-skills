"""Source-file extensions and ignored directories shared by detector and auditor."""

from __future__ import annotations

SOURCE_EXTENSIONS = {".kt", ".kts", ".dart", ".swift", ".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".rs", ".cpp", ".hpp", ".cc", ".cxx", ".c", ".h"}
IGNORE_DIRS = {
    ".git", ".githooks", ".agents", ".claude", ".cursor", ".idea", ".vscode", "node_modules", "build", "build-*", "cmake-build-*", ".gradle",
    ".dart_tool", ".build", "DerivedData", "dist", ".next", "__pycache__", ".venv", "venv", "vendor", "Pods", "target",
    "library", "libraries", "extern", "external", "third_party", "thirdparty",
}

