import re

from butcher.common_types import AnyDict, RegistryType


def resolve_enum(registry: RegistryType, enum_config: AnyDict):
    enum_name = enum_config["name"]
    enum_type = enum_config.get("type", "str")
    bases = [enum_type, "Enum"]

    values = {}

    if enum_static := enum_config.get("static"):
        values.update(enum_static)

    if enum_parse := enum_config.get("parse"):
        source_entity = registry[enum_parse.get("category", "types")][enum_parse["entity"]]
        source_annotation = next(
            filter(
                lambda item: item["name"] == enum_parse["attribute"],
                source_entity["object"]["annotations"],
            )
        )
        description_format = enum_parse.get("format", "")
        if description_format:
            description_format += "_"
        source = source_annotation[f"{description_format}description"]
        pattern = enum_parse["regexp"]
        for item in re.findall(pattern, source):
            values[item.upper()] = item
            update_const(source_annotation, enum_name, item)

    if enum_multi_parse := enum_config.get("multi_parse"):
        category = enum_multi_parse.get("category", "types")
        annotation_name = enum_multi_parse["attribute"]
        entities = enum_multi_parse["entities"]
        pattern = enum_multi_parse["regexp"]
        description_format = enum_multi_parse.get("format", "")
        if description_format:
            description_format += "_"
        for entity_name in entities:
            source_entity = registry[category][entity_name]
            source_annotation = extract_annotation(source_entity, annotation_name)
            if item := re.search(pattern, source_annotation[f"{description_format}description"]):
                value = item.group(1)
                values[value.upper()] = value

                update_const(source_annotation, enum_name, value)

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
            "docs": enum_config.get("docs"),
            "values": values,
            "category": "enums",
        },
    }
    return result


def extract_annotation(entity: AnyDict, name: str) -> AnyDict:
    annotation = next(
        filter(
            lambda item: item["name"] == name,
            entity["object"]["annotations"],
        )
    )
    return annotation


def update_const(annotation: AnyDict, enum: str, value: str) -> None:
    annotation["enum_value"] = f"{enum}.{value.upper()}"
