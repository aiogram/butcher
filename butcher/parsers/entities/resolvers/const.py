import re

from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver

CONST_PATTERNS = [
    re.compile(r", must be (\w+)$"),
    re.compile(r", always '(\w+)'"),
]


class ConstResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        for annotation in entity["object"]["annotations"]:
            description = annotation["description"]
            is_const = False
            for pattern in CONST_PATTERNS:
                if result := pattern.search(description):
                    annotation["const"] = f'"{result.group(1)}"'
                    is_const = True
                    break
            if is_const and (enum_value := annotation.get("enum_value")):
                annotation["const"] = enum_value
