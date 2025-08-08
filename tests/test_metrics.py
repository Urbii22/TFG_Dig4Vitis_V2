import numpy as np

from ecovid.metrics import compute_coverage_percentage


def test_compute_coverage_percentage_basic():
    leaf = np.zeros((10, 10), dtype=bool)
    leaf[2:8, 2:8] = True  # 36 píxeles
    drops = np.zeros((10, 10), dtype=bool)
    drops[4:6, 4:6] = True  # 4 píxeles

    pct = compute_coverage_percentage(leaf, drops)
    assert abs(pct - (4 / 36 * 100)) < 1e-6


def test_compute_coverage_empty_leaf():
    leaf = np.zeros((5, 5), dtype=bool)
    drops = np.ones((5, 5), dtype=bool)
    assert compute_coverage_percentage(leaf, drops) == 0.0


