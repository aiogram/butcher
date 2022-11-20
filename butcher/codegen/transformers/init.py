from typing import Optional, Sequence, Union

from libcst import Assign, BaseSmallStatement, FlattenSentinel, ImportFrom, RemovalSentinel
from libcst import matchers as m
from libcst import parse_statement
from libcst.codemod import CodemodContext, ContextAwareTransformer
from libcst.codemod.visitors import AddImportsVisitor

from butcher.codegen.generators.pythonize import pythonize_class_name, pythonize_name


class InitTransformer(ContextAwareTransformer):
    def __init__(self, context: CodemodContext, names: Sequence[str]) -> None:
        super().__init__(context=context)
        self.names = names

        self.imported_entities = set()

    def visit_ImportFrom(self, node: "ImportFrom") -> Optional[bool]:
        # self.imported_entities.add()
        self.imported_entities.update(alias.name.value for alias in node.names)
        return False

    def leave_Assign(
        self, original_node: "Assign", updated_node: "Assign"
    ) -> Union["BaseSmallStatement", FlattenSentinel["BaseSmallStatement"], RemovalSentinel]:
        if not m.matches(
            original_node,
            m.Assign(targets=[m.AssignTarget(target=m.Name(value="__all__"))], value=m.Tuple()),
        ):
            return original_node

        all_names = {element.value.value for element in original_node.value.elements}
        new_names = {f'"{pythonize_class_name(item)}"' for item in self.names}
        missing_names = new_names - all_names
        if not missing_names:
            return original_node
        for quoted_name in missing_names:
            name = quoted_name.strip('"')
            AddImportsVisitor.add_needed_import(
                self.context, pythonize_name(name), pythonize_class_name(name), relative=1
            )
        names = ",\n    ".join(sorted(all_names | missing_names)) + ","
        result = parse_statement(f"__all__ = (\n    {names}\n)").body[0]
        return updated_node.with_changes(value=result.value)
