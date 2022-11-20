from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver


class AliasesConfig(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        aliases_config = self.ensure_config(entity, "aliases")

        aliases = entity["aliases"] = {}
        for name, alias in aliases_config.items():
            aliases[name] = self._resolve_alias(
                registry=registry, entity=entity, name=name, alias=alias
            )

    def _resolve_alias(self, registry: RegistryType, entity: AnyDict, name: str, alias: AnyDict):
        referenced_method = registry["methods"][alias["method"]]
        fill = alias["fill"]
        result = {
            "method": alias["method"],
            "anchor": referenced_method["object"]["anchor"],
            "fill": alias["fill"],
            "description": referenced_method["object"]["description"],
            "html_description": referenced_method["object"]["html_description"],
            "rst_description": referenced_method["object"]["rst_description"],
            "annotations": [
                item
                for item in referenced_method["object"]["annotations"]
                if item["name"] not in fill
            ],
            "returning": referenced_method["object"]["returning"],
        }
        method_aliased = referenced_method.setdefault("aliased", [])
        method_aliased.append(
            {
                "type": entity["object"]["name"],
                "name": name,
            }
        )
        return result
