from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Taxonomy:
    raw_to_training: dict[int, int]
    class_names: tuple[str, ...]
    ignore_index: int

    @property
    def class_count(self) -> int:
        return len(self.class_names)

    def remap(self, raw_mask: NDArray[np.integer]) -> NDArray[np.uint8]:
        unique_values = {int(value) for value in np.unique(raw_mask)}
        unknown_values = sorted(unique_values.difference(self.raw_to_training))
        if unknown_values:
            labels = ", ".join(str(value) for value in unknown_values)
            raise ValueError(f"Unexpected raw labels: {labels}")

        remapped = np.full(raw_mask.shape, self.ignore_index, dtype=np.uint8)
        for raw_value, training_value in self.raw_to_training.items():
            remapped[raw_mask == raw_value] = training_value
        return remapped
