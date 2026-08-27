import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class SplitManifest:
    seed: int
    sample_count: int
    train: list[int]
    validation: list[int]
    test: list[int]

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "SplitManifest":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


def create_split_manifest(
    sample_count: int,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> SplitManifest:
    if sample_count < 3:
        raise ValueError("At least three samples are required")
    if train_ratio <= 0 or validation_ratio <= 0 or train_ratio + validation_ratio >= 1:
        raise ValueError("Train and validation ratios must be positive and sum to less than 1")

    shuffled = np.random.default_rng(seed).permutation(sample_count).tolist()
    train_end = round(sample_count * train_ratio)
    validation_end = train_end + round(sample_count * validation_ratio)
    return SplitManifest(
        seed=seed,
        sample_count=sample_count,
        train=sorted(shuffled[:train_end]),
        validation=sorted(shuffled[train_end:validation_end]),
        test=sorted(shuffled[validation_end:]),
    )
