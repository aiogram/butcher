from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver

RESERVED = {
    "from": "from_user",
}


class ReservedNameResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        for annotation in entity["object"]["annotations"]:
            replacement = RESERVED.get(annotation["name"])
            if not replacement:
                continue

            annotation["alias"] = annotation["name"]
            annotation["name"] = replacement
