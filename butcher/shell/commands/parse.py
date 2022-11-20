import click

from butcher.data import dump_json
from butcher.parsers.api_parser import parse_docs
from butcher.parsers.consts import DOCS_URL
from butcher.shell.config import ProjectConfig, pass_config


@click.command("parse", help="Parse API docs to cache")
@pass_config
def command_parse(config: ProjectConfig):
    docs = parse_docs(DOCS_URL)
    dump_json(value=docs, path=config.project_dir / "schema" / "schema.json")
