from typing import Any

from pydantic import BaseModel

from butcher.parsers.dev_entities.type_parser import ObjectTypeUnion
from butcher.rules.registry import ActionsRegistry
from butcher.rules.schema import ActionModel

annotations_registry = ActionsRegistry()


class ParsedTypeWrapper(BaseModel):
    type: ObjectTypeUnion


@annotations_registry.register(name="update_type")
def apply_update_type(action: ActionModel, value: Any) -> Any:
    return value.copy(update={"parsed_type": ParsedTypeWrapper(type=action.args).type})
