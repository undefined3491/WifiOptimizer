"""Repository-local delivery checks; deliberately does not import the plugin."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DECKY_PREFIX = "decky://decky/plugin/WiFi%20Optimizer/"


def _json_map(path: Path) -> dict[str, Any]:
    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        data = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read source map {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"source map {path} must contain a JSON object")
    if not isinstance(data.get("sources"), list) or not data["sources"]:
        raise ValueError("source map must contain a non-empty sources array")
    if not isinstance(data.get("sourcesContent"), list) or len(data["sourcesContent"]) != len(data["sources"]):
        raise ValueError("source map sourcesContent must match the sources array")
    if not all(isinstance(source, str) for source in data["sources"]):
        raise ValueError("source map sources entries must be strings")
    if not all(isinstance(content, str) for content in data["sourcesContent"]):
        raise ValueError("source map sourcesContent entries must be strings")
    if not isinstance(data.get("mappings"), str) or not isinstance(data.get("names"), list):
        raise ValueError("source map must contain string mappings and array names")
    return data


def _normalize_source_path(source: str) -> str:
    if source.startswith(DECKY_PREFIX):
        suffix = source[len(DECKY_PREFIX):]
    elif source.startswith("../src/"):
        suffix = source[3:]
    elif source.startswith("../node_modules/"):
        suffix = source[3:]
    elif source.startswith("src/") or source.startswith("node_modules/"):
        suffix = source
    else:
        raise ValueError(f"unsupported source map source path: {source!r}")
    parts = Path(suffix).parts
    if not parts or parts[0] not in {"src", "node_modules"} or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsupported or ambiguous source map source path: {source!r}")
    return "/".join(parts)


def normalize_source_map(data: dict) -> dict:
    """Normalize only approved source prefixes and text line endings."""
    if not isinstance(data, dict):
        raise ValueError("source map must be a JSON object")
    if data.get("version") != 3 or not isinstance(data.get("file"), str):
        raise ValueError("source map must have version 3 and a string file field")
    normalized = dict(data)
    sources = data.get("sources")
    content = data.get("sourcesContent")
    if not isinstance(sources, list) or not sources or not isinstance(content, list) or len(content) != len(sources):
        raise ValueError("source map sources and sourcesContent must be non-empty arrays of equal length")
    if not isinstance(data.get("mappings"), str) or not isinstance(data.get("names"), list):
        raise ValueError("source map must contain string mappings and array names")
    normalized_sources = [_normalize_source_path(source) if isinstance(source, str) else None for source in sources]
    if any(source is None for source in normalized_sources):
        raise ValueError("source map sources entries must be strings")
    if len(set(normalized_sources)) != len(normalized_sources):
        raise ValueError("source map contains ambiguous duplicate source paths")
    if not all(isinstance(text, str) for text in content):
        raise ValueError("source map sourcesContent entries must be strings")
    normalized["sources"] = normalized_sources
    normalized["sourcesContent"] = [text.replace("\r\n", "\n") for text in content]
    return normalized


def check_source_map_sources(root: Path, data: dict) -> None:
    normalized = normalize_source_map(data)
    sources = normalized["sources"]
    if "src/index.tsx" not in sources:
        raise ValueError("source map must embed repository source src/index.tsx")
    for source, embedded in zip(sources, normalized["sourcesContent"]):
        if source.startswith("src/"):
            path = root / Path(source)
            try:
                actual = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
            except (OSError, UnicodeError) as exc:
                raise ValueError(f"source map repository source {source} is missing or unreadable: {exc}") from exc
            if actual != embedded:
                raise ValueError(f"source map embedded repository source is stale: {source}")


def _read_bundle(root: Path) -> str:
    path = root / "dist/index.js"
    try:
        return path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read required bundle dist/index.js: {exc}") from exc


def snapshot_dist(root: Path, output: Path) -> None:
    bundle = _read_bundle(root)
    map_path = root / "dist/index.js.map"
    if not map_path.is_file():
        raise ValueError("required artifact dist/index.js.map is missing")
    data = _json_map(map_path)
    normalized = normalize_source_map(data)
    check_source_map_sources(root, data)
    snapshot = {"bundle": bundle, "source_map": normalized}
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot write artifact snapshot {output}: {exc}") from exc


def verify_dist(root: Path, snapshot: Path) -> None:
    try:
        expected = json.loads(snapshot.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read artifact snapshot {snapshot}: {exc}") from exc
    if not isinstance(expected, dict) or not isinstance(expected.get("bundle"), str) or not isinstance(expected.get("source_map"), dict):
        raise ValueError("artifact snapshot has invalid structure")
    actual_bundle = _read_bundle(root)
    if actual_bundle != expected["bundle"].replace("\r\n", "\n"):
        raise ValueError("rebuilt dist/index.js differs from the committed snapshot")
    actual_map_data = _json_map(root / "dist/index.js.map")
    check_source_map_sources(root, actual_map_data)
    actual_map = normalize_source_map(actual_map_data)
    if actual_map != normalize_source_map(expected["source_map"]):
        raise ValueError("rebuilt dist/index.js.map differs from the committed snapshot")


def _render_update_fstring(tree: ast.Module) -> str:
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "apply_update"]
    if len(functions) != 1:
        raise ValueError("main.py must define exactly one apply_update method")
    assignments = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "script" for target in node.targets)]
    if len(assignments) != 1 or not isinstance(assignments[0].value, ast.JoinedStr):
        raise ValueError("apply_update must assign its generated script as the known f-string")
    pieces = []
    for value in assignments[0].value.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            pieces.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            if value.conversion != -1:
                raise ValueError("unsupported conversion in generated update script f-string")
            if value.format_spec is not None:
                raise ValueError("unsupported format specifier in generated update script f-string")
            # All interpolation points are replaced with inert shell-safe text.
            pieces.append("fixture")
        else:
            raise ValueError("unsupported expression in generated update script")
    return "".join(pieces)


def _bash_check(path: Path, content: str | None = None) -> None:
    bash = shutil.which("bash")
    if not bash:
        raise ValueError("bash is required for shell syntax validation")
    if content is None:
        command = [bash, "-n", str(path)]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    else:
        result = subprocess.run([bash, "-n"], input=content, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"bash syntax error in {path}: {(result.stderr or result.stdout).strip()}")


def check_python_and_shell(root: Path) -> None:
    parsed = {}
    for relative in ("main.py", "decky.pyi"):
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8")
            parsed[relative] = ast.parse(text, filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ValueError(f"Python syntax validation failed for {relative}: {exc}") from exc
    script = _render_update_fstring(parsed["main.py"])
    _bash_check(root / "main.py: apply_update generated script", script)
    for relative in ("install.sh", "defaults/dispatcher.sh.tmpl"):
        path = root / relative
        if not path.is_file():
            raise ValueError(f"required shell file is missing: {relative}")
        _bash_check(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate committed WiFi Optimizer delivery artifacts")
    sub = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = sub.add_parser("snapshot")
    snapshot_parser.add_argument("--output", type=Path, required=True)
    verify_parser = sub.add_parser("verify-dist")
    verify_parser.add_argument("--snapshot", type=Path, required=True)
    sub.add_parser("check-syntax")
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "snapshot":
            snapshot_dist(root, args.output)
        elif args.command == "verify-dist":
            verify_dist(root, args.snapshot)
        else:
            check_python_and_shell(root)
    except ValueError as exc:
        print(f"delivery check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
