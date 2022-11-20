from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from butcher.codegen.generators.annotation import type_as_str
from butcher.codegen.generators.pythonize import pythonize_class_name, pythonize_name
from butcher.common_types import AnyDict
from butcher.parsers.entities.generator import EntitiesRegistry
from butcher.shell.config import ProjectConfig


class DocsManager:
    def __init__(self, config: ProjectConfig, registry: EntitiesRegistry) -> None:
        self.config = config
        self.registry = registry

        self.env = Environment(
            loader=FileSystemLoader(
                searchpath=config.project_dir / "templates",
            ),
        )
        self.env.filters.update(
            {
                "header": lambda value, symbol: symbol * len(value),
                "pythonize_name": pythonize_name,
                "pythonize_class_name": pythonize_class_name,
                "type": type_as_str,
            }
        )

    def resolve_package_path(self, *parts: str) -> Path:
        return self.config.docs_dir.joinpath(*parts)

    def entity_path(self, *parts: str, name: str) -> Path:
        return self.resolve_package_path(*parts, f"{pythonize_name(name)}.rst")

    def read_code(self, path: Path) -> str:
        try:
            return path.read_text()
        except FileNotFoundError:
            return ""

    def apply_entity(self, category: str, name: str, docs: str) -> str:
        entity = self.registry.registry[category][name]
        return self._apply_entity(entity=entity, docs=docs)

    def _apply_entity(self, entity: AnyDict, docs: str) -> str:
        if entity["object"]["category"] == "types":
            template = self.env.get_template("types/entity.rst.jinja2")
        elif entity["object"]["category"] == "methods":
            template = self.env.get_template("methods/entity.rst.jinja2")
        elif entity["object"]["category"] == "enums":
            template = self.env.get_template("enums/entity.rst.jinja2")
        else:
            raise NotImplementedError()

        return template.render(**entity).rstrip() + "\n"

    def process_entity(self, category: str, name: str) -> tuple[Path, str, str]:
        docs_path = self.entity_path("api", category, name=name)
        docs = self.read_code(docs_path)
        new_docs = self.apply_entity(category=category, name=name, docs=docs)
        return docs_path, docs, new_docs

    def _collect_index(self, category: str):
        index = defaultdict(list)
        for name, entity in self.registry.registry[category].items():
            title = entity.get("group", {}).get("title", None)
            index[title].append(name)
        for group in index.values():
            group.sort()
        return index

    def apply_index(self, category: str, index: str) -> str:
        groups = self._collect_index(category=category)
        template = self.env.get_template(f"{category}/index.rst.jinja2")
        return template.render(groups=groups)

    def process_index(self, category: str) -> tuple[Path, str, str]:
        index_path = self.entity_path("api", category, name="index")
        index = self.read_code(index_path)
        new_index = self.apply_index(category=category, index=index)
        return index_path, index, new_index
