from butcher.codegen.generators.pythonize import pythonize_class_name, pythonize_name
from butcher.common_types import AnyDict


def render_reference(entity: AnyDict) -> str:
    obj = entity["obj"]
    return render_entity_reference(
        category=obj["category"],
        name=entity["name"],
        label=entity["name"],
    )


def render_entity_reference(category: str, name: str, label: str | None = None) -> str:
    return _render_reference(
        "class",
        "aiogram",
        category,
        pythonize_name(name),
        pythonize_class_name(name),
        label=label,
    )


def _render_reference(ref: str, *parts: str, label: str | None = None) -> str:
    value = ".".join(parts)
    if label:
        value = f"{label} <{value}>"
    return f":{ref}:`{value}`"
