import re

from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.annotation_type import parse_type
from butcher.parsers.entities.resolvers.base import EntityResolver

RE_FLAGS = re.IGNORECASE
RETURN_PATTERNS = [
    re.compile(item, flags=RE_FLAGS)
    for item in [
        r"(?P<type>[a-z]+) is returned, otherwise (?P<other>[a-zA-Z]+) is returned",
        r"returns the edited (?P<type>[a-z]+), otherwise returns (?P<other>[a-zA-Z]+)",
        r"On success, the stopped (?P<type>[a-z]+) with the final results is returned",
        r"On success, an (?P<type>array of [a-z]+)s that were sent is returned",
        r"Returns the (?P<type>[a-z]+) of the sent message on success",
        r"(?P<type>Array of [a-z]+) objects",
        r"Returns (?P<type>Array of [a-z]+) on success",
        r"a (?P<type>[a-z]+) object",
        r"Returns (?P<type>[a-z]+) on success",
        r"(?P<type>[a-z]+) on success",
        r"(?P<type>[a-z]+) is returned",
        r"Returns the [a-z ]+ as (?P<type>[a-z]+) object",
        r"Returns (?P<type>[a-z]+)",
    ]
]


class ReturningTypeResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        type_, description = parse_returning(entity["object"]["description"])
        entity["object"]["returning"] = {
            "type": type_,
            "parsed_type": parse_type(type_),
            "description": description,
        }


def parse_returning(description: str):
    parts = list(filter(lambda item: "return" in item.lower(), description.split(".")))
    if not parts:
        raise RuntimeError(f"Failed to parse returning type for {description!r}")
    sentence = ". ".join(map(str.strip, parts))
    return_type = None

    for pattern in RETURN_PATTERNS:
        temp = pattern.search(sentence)
        if temp:
            return_type = temp.group("type")
            if "other" in temp.groupdict():
                otherwise = temp.group("other")
                return_type += f" or {otherwise}"
        if return_type:
            break
    if not return_type:
        raise RuntimeError(f"Failed to parse return type from {sentence!r}")

    if return_type == "Int":
        return_type = "Integer"
    return return_type, sentence + "."
