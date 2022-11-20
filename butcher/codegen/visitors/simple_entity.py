from typing import Optional

from libcst import ClassDef, CSTVisitor


class EntityVisitor(CSTVisitor):
    def __init__(self):
        super().__init__()

        self.entities = {}

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        self.entities[node.name.value] = node
        return True
