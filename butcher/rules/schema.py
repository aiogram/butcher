from typing import Any

import rule_engine
from pydantic import BaseModel
from rule_engine import Rule, RuleSyntaxError


class ActionModel(BaseModel):
    action: str
    args: dict[str, Any] | None = None


class RuleType(Rule):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> "RuleType":
        context = rule_engine.Context(resolver=rule_engine.resolve_attribute)
        try:
            return cls(v, context=context)
        except RuleSyntaxError as e:
            raise ValueError(e.message)


class TermModel(BaseModel):
    name: str | None = None
    rule: RuleType
    do: list[ActionModel]


class TermsConfig(BaseModel):
    methods: list[TermModel]
    types: list[TermModel]
