from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver


class BaseClassResolver(EntityResolver):
    def __init__(self, *bases: str):
        self.bases = bases

    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        entity["object"]["bases"] = list(self.bases)
