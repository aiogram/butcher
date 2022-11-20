from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver


class CanBeUsedInWebhookResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        entity["can_be_used_in_webhook"] = self._detect(entity["object"])

    def _detect(self, obj: AnyDict) -> bool:
        if obj["name"].startswith("get"):
            return False
        for annotation in obj["annotations"]:
            if (
                annotation["parsed_type"]["type"] == "entity"
                and annotation["parsed_type"]["references"]["name"] == "InputFile"
                and annotation["required"] is True
            ):
                return False
        return True
