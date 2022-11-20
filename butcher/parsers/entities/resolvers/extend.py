from butcher.common_types import AnyDict, RegistryType
from butcher.parsers.entities.resolvers.base import EntityResolver


class ExtendResolver(EntityResolver):
    def resolve(self, registry: RegistryType, entity: AnyDict) -> None:
        config = self.ensure_config(entity, "extend")

        define = config.get("define", [])
        clone = config.get("clone", [])

        annotations = entity["object"]["annotations"]
        names = {annotation["name"] for annotation in annotations}
        for item in define:
            if item["name"] in names:
                continue
            annotations.append(item)
            names.add(item["name"])

        for item in clone:
            entity_name = item
            if isinstance(item, dict):
                entity_name = list(item.keys())[0]
                entity_config = item[entity_name]
                exclude_names = entity_config.get("exclude", [])
            else:
                entity_name = item
                entity_config = {}
                exclude_names = []

            entity = registry["types"][entity_name]
            for annotation in entity["object"]["annotations"]:
                if annotation["name"] in names or annotation["name"] in exclude_names:
                    continue
                cloned = annotation.copy()
                cloned["required"] = False
                if not cloned["rst_description"].startswith("*Optional*"):
                    cloned["rst_description"] = f"*Optional*. {cloned['rst_description']}"
                annotations.append(cloned)
                names.add(annotation["name"])
