from typing import Optional, Union

from libcst import (
    BaseStatement,
    ClassDef,
    FlattenSentinel,
    FunctionDef,
    RemovalSentinel,
    parse_statement,
)
from libcst.codemod import CodemodContext, ContextAwareTransformer

from butcher.codegen.generators.annotation import annotation_as_str, args_as_str, type_as_str
from butcher.codegen.generators.pythonize import pythonize_class_name, pythonize_name
from butcher.codegen.generators.text import first_line
from butcher.common_types import AnyDict


class BotTransformer(ContextAwareTransformer):
    def __init__(self, context: CodemodContext, entities: AnyDict) -> None:
        super().__init__(context=context)

        self.entities = entities
        self.methods = {pythonize_name(name): entity for name, entity in entities.items()}
        self.method_names = set(self.methods.keys())

        self.inside_class = False
        self.known_methods = set()

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        if node.name.value != "Bot":
            return False
        self.inside_class = True
        return True

    def leave_ClassDef(
        self, original_node: "ClassDef", updated_node: "ClassDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:
        if original_node.name.value != "Bot":
            return original_node
        self.inside_class = False

        missing_methods = self.method_names - self.known_methods

        body_extension = []

        for name in sorted(missing_methods):
            body_extension.append(self._render_method(name, self.methods[name]))

        if not body_extension:
            return updated_node
        return updated_node.with_deep_changes(
            updated_node.body,
            body=[
                *updated_node.body.body,
                *body_extension,
            ],
        )

    def leave_FunctionDef(
        self, original_node: "FunctionDef", updated_node: "FunctionDef"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], RemovalSentinel]:
        name = updated_node.name.value
        if not self.inside_class or name.startswith("_"):
            return original_node
        self.known_methods.add(updated_node.name.value)

        method = self.methods.get(name)
        if not method:
            return original_node

        return self._render_method(name, method)

    def _ensure_import(self, item: AnyDict):
        # if item["type"] == "entity":
        #     references = item["references"]
        #     AddImportsVisitor.add_needed_import(
        #         self.context,
        #         f"{references['category']}",
        #         pythonize_class_name(references["name"]),
        #         relative=2,
        #     )
        # elif item["type"] == "union":
        #     for variant in item["items"]:
        #         self._ensure_import(variant)
        # elif item["type"] == "array":
        #     self._ensure_import(item["items"])
        return

    def _render_method(self, name, method: AnyDict):
        args = []
        annotations = []
        call_kwargs = {}

        self._ensure_import(
            {
                "type": "entity",
                "references": {
                    "category": "methods",
                    "name": method["object"]["name"],
                },
            }
        )
        for annotation in method["object"]["annotations"]:
            self._ensure_import(annotation["parsed_type"])
            args.append(annotation_as_str(annotation))
            annotations.append(
                f":param {annotation['name']}: {first_line(annotation['rst_description'])}"
            )
            call_kwargs[annotation["name"]] = annotation["name"]
        annotations.append(":param request_timeout: Request timeout")
        return_description = first_line(
            method["object"]["rst_description"].rsplit(". ", maxsplit=1)[-1]
        )
        annotations.append(f":return: {return_description}")

        self._ensure_import(method["object"]["returning"]["parsed_type"])
        method_args = ", ".join(
            [
                "self",
                *args,
                "request_timeout: Optional[int] = None",
            ]
        )
        description = "\n".join(
            [
                method["object"]["rst_description"].strip(),
                "",
                *annotations,
            ]
        )

        statement = f'''
async def {name}({method_args},) -> {type_as_str(method['object']['returning']['parsed_type'])}:
    """
{description}
    """

    call = {pythonize_class_name(method['object']['name'])}({args_as_str(**call_kwargs)})
    return await self(call, request_timeout=request_timeout)
        '''
        return parse_statement(statement.strip())
