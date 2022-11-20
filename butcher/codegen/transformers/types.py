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
    FlattenSentinel,
    FunctionDef,
    Name,
    Pass,
    RemovalSentinel,
    SimpleStatementLine,
    parse_statement,
)

from butcher.codegen.generators.annotation import annotation_as_str
from butcher.codegen.generators.pythonize import pythonize_class_name
from butcher.codegen.generators.reference import render_entity_reference
from butcher.codegen.generators.text import first_line
from butcher.common_types import AnyDict


class TypeEntityTransformer(CSTTransformer):
    def __init__(self, entity: AnyDict) -> None:
        super().__init__()

        self.entity = entity
        self.inside_class = False
        self.found_methods = []

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        if node.name.value == self.entity["object"]["name"]:
            self.inside_class = True
            return True
        return False

    def _render_annotation(self, annotation: AnyDict) -> list[SimpleStatementLine]:
        attribute = annotation_as_str(annotation=annotation, as_field=True)

        return [
            parse_statement(f"{attribute}"),
            parse_statement(f'"""{first_line(annotation["rst_description"])}"""'),
        ]

    def _render_docstring(self):
        description = self.entity["object"]["rst_description"]
        anchor = self.entity["object"]["anchor"]
        return parse_statement(
            indent(
                f'"""\n{description}\n\nSource: https://core.telegram.org/bots/api#{anchor}\n"""',
                prefix="    ",
            ).lstrip()
        )

    def _render_alias(self, name: str, alias: AnyDict):
        args = ", ".join(
            ["self"]
            + [annotation_as_str(annotation) for annotation in alias["annotations"]]
            + ["**kwargs: Any"]
        )
        method_class_name = pythonize_class_name(alias["method"])
        header_statement = f"def {name}({args},) -> {method_class_name}:"
        import_statement = f"from aiogram.methods import {method_class_name}"

        params_description = [
            f":param {annotation['name']}: {first_line(annotation['rst_description'])}"
            for annotation in alias["annotations"]
        ]
        ref = render_entity_reference("methods", alias["method"])
        params_description.append(f":return: instance of method {ref}")
        fill_names = "\n- ".join(f":code:`{name}`" for name in alias["fill"].keys())
        description_lines = [
            f"Shortcut for method {ref}\n"
            f"will automatically fill method attributes:\n\n- {fill_names}",
            alias["rst_description"],
            f"Source: https://core.telegram.org/bots/api#{alias['anchor']}",
            "\n".join(params_description),
        ]
        description = (
            '"""\n' + indent("\n\n".join(description_lines), prefix=" " * 8) + '\n        """'
        )

        alias_kwargs = {
            **alias["fill"],
            **{annotation["name"]: annotation["name"] for annotation in alias["annotations"]},
        }
        alias_kwargs_str = ", ".join([f"{k}={v}" for k, v in alias_kwargs.items()] + ["**kwargs"])
        alias_statement = f"{method_class_name}({alias_kwargs_str},)"
        return parse_statement(
            f"\n{header_statement}\n"
            f"    {description}\n"
            f"    # DO NOT EDIT MANUALLY!!!\n"
            f"    # This method was auto-generated via `butcher`\n\n"
            f"    {import_statement}\n"
            "\n"
            f"    return {alias_statement}\n"
        )

    def leave_ClassDef(
        self, original_node: "ClassDef", updated_node: "ClassDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:
        if updated_node.name.value != self.entity["object"]["name"]:
            return updated_node
        self.inside_class = False

        node_index = 0
        for node_index, node in enumerate(updated_node.body.body):
            # TODO: Add possibility to keep custom attributes
            if m.matches(node, m.FunctionDef()):
                break
        else:
            node_index += 1

        missing_aliases = []
        for name, alias in self.entity.get("aliases", {}).items():
            if name not in self.found_methods:
                missing_aliases.append(self._render_alias(name=name, alias=alias))

        bases = [Arg(value=Name(value=base)) for base in self.entity["object"]["bases"]]
        return updated_node.with_changes(bases=bases).with_deep_changes(
            updated_node.body,
            body=[
                self._render_docstring(),
                *chain.from_iterable(
                    self._render_annotation(annotation)
                    for annotation in self.entity["object"]["annotations"]
                ),
                *updated_node.body.body[node_index:],
                *missing_aliases,
            ],
        )

    def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
        if not self.inside_class:
            return False

        self.found_methods.append(node.name.value)

        return False

    def leave_FunctionDef(
        self, original_node: "FunctionDef", updated_node: "FunctionDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:

        if updated_node.name.value not in self.entity.get("aliases", {}):
            return updated_node

        return self._render_alias(
            updated_node.name.value, alias=self.entity["aliases"][updated_node.name.value]
        )

    def visit_Pass(self, node: "Pass") -> Optional[bool]:
        return True

    def leave_Pass(
        self, original_node: "Pass", updated_node: "Pass"
    ) -> Union["BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel]:
        return RemovalSentinel.REMOVE
