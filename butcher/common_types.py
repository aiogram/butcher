from typing import Any, Literal, TypeAlias

AnyDict: TypeAlias = dict[str, Any]
CategoryType: TypeAlias = Literal["types", "methods", "enums"]
RegistryType: TypeAlias = dict[CategoryType, dict[str, AnyDict]]
