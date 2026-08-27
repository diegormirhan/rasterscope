from rasterscope.ml.splits import create_split_manifest


def test_split_manifest_is_deterministic_and_disjoint() -> None:
    first = create_split_manifest(sample_count=20, seed=7, train_ratio=0.7, validation_ratio=0.15)
    second = create_split_manifest(sample_count=20, seed=7, train_ratio=0.7, validation_ratio=0.15)

    assert first == second
    assert len(first.train) == 14
    assert len(first.validation) == 3
    assert len(first.test) == 3
    assert set(first.train).isdisjoint(first.validation)
    assert set(first.train).isdisjoint(first.test)
    assert sorted(first.train + first.validation + first.test) == list(range(20))


def test_split_manifest_rejects_invalid_ratios() -> None:
    try:
        create_split_manifest(10, seed=1, train_ratio=0.9, validation_ratio=0.2)
    except ValueError as error:
        assert "sum to less than 1" in str(error)
    else:
        raise AssertionError("Expected invalid ratios to raise ValueError")
