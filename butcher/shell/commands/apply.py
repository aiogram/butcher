import difflib
import typing as t
from pathlib import Path

import click
from alive_progress import alive_bar
from click import Context, Parameter, pass_context

from butcher.codegen.manager import CodegenManager
from butcher.docs.manager import DocsManager
from butcher.parsers.entities.generator import EntitiesRegistry
from butcher.shell.config import ProjectConfig, pass_config

pass_registry = click.make_pass_decorator(EntitiesRegistry)


class EntityNameType(click.ParamType):
    name = "entity"

    def __init__(self, category: str) -> None:
        self.category = category

    def convert(
        self, value: t.Any, param: t.Optional["Parameter"], ctx: t.Optional["Context"]
    ) -> t.Any:
        registry = ctx.ensure_object(EntitiesRegistry)
        try:
            registry.registry[self.category][value]
        except KeyError:
            self.fail(f"entity {value!r} is not known in category {self.category!r}")
        return super().convert(value, param, ctx)


@click.group("apply")
@pass_config
@pass_context
def group_apply(ctx: Context, config: ProjectConfig):
    """
    Apply changes to the code
    """
    registry = EntitiesRegistry(project_dir=config.project_dir)
    registry.initialize()
    ctx.obj = registry


@group_apply.command("type")
@click.argument(
    "names",
    nargs=-1,
    type=EntityNameType("types"),
)
@click.option(
    "--diff",
    is_flag=True,
    default=False,
    help="Show diff instead of applying changes",
)
@pass_config
@pass_registry
def command_apply_type(
    registry: EntitiesRegistry, config: ProjectConfig, diff: bool, names: tuple[str, ...]
):
    """
    Generate types
    """
    _apply(registry=registry, config=config, diff=diff, category="types", names=names)


@group_apply.command("method")
@click.argument(
    "names",
    nargs=-1,
    type=EntityNameType("methods"),
)
@click.option(
    "--diff",
    is_flag=True,
    default=False,
    help="Show diff instead of applying changes",
)
@pass_config
@pass_registry
def command_apply_method(
    registry: EntitiesRegistry, config: ProjectConfig, diff: bool, names: tuple[str, ...]
):
    """
    Generate methods
    """
    _apply(registry=registry, config=config, diff=diff, category="methods", names=names)


@group_apply.command("enum")
@click.argument(
    "names",
    nargs=-1,
    type=EntityNameType("types"),
)
@click.option(
    "--diff",
    is_flag=True,
    default=False,
    help="Show diff instead of applying changes",
)
@pass_config
@pass_registry
def command_apply_enum(
    registry: EntitiesRegistry, config: ProjectConfig, diff: bool, names: tuple[str, ...]
):
    """
    Generate enums
    """
    _apply(registry=registry, config=config, diff=diff, category="enums", names=names)


@group_apply.command("all")
@click.option(
    "--diff",
    is_flag=True,
    default=False,
    help="Show diff instead of applying changes",
)
@pass_config
@pass_registry
def command_apply_all(registry: EntitiesRegistry, config: ProjectConfig, diff: bool):
    """
    Generate all entities
    """
    _apply(registry=registry, config=config, diff=diff, category="types", names=())
    _apply(registry=registry, config=config, diff=diff, category="methods", names=())
    _apply(registry=registry, config=config, diff=diff, category="enums", names=())


def _apply(
    registry: EntitiesRegistry,
    config: ProjectConfig,
    diff: bool,
    category: str,
    names: tuple[str, ...],
):
    if not names:
        names = tuple(registry.registry[category].keys())
    code_manager = CodegenManager(config=config, registry=registry)
    docs_manager = DocsManager(config=config, registry=registry)
    with alive_bar(
        len(names) + 1,
        # dual_line=True,
        title=f"Rendering {category}...",
        enrich_print=False,
        title_length=20,
    ) as progress:
        for name in names:
            progress.text = f"Rendering {name}"
            code_path, old_code, new_code = code_manager.process_entity(
                category=category, name=name
            )
            docs_path, old_docs, new_docs = docs_manager.process_entity(
                category=category, name=name
            )

            if diff:
                _diff_in_progress(code_path, old_code, new_code, progress)
                _diff_in_progress(docs_path, old_docs, new_docs, progress)
            else:
                code_path.write_text(new_code)
                docs_path.write_text(new_docs)
            progress()

        init_path = code_manager.resolve_package_path(category, "__init__.py")
        init = code_manager.read_code(init_path)
        new_init = code_manager.apply_init(init, names=names)
        if diff:
            _diff_in_progress(code_path, init, new_init, progress)
        else:
            init_path.write_text(new_init)

        docs_index_path, old_index_docs, new_index_docs = docs_manager.process_index(
            category=category
        )
        if diff:
            _diff_in_progress(docs_index_path, old_index_docs, new_index_docs, progress)
        else:
            docs_index_path.write_text(new_index_docs)
        progress()


def _render_diff(path: Path, a: str, b: str):
    diff_lines = difflib.unified_diff(
        a=a.splitlines(keepends=True),
        b=b.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    diff = "".join(diff_lines)
    return diff


def _diff_in_progress(path: Path, a: str, b: str, bar):
    diff = _render_diff(path, a, b)
    if not diff:
        return
    with bar.pause():
        click.echo_via_pager(diff)
