from libcst import Module, Name
from libcst.helpers import parse_template_module

from butcher.codegen.visitors.simple_entity import EntityVisitor

BASE_ENTITY_TEMPLATE = """
class {class_name}:
    pass

""".lstrip()


def ensure_entity_class(module: Module, name: str) -> Module:
    visitor = EntityVisitor()
    module.visit(visitor)
    entity_class = visitor.entities.get(name)
    if entity_class:
        return module

    class_template = parse_template_module(BASE_ENTITY_TEMPLATE, class_name=Name(name))
    if not module.body:
        return class_template
    module = module.with_changes(
        body=[
            *module.body,
            class_template,
        ],
    )
    return module
