from datetime import datetime
from pathlib import Path
from typing import Any

import orjson
import yaml


def _default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise ValueError


def dump_json(value: Any, path: Path, force: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("rb") as f:
            current_content = f.read()
    else:
        current_content = b""

    content = orjson.dumps(value, option=orjson.OPT_INDENT_2, default=_default) + b"\n"
    if content != current_content or force:
        with path.open("wb") as f:
            f.write(content)
        return True
    return False


def load_json(path: Path) -> Any:
    with path.open("rb") as f:
        return orjson.loads(f.read())


def load_yaml(path: Path) -> Any:
    with path.open("r") as f:

        return yaml.safe_load(f)
