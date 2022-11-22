from functools import lru_cache
from pathlib import Path
from typing import Sequence

import black
from libcst import parse_module
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor

from butcher.codegen.generators.bases import ensure_entity_class
from butcher.codegen.generators.pythonize import pythonize_class_name, pythonize_name
from butcher.codegen.transformers.bot import BotTransformer
from butcher.codegen.transformers.enums import EnumEntityTransformer
from butcher.codegen.transformers.init import InitTransformer
from butcher.codegen.transformers.methods import MethodEntityTransformer
from butcher.codegen.transformers.types import TypeEntityTransformer
from butcher.common_types import AnyDict
from butcher.parsers.entities.generator import EntitiesRegistry
from butcher.shell.config import ProjectConfig


class CodegenManager:
    def __init__(self, config: ProjectConfig, registry: EntitiesRegistry) -> None:
        self.config = config
        self.registry = registry

    @lru_cache
    def _get_black_mode(self):
        return black.FileMode(target_versions={black.TargetVersion.PY37}, line_length=99)

    def _reformat_code(self, code: str) -> str:
        try:
            return black.format_file_contents(
                code,
                fast=True,
                mode=self._get_black_mode(),
            )
        except black.NothingChanged:
            return code
        except black.InvalidInput:
            print(code)
            raise

    def resolve_package_path(self, *parts: str) -> Path:
        return self.config.package_dir.joinpath(*parts)

    def entity_path(self, *parts: str, name: str) -> Path:
        return self.resolve_package_path(*parts, f"{pythonize_name(name)}.py")

    def read_code(self, path: Path) -> str:
        try:
            return path.read_text()
        except FileNotFoundError:
            return ""

    def apply_entity(self, category: str, name: str, code: str) -> str:
        entity = self.registry.registry[category][name]
        return self._apply_entity(entity=entity, code=code)

    def _apply_entity(self, entity: AnyDict, code: str) -> str:
        module = parse_module(code)
        module = ensure_entity_class(
            module=module, name=pythonize_class_name(entity["object"]["name"])
        )
        context = CodemodContext()

        if entity["object"]["category"] == "types":
            transformer = TypeEntityTransformer(entity=entity)
        elif entity["object"]["category"] == "methods":
            transformer = MethodEntityTransformer(entity=entity)
        elif entity["object"]["category"] == "enums":
            transformer = EnumEntityTransformer(context=context, entity=entity)
        else:
            raise NotImplementedError()

        module = module.visit(transformer)
        module = module.visit(AddImportsVisitor(context=context))

        new_code = module.code_for_node(module)
        return self._reformat_code(new_code)

    def process_entity(self, category: str, name: str) -> tuple[Path, str, str]:
        code_path = self.entity_path(category, name=name)
        code = self.read_code(code_path)
        new_code = self.apply_entity(category=category, name=name, code=code)
        return code_path, code, new_code

    def apply_init(self, code: str, names: Sequence[str]) -> str:
        module = parse_module(code)
        context = CodemodContext()
        visitor = InitTransformer(context=context, names=names)
        module = module.visit(visitor)
        module = module.visit(AddImportsVisitor(context=context))

        new_code = module.code_for_node(module)
        return self._reformat_code(new_code)

    def apply_bot(self, code: str) -> str:
        module = parse_module(code)

        context = CodemodContext()

        module = module.visit(
            BotTransformer(context=context, entities=self.registry.registry["methods"])
        )
        module = module.visit(AddImportsVisitor(context=context))

        new_code = module.code_for_node(module)
        return self._reformat_code(new_code)

    def process_bot(self) -> tuple[Path, str, str]:
        code_path = self.resolve_package_path("client", "bot.py")
        code = self.read_code(code_path)
        new_code = self.apply_bot(code)
        return code_path, code, new_code
