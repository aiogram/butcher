from itertools import chain
from textwrap import indent
from typing import Optional, Union

import libcst.matchers as m
from libcst import (
    Arg,
    BaseSmallStatement,
    BaseStatement,
    ClassDef,
    CSTTransformer,
    EmptyLine,
    FlattenSentinel,
    FunctionDef,
    Newline,
    Pass,
    RemovalSentinel,
    SimpleStatementLine,
    SimpleWhitespace,
    parse_statement,
)

from butcher.codegen.generators.annotation import annotation_as_str, type_as_str
from butcher.codegen.generators.pythonize import pythonize_class_name
from butcher.codegen.generators.text import first_line
from butcher.common_types import AnyDict


class MethodEntityTransformer(CSTTransformer):
    def __init__(self, entity: AnyDict) -> None:
        super().__init__()

        self.entity = entity
        self.inside_class = False
        self.found_methods = []

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        if node.name.value == pythonize_class_name(self.entity["object"]["name"]):
            self.inside_class = True
            return True
        return False

    def _render_annotation(
        self, annotation: AnyDict, leading_whitespace: bool = False
    ) -> list[SimpleStatementLine]:
        attribute = annotation_as_str(annotation=annotation, as_field=True)
        lines = [
            parse_statement(f"{attribute}"),
            parse_statement(f'"""{first_line(annotation["rst_description"])}"""'),
        ]
        if leading_whitespace:
            lines[0] = lines[0].with_changes(
                leading_lines=[
                    EmptyLine(
                        whitespace=SimpleWhitespace(
                            value="",
                        ),
                        newline=Newline(
                            value=None,
                        ),
                    )
                ],
            )

        return lines

    def _render_docstring(self):
        description = self.entity["object"]["rst_description"]
        anchor = self.entity["object"]["anchor"]
        return parse_statement(
            indent(
                f'"""\n{description}\n\nSource: https://core.telegram.org/bots/api#{anchor}\n"""',
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
        for node_index, node in enumerate(updated_node.body.body):
            # TODO: Add possibility to keep custom attributes
            if m.matches(node, m.FunctionDef()):
                break
        else:
            node_index += 1

        returning_type = type_as_str(self.entity["object"]["returning"]["parsed_type"])
        bases = [
            Arg(value=parse_statement(f"{base}[{returning_type}]"))
            for base in self.entity["object"]["bases"]
        ]
        extensions = []
        if "build_request" not in self.found_methods:
            extensions.append(
                parse_statement(
                    f"""
def build_request(self, bot: Bot) -> Request:
    data: Dict[str, Any] = self.dict()

    return Request(method="{self.entity['object']['name']}", data=data)
"""
                )
            )
        return updated_node.with_changes(bases=bases).with_deep_changes(
            updated_node.body,
            body=[
                self._render_docstring(),
                parse_statement(f"__returning__ = {returning_type}"),
                *chain.from_iterable(
                    self._render_annotation(annotation, leading_whitespace=index == 0)
                    for index, annotation in enumerate(self.entity["object"]["annotations"])
                ),
                *updated_node.body.body[node_index:],
                *extensions,
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
