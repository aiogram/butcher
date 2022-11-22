from typing import Any, TypeAlias

AnyDict: TypeAlias = dict[str, Any]
CategoryType: TypeAlias = str
RegistryType: TypeAlias = dict[CategoryType, dict[str, AnyDict]]
