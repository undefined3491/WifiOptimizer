"""Repository-local delivery checks; deliberately does not import the plugin."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

DECKY_PREFIX = "decky://decky/plugin/WiFi%20Optimizer/"
REPOSITORY = "undefined3491/WifiOptimizer"
SHIPPED_FILES = (
    "plugin.json", "package.json", "main.py", "decky.pyi", "dist/index.js",
    "dist/index.js.map", "defaults/dispatcher.sh.tmpl",
)


def _stable_version(version: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError(f"invalid Stable version: {version!r}")
    return tuple(int(part) for part in version.split("."))


def validate_release(root: Path, version: str, ref: str, repository: str, deck_tested: bool) -> str:
    _stable_version(version)
    if ref != "refs/heads/main":
        raise ValueError("Stable releases can only be dispatched from main")
    if repository != REPOSITORY:
        raise ValueError(f"release repository must be {REPOSITORY}")
    if not deck_tested:
        raise ValueError("supported-device smoke test attestation is required")
    try:
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read package version: {exc}") from exc
    if not isinstance(package, dict) or package.get("version") != version:
        raise ValueError("release version does not match package.json")
    try:
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read changelog: {exc}") from exc
    release_notes(changelog, version)
    return f"v{version}"


def validate_release_history(version: str, latest_version: str | None, existing_tag: bool, existing_release: bool) -> None:
    candidate = _stable_version(version)
    if existing_tag or existing_release:
        raise ValueError("candidate tag or release already exists")
    if latest_version is not None:
        try:
            latest = _stable_version(latest_version)
        except ValueError as exc:
            raise ValueError("latest Stable release has an invalid version") from exc
        if candidate <= latest:
            raise ValueError("Stable version must be greater than the latest release")


def _gh_api(repository: str, endpoint: str) -> tuple[int, str]:
    if repository != REPOSITORY:
        raise ValueError(f"release repository must be {REPOSITORY}")
    try:
        result = subprocess.run(["gh", "api", "--include", f"repos/{repository}/{endpoint}"], capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("GitHub CLI is unavailable for release history checks") from exc
    response_lines = result.stdout.splitlines()
    response_line = response_lines[0] if response_lines else ""
    match = re.fullmatch(r"HTTP/\d+(?:\.\d+)?\s+(\d{3})(?:\s+.*)?", response_line)
    if not match:
        raise ValueError("GitHub API response has no valid HTTP status header")
    status = int(match.group(1))
    if status == 404:
        return status, ""
    if result.returncode != 0 or status < 200 or status >= 300:
        raise ValueError(f"GitHub API request failed with HTTP {status or 'unknown'}")
    _, separator, body = result.stdout.partition("\r\n\r\n")
    if not separator:
        _, separator, body = result.stdout.partition("\n\n")
    if not separator:
        raise ValueError("GitHub API response has no header/body separator")
    try:
        json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("GitHub API returned invalid JSON") from exc
    return status, body


def get_release_history(repository: str, version: str) -> tuple[str | None, bool, bool]:
    tag = "v" + version
    _stable_version(version)
    latest_status, latest_body = _gh_api(repository, "releases/latest")
    if latest_status == 404:
        latest = None
    else:
        latest_data = json.loads(latest_body)
        latest_tag = latest_data.get("tag_name") if isinstance(latest_data, dict) else None
        if not isinstance(latest_tag, str) or not latest_tag.startswith("v"):
            raise ValueError("latest release response has no Stable tag")
        latest = latest_tag[1:]
    tag_status, _ = _gh_api(repository, f"git/ref/tags/{tag}")
    release_status, _ = _gh_api(repository, f"releases/tags/{tag}")
    return latest, tag_status != 404, release_status != 404


def verify_archive(archive: Path, version: str) -> None:
    _stable_version(version)
    expected_root = f"WifiOptimizer-{version}"
    found: set[str] = set()
    seen: set[str] = set()
    try:
        with tarfile.open(archive, "r:*") as tar:
            for member in tar.getmembers():
                name = member.name.rstrip("/") if member.isdir() else member.name
                parts = name.split("/")
                if name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in parts):
                    raise ValueError(f"unsafe archive path: {name!r}")
                if parts[0] != expected_root or len(parts) == 1 and not member.isdir():
                    raise ValueError("archive does not have the exact release root")
                if name in seen:
                    raise ValueError(f"duplicate archive entry: {name}")
                seen.add(name)
                if not member.isdir() and not member.isfile():
                    raise ValueError(f"unsupported archive entry type: {name}")
                if member.isfile():
                    relative = "/".join(parts[1:])
                    if relative in SHIPPED_FILES:
                        found.add(relative)
    except (OSError, tarfile.TarError) as exc:
        raise ValueError(f"cannot inspect source archive: {exc}") from exc
    missing = sorted(set(SHIPPED_FILES) - found)
    if missing:
        raise ValueError("archive is missing shipped files: " + ", ".join(missing))


def release_notes(changelog: str, version: str) -> str:
    _stable_version(version)
    lines = changelog.splitlines()
    heading = f"## [{version}]"
    starts = [index for index, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        raise ValueError(f"changelog must contain exactly one section for {version}")
    start = starts[0] + 1
    end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise ValueError(f"changelog section for {version} is empty")
    return notes


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
    release_parser = sub.add_parser("validate-release")
    release_parser.add_argument("--version", required=True)
    release_parser.add_argument("--ref", required=True)
    release_parser.add_argument("--repository", required=True)
    release_parser.add_argument("--deck-tested", choices=("true", "false"), required=True)
    archive_parser = sub.add_parser("verify-archive")
    archive_parser.add_argument("--archive", type=Path, required=True)
    archive_parser.add_argument("--version", required=True)
    history_parser = sub.add_parser("release-history")
    history_parser.add_argument("--version", required=True)
    history_parser.add_argument("--repository", required=True)
    notes_parser = sub.add_parser("release-notes")
    notes_parser.add_argument("--version", required=True)
    notes_parser.add_argument("--output", type=Path, required=True)
    sub.add_parser("check-syntax")
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "snapshot":
            snapshot_dist(root, args.output)
        elif args.command == "verify-dist":
            verify_dist(root, args.snapshot)
        elif args.command == "validate-release":
            print(validate_release(root, args.version, args.ref, args.repository, args.deck_tested == "true"))
        elif args.command == "verify-archive":
            verify_archive(args.archive, args.version)
        elif args.command == "release-history":
            history = get_release_history(args.repository, args.version)
            validate_release_history(args.version, *history)
            print(json.dumps(history))
        elif args.command == "release-notes":
            try:
                notes = release_notes((root / "CHANGELOG.md").read_text(encoding="utf-8"), args.version)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(notes + "\n", encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ValueError(f"cannot write release notes: {exc}") from exc
        else:
            check_python_and_shell(root)
    except ValueError as exc:
        print(f"delivery check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
