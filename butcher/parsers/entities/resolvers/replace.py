from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver


class LocalReplacementResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        replace_config = self.ensure_config(entity, "replace")
        self._resolve_replacement(entity=entity, config=replace_config)

    def _resolve_replacement(self, entity: AnyDict, config: AnyDict):
        if annotations := config.get("annotations"):
            self._resolve_annotations(entity=entity, annotations=annotations)
        if bases := config.get("bases"):
            entity["object"]["bases"] = bases
        if returning := config.get("returning"):
            entity["object"]["returning"] = returning

    def _resolve_annotations(self, entity: AnyDict, annotations: AnyDict):
        for annotation in entity["object"]["annotations"]:
            replacement = annotations.get(annotation["name"])
            if not replacement:
                continue
            annotation.update(replacement)
