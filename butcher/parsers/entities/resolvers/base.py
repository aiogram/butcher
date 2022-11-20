from abc import ABC, abstractmethod

from butcher.common_types import AnyDict, RegistryType


class EntityResolver(ABC):
    @abstractmethod
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        pass

    def ensure_config(self, entity: AnyDict, name: str) -> AnyDict:
        configs = entity.get("configs")
        if not configs:
            raise RejectResolver("entity has no configs")
        config = configs.get(name)
        if not config:
            raise RejectResolver(f"entity has no config named {name!r}")
        return config

    def optional_ensure_config(self, entity: AnyDict, name: str) -> AnyDict | None:
        try:
            self.ensure_config(entity=entity, name=name)
        except RejectResolver:
            return None


class RejectResolver(Exception):
    pass
