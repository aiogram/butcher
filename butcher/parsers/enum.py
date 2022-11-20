import re

from butcher.common_types import AnyDict, RegistryType


def resolve_enum(registry: RegistryType, enum_config: AnyDict):
    enum_type = enum_config.get("type", "str")
    bases = [enum_type, "Enum"]

    values = {}

    if enum_static := enum_config.get("static"):
        values.update(enum_static)
    if enum_parse := enum_config.get("parse"):
        source_entity = registry["types"][enum_parse["entity"]]
        source_annotation = next(
            filter(
                lambda item: item["name"] == enum_parse["attribute"],
                source_entity["object"]["annotations"],
            )
        )
        source = source_annotation["description"]

        values.update(extract_enum_values_from_string(value=source, pattern=enum_parse["regexp"]))
    if enum_extract := enum_config.get("extract"):
        exclude = set(enum_extract.get("exclude", []))
        source_entity = registry["types"][enum_extract["entity"]]
        values.update(
            {
                annotation["name"].upper(): annotation["name"]
                for annotation in source_entity["object"]["annotations"]
                if annotation["name"] not in exclude
            }
        )

    result = {
        "meta": {},
        "object": {
            "name": enum_config["name"],
            "type": enum_type,
            "bases": bases,
            "description": enum_config["description"],
            "html_description": enum_config["description"],
            "rst_description": enum_config["description"].strip(),
            "values": values,
            "category": "enums",
        },
    }
    return result


def extract_enum_values_from_string(value: str, pattern: str) -> dict[str, str]:
    result = {}
    for item in re.findall(pattern, value):
        result[item.upper()] = item
    return result
