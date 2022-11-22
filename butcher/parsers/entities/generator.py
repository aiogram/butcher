import logging
from pathlib import Path

from butcher.common_types import RegistryType
from butcher.data import load_json, load_yaml
from butcher.parsers.entities.resolvers.aliases import AliasesConfig
from butcher.parsers.entities.resolvers.annotation_type import AnnotationTypeResolver
from butcher.parsers.entities.resolvers.base import RejectResolver
from butcher.parsers.entities.resolvers.base_class import BaseClassResolver
from butcher.parsers.entities.resolvers.can_be_used_in_webhook import CanBeUsedInWebhookResolver
from butcher.parsers.entities.resolvers.const import ConstResolver
from butcher.parsers.entities.resolvers.extend import ExtendResolver
from butcher.parsers.entities.resolvers.replace import LocalReplacementResolver
from butcher.parsers.entities.resolvers.reserved_names import ReservedNameResolver
from butcher.parsers.entities.resolvers.returning_type import ReturningTypeResolver
from butcher.parsers.enum import resolve_enum

logger = logging.getLogger(__name__)


class EntitiesRegistry:
    def __init__(
        self,
        project_dir: Path,
    ) -> None:
        self.project_dir = project_dir
        self.registry: RegistryType = {
            "methods": {},
            "types": {},
            "enums": {},
        }

        annotation_type_resolver = AnnotationTypeResolver()
        local_replacement_resolver = LocalReplacementResolver()
        self.resolvers = {
            "methods": [
                annotation_type_resolver,
                ReturningTypeResolver(),
                BaseClassResolver("TelegramMethod"),
                CanBeUsedInWebhookResolver(),
                local_replacement_resolver,
            ],
            "types": [
                ExtendResolver(),
                annotation_type_resolver,
                ReservedNameResolver(),
                BaseClassResolver("TelegramObject"),
                ConstResolver(),
                local_replacement_resolver,
                AliasesConfig(),
            ],
            "enums": [
                # BaseClassResolver("str", "Enum"),
            ],
        }

    def scan(self) -> None:
        for category in [
            "methods",
            "types",
        ]:
            category_mapping = self.registry.setdefault(category, {})
            category_dir = self.project_dir / category
            logger.debug("Scan category %r in %s", category, category_dir)
            for entity_path in category_dir.glob("**/entity.json"):
                entity_dir = entity_path.parent
                entity_name = entity_dir.name.removesuffix(entity_dir.suffix)
                logger.debug("Load entity %r from %s", entity_name, entity_path)
                entity = load_json(path=entity_path)
                category_mapping[entity_name] = entity
                entity_configs = entity["configs"] = {}

                for config_path in entity_dir.glob("*.yml"):
                    config_name = config_path.name.removesuffix(config_path.suffix)
                    entity_configs[config_name] = load_yaml(config_path)

    def resolve(self):
        for category, entities in self.registry.items():
            logger.debug("Resolve category %s", category)
            for entity in entities.values():
                logger.debug("Resolve entity %s.%s", category, entity["object"]["name"])
                resolvers = self.resolvers.get(category)
                if not resolvers:
                    continue

                for resolver in resolvers:
                    try:
                        resolver.resolve(registry=self.registry, entity=entity)
                    except RejectResolver:
                        continue

    def resolve_enums(self):
        logger.debug("Resolve enums")
        enums_dir = self.project_dir / "enums"
        for enum_config_path in enums_dir.glob("*.yml"):
            enum_config = load_yaml(enum_config_path)
            self.registry["enums"][enum_config["name"]] = resolve_enum(
                registry=self.registry,
                enum_config=enum_config,
            )

    def initialize(self):
        self.scan()
        self.resolve_enums()
        self.resolve()
