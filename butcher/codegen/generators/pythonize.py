def pythonize_name(name: str) -> str:
    return "".join(f"_{s}" if i > 0 and s.isupper() else s for i, s in enumerate(name)).lower()


def pythonize_class_name(name: str) -> str:
    return name[0].upper() + name[1:]
