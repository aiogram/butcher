from textwrap import indent
from typing import Optional, Union

import libcst.matchers as m
from libcst import (
    Arg,
    Assign,
    BaseSmallStatement,
    BaseStatement,
    ClassDef,
    CSTTransformer,
    FlattenSentinel,
    FunctionDef,
    Name,
    Pass,
    RemovalSentinel,
    SimpleStatementLine,
    parse_statement,
)

from butcher.codegen.generators.pythonize import pythonize_class_name
from butcher.common_types import AnyDict


class EnumEntityTransformer(CSTTransformer):
    def __init__(self, entity: AnyDict) -> None:
        super().__init__()

        self.entity = entity
        self.inside_class = False
        self.found_methods = []
        self.found_names = []

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        if node.name.value == pythonize_class_name(self.entity["object"]["name"]):
            self.inside_class = True
            return True
        return False

    def _render_value(self, name: str, value: str) -> SimpleStatementLine:
        if self.entity["object"]["type"] == "str":
            value = f'"{value}"'
        return parse_statement(f"{name} = {value}")

    def _render_docstring(self):
        description = self.entity["object"]["rst_description"]
        return parse_statement(
            indent(
                f'"""\n{description}\n"""',
                prefix="    ",
            ).lstrip()
        )

    def leave_ClassDef(
        self, original_node: "ClassDef", updated_node: "ClassDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:
        if updated_node.name.value != pythonize_class_name(self.entity["object"]["name"]):
            return updated_node
        self.inside_class = False

        node_index = 0

        body = []

        for node_index, node in enumerate(updated_node.body.body):
            if node_index == 0 and m.matches(
                node, m.SimpleStatementLine(body=[m.Expr(value=m.SimpleString())])
            ):
                continue
            if m.matches(
                node,
                m.SimpleStatementLine(
                    body=[
                        m.Assign(
                            targets=[
                                m.AssignTarget(
                                    target=m.Name(
                                        value=m.MatchIfTrue(
                                            lambda value: value in self.entity["object"]["values"]
                                        )
                                    )
                                )
                            ]
                        )
                    ]
                ),
            ):
                continue
            body.append(node)
            if m.matches(node, m.FunctionDef()):
                break
        else:
            node_index += 1

        bases = [Arg(value=Name(value=base)) for base in self.entity["object"]["bases"]]

        return updated_node.with_changes(bases=bases).with_deep_changes(
            updated_node.body,
            body=[
                self._render_docstring(),
                *(
                    self._render_value(name, value)
                    for name, value in self.entity["object"]["values"].items()
                    if name not in self.found_names
                ),
                *body,
                *updated_node.body.body[node_index:],
            ],
        )

    def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
        if not self.inside_class:
            return False

        self.found_methods.append(node.name.value)

        return False

    def visit_Pass(self, node: "Pass") -> Optional[bool]:
        return True

    def leave_Pass(
        self, original_node: "Pass", updated_node: "Pass"
    ) -> Union["BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel]:
        return RemovalSentinel.REMOVE

    def visit_Assign(self, node: "Assign") -> Optional[bool]:
        if not self.inside_class:
            return False

        return False

    def leave_Assign(
        self, original_node: "Assign", updated_node: "Assign"
    ) -> Union["BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel]:
        if not self.inside_class:
            return original_node
        name = updated_node.targets[0].target.value
        if not name.isupper():
            return original_node

        if (values := self.entity["object"]["values"]) and values.get(name, None):
            return RemovalSentinel.REMOVE

        self.found_names.append(name)
        return original_node
