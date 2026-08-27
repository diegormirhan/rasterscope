import numpy as np

from rasterscope.domain.analysis import (
    calculate_area_summary,
    calculate_transition_matrix,
    normalized_entropy,
)


def test_area_summary_converts_pixels_to_hectares() -> None:
    mask = np.array([[0, 0], [1, 255]], dtype=np.uint8)

    areas = calculate_area_summary(mask, class_count=2, meters_per_pixel=10, ignore_index=255)

    assert areas.pixel_counts == (2, 1)
    assert areas.hectares == (0.02, 0.01)
    assert areas.valid_hectares == 0.03


def test_transition_matrix_counts_only_valid_aligned_pixels() -> None:
    before = np.array([[0, 0], [1, 255]], dtype=np.uint8)
    after = np.array([[0, 1], [1, 0]], dtype=np.uint8)

    matrix = calculate_transition_matrix(before, after, class_count=2, ignore_index=255)

    assert matrix.tolist() == [[1, 1], [0, 1]]


def test_normalized_entropy_is_zero_for_certainty_and_one_for_uniform_distribution() -> None:
    probabilities = np.array(
        [
            [[1.0, 0.0], [0.5, 0.5]],
            [[0.0, 1.0], [0.5, 0.5]],
        ],
        dtype=np.float32,
    )

    entropy = normalized_entropy(probabilities)

    assert np.allclose(entropy[0], [0.0, 0.0])
    assert np.allclose(entropy[1], [1.0, 1.0])
