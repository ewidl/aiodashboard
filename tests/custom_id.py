from dataclasses import dataclass

@dataclass(order=True)
class CustomID:
    id1: int
    id2: str

    def __repr__(self) -> str:
        return f'CustomID / {self.id1} / {self.id2}'
