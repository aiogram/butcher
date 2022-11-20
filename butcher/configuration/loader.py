from pathlib import Path
from typing import Type, TypeVar

import yaml
from pydantic import BaseModel

from butcher.common_types import AnyDict

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: Path) -> AnyDict:
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_config(path: Path, model: Type[T]) -> T:
    data = load_yaml(path)
    return model.parse_obj(data)


def dump_yaml(path: Path, data: AnyDict):
    with path.open("w") as f:
        yaml.safe_dump(
            data=data,
            stream=f,
            default_flow_style=False,
            default_style=None,
            width=80,
            sort_keys=False,
        )
