from butcher.common_types import AnyDict
from butcher.parsers.pythonize import pythonize_class_name, pythonize_name


def render_reference(entity: AnyDict) -> str:
    obj = entity["obj"]
    return render_entity_reference(
        category=obj["category"],
        name=entity["name"],
        label=entity["name"],
    )


def render_entity_reference(category: str, name: str, label: str | None = None) -> str:
    return _render_reference(
        "aiogram",
        category,
        pythonize_name(name),
        pythonize_class_name(name),
        label=label,
    )


def _render_reference(*parts: str, label: str | None = None) -> str:
    ref = ".".join(parts)
    if label:
        ref = f"{label} <{ref}>"
    return f":ref:`{ref}`"
