from butcher.common_types import AnyDict


def args_as_str(*args, _trailing_coma: bool = False, **kwargs):
    result = ", ".join([*args, *[f"{k}={v}" for k, v in kwargs.items()]])
    if _trailing_coma and result:
        result += ","
    return result


def annotation_as_str(annotation: AnyDict, as_field: bool = False) -> str:
    name = annotation["name"]
    hint = type_as_str(annotation["parsed_type"])

    field_kwargs = {}

    value = annotation.get("value", None)
    if not annotation["required"]:
        hint = f"Optional[{hint}]"
        if not value:
            value = "None"

    if const := annotation.get("const"):
        value = const
        field_kwargs["const"] = "True"

    if alias := annotation.get("alias"):
        field_kwargs["alias"] = repr(alias)

    result = f"{name}: {hint}"

    if value or field_kwargs:
        if as_field and field_kwargs:
            value = f"Field({args_as_str(value or '...', **field_kwargs)})"
        result += f" = {value}"

    return result


def type_as_str(value: AnyDict) -> str:
    if value["type"] == "std":
        return value["name"]
    if value["type"] == "array":
        return f"List[{type_as_str(value['items'])}]"
    if value["type"] == "entity":
        return value["references"]["name"]
    if value["type"] == "union":
        union_types = ", ".join(type_as_str(union_type) for union_type in value["items"])
        return f"Union[{union_types}]"

    raise NotImplementedError(f"Rendering of type {value} is not supported")
