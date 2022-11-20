import re

from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver

CONST_PATTERNS = [
    re.compile(r", must be (\w+)$"),
    re.compile(r", always '(\w+)'"),
]


class ConstResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        # entity_name = entity["object"]["name"]
        for annotation in entity["object"]["annotations"]:
            description = annotation["description"]
            # name = annotation["name"]
            for pattern in CONST_PATTERNS:
                if result := pattern.search(description):
                    # print(f"{entity_name:>40}  .{name:<15} - {result.group(1):25} - {description}")
                    annotation["const"] = f'"{result.group(1)}"'
