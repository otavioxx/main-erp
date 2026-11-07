from typing import Any


class ComponentMixin:
    def __getattr__(self, name: str) -> Any:
        return getattr(super(), name)
