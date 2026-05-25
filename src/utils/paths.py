from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return project_root() / "data"


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_project_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None

    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved
    return project_root() / resolved
