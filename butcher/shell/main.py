import logging
import sys
from pathlib import Path

import click
from click import Context

from butcher.shell.commands.apply import group_apply
from butcher.shell.commands.parse import command_parse
from butcher.shell.commands.refresh import command_refresh
from butcher.shell.config import ProjectConfig

logger = logging.getLogger(__name__)


@click.group()
@click.option("--project-dir", type=click.Path(path_type=Path), default=".project")
@click.option("--package-dir", type=click.Path(path_type=Path), default="aiogram")
@click.option("--docs-dir", type=click.Path(path_type=Path), default="docs")
@click.pass_context
def cli(ctx: Context, project_dir: Path, package_dir: Path, docs_dir: Path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)8s: %(message)s",
        stream=sys.stdout,
    )
    ctx.obj = ProjectConfig(
        project_dir=project_dir,
        package_dir=package_dir,
        docs_dir=docs_dir,
    )


def main():
    for command in [
        command_parse,
        command_refresh,
        group_apply,
    ]:
        cli.add_command(command)
    cli(auto_envvar_prefix="PARSER")


if __name__ == "__main__":
    main()
