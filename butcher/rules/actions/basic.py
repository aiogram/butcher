from typing import Any

from butcher.rules.registry import ActionsRegistry
from butcher.rules.schema import ActionModel

basic_registry = ActionsRegistry()


@basic_registry.register(name="update")
def apply_update(action: ActionModel, value: Any) -> Any:
    return value.copy(update=action.args, deep=True)
