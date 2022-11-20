from pathlib import Path

from pydantic import BaseModel


class ProjectConfig(BaseModel):
    version: int = 1
    package: Path = Path("aiogram")
    sources: Path = Path(".butcher")
