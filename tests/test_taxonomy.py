import numpy as np

from rasterscope.ml.taxonomy import Taxonomy


def test_remap_groups_sparse_worldcover_classes() -> None:
    taxonomy = Taxonomy(
        raw_to_training={0: 255, 10: 0, 20: 1, 30: 1, 80: 2},
        class_names=("Trees", "Low vegetation", "Water"),
        ignore_index=255,
    )
    raw_mask = np.array([[0, 10, 20], [30, 80, 10]], dtype=np.uint8)

    remapped = taxonomy.remap(raw_mask)

    assert remapped.tolist() == [[255, 0, 1], [1, 2, 0]]


def test_remap_rejects_unknown_raw_value() -> None:
    taxonomy = Taxonomy(
        raw_to_training={0: 255, 10: 0},
        class_names=("Trees",),
        ignore_index=255,
    )

    with np.testing.assert_raises_regex(ValueError, "Unexpected raw labels: 42"):
        taxonomy.remap(np.array([[10, 42]], dtype=np.uint8))
