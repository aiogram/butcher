def camel_to_snake_case(name: str) -> str:
    return "".join(f"_{s}" if i > 0 and s.isupper() else s for i, s in enumerate(name)).lower()
