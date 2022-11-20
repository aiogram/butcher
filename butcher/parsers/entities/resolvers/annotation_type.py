from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.entity_type import ENTITY_CATEGORY, detect_entity_type_by_name
from butcher.parsers.entities.resolvers.base import EntityResolver

BUILTIN_TYPES = {
    "String": "str",
    "Integer": "int",
    "Float": "float",
    "Boolean": "bool",
}


class AnnotationTypeResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        for annotation in entity["object"]["annotations"]:
            annotation["parsed_type"] = parse_type(annotation["type"])
        entity["object"]["annotations"].sort(key=lambda item: not item["required"])


def parse_type(value: str) -> AnyDict:
    if not value:
        return {"type": "std", "name": "Any"}

    lower = value.lower()
    split = lower.split()

    if split[0] == "array":
        new_string = value[lower.index("of") + 2 :].strip()
        return {"type": "array", "items": parse_type(new_string)}
    if "messages" in split:
        return parse_type(value.replace("Messages", "array of Message"))
    if "or" in split:
        split_types = value.split(" or ")
        return {
            "type": "union",
            "items": [parse_type(item.strip()) for item in split_types],
        }
    if "and" in split:
        split_types = value.split(" and ")
        return {
            "type": "union",
            "items": [parse_type(item.strip()) for item in split_types],
        }
    if "number" in lower:
        return parse_type(value.replace("number", "").strip())
    if lower in ["true", "false"]:
        return {"type": "std", "name": "bool", "value": lower == "true"}
    if value not in BUILTIN_TYPES and value[0].isupper():
        return {
            "type": "entity",
            "references": {
                "category": ENTITY_CATEGORY[detect_entity_type_by_name(value)],
                "name": str(value),
            },
        }
    elif value in BUILTIN_TYPES:
        return {"type": "std", "name": BUILTIN_TYPES[value]}

    raise ValueError(f"Type {value} can't be parsed")
