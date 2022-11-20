from enum import Enum, auto

from butcher.common_types import AnyDict


class EntityType(Enum):
    type = auto()
    method = auto()


ENTITY_CATEGORY = {
    EntityType.type: "types",
    EntityType.method: "methods",
}


def detect_entity_type(entity: AnyDict) -> EntityType:
    return detect_entity_type_by_name(entity["name"])


def detect_entity_type_by_name(name: str) -> EntityType:
    if name[0].isupper():
        return EntityType.type
    return EntityType.method
