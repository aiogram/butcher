from typing import Any

from butcher.rules.actions.annotations import annotations_registry
from butcher.rules.actions.basic import basic_registry
from butcher.rules.registry import ActionsRegistry
from butcher.rules.schema import TermModel

all_registry = ActionsRegistry().merge(
    basic_registry,
    annotations_registry,
)


def apply_term(term: TermModel, value: Any) -> Any:
    if not term.rule.matches(value):
        return value

    value = all_registry.apply_all(actions=term.do, value=value)
    return value


def apply_terms(terms: list[TermModel], value: Any) -> Any:
    for term in terms:
        value = apply_term(term, value)
    return value
