import difflib
import typing as t
from pathlib import Path

import click
from alive_progress import alive_bar
from click import Context, Parameter, pass_context

from butcher.codegen.manager import CodegenManager
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
    manager = CodegenManager(config=config, registry=registry)
    with alive_bar(
        len(names),
        dual_line=True,
        title=f"Rendering {category}...",
    ) as progress:
        for name in names:
            progress.text = f"Rendering {name}"
            code_path = manager.entity_path(category, name=name)
            code = manager.read_code(code_path)
            new_code = manager.apply_entity(category=category, name=name, code=code)

            if diff:
                _show_diff(code_path, code, new_code)
            else:
                code_path.write_text(new_code)
            progress()

    init_path = manager.resolve_package_path(category, "__init__.py")
    init = manager.read_code(init_path)
    new_init = manager.apply_init(init, names=names)
    if diff:
        _show_diff(init_path, init, new_init)
    else:
        init_path.write_text(new_init)


def _show_diff(path: Path, a: str, b: str):
    diff_lines = difflib.unified_diff(
        a=a.splitlines(keepends=True),
        b=b.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    diff = "".join(diff_lines)
    click.echo_via_pager(diff)
