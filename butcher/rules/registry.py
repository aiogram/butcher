from typing import Any, Callable, Iterable

from butcher.configuration.loader import T
from butcher.rules.schema import ActionModel

ResolverType = Callable[[ActionModel, T], Any]


class ActionsRegistry:
    def __init__(self, **actions: ResolverType) -> None:
        self._actions = {**actions}

    def items(self) -> Iterable[tuple[str, ResolverType]]:
        return self._actions.items()

    def _register(self, name: str, resolver: ResolverType):
        self._actions[name] = resolver

    def register(
        self, resolver: ResolverType | None = None, name: str = None
    ) -> ResolverType | Callable[[ResolverType], ResolverType]:
        def decorator(func: ResolverType) -> ResolverType:
            self._register(name or func.__name__, func)
            return func

        if resolver is not None:
            return decorator(resolver)
        return decorator

    def merge(self, *registries: "ActionsRegistry") -> "ActionsRegistry":
        targets = [self, *registries]

        actions = {}
        for target in targets:
            actions |= dict(target.items())

        return type(self)(**actions)

    def apply(self, action: ActionModel, value: T) -> T:
        return self._actions[action.action](action, value)

    def apply_all(self, actions: list[ActionModel], value: T) -> T:
        for action in actions:
            value = self.apply(action, value)
        return value
