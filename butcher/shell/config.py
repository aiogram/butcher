from dataclasses import dataclass
from pathlib import Path

import click


@dataclass
class ProjectConfig:
    project_dir: Path
    package_dir: Path
    docs_dir: Path


pass_config = click.make_pass_decorator(ProjectConfig)
