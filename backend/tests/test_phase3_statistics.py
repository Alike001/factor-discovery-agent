from __future__ import annotations

import math
import re

from app.research.statistics import (
    deflated_sharpe,
    expected_maximum_sharpe,
    probabilistic_sharpe_ratio,
    return_moments,
)


def test_expected_hurdle_does_not_get_easier_as_search_grows() -> None:
    small = expected_maximum_sharpe([-0.2, 0.0, 0.2])
    large = expected_maximum_sharpe([-0.2, 0.0, 0.2, -0.2, 0.0, 0.2])
    assert small["status"] == large["status"] == "OK"
    assert float(large["sr_star"]) >= float(small["sr_star"])


def test_adverse_skew_and_kurtosis_do_not_improve_positive_sharpe_psr() -> None:
    normal = probabilistic_sharpe_ratio(0.2, 0.1, 100, 0.0, 3.0)
    adverse = probabilistic_sharpe_ratio(0.2, 0.1, 100, -1.0, 6.0)
    assert float(adverse["probability"]) <= float(normal["probability"])


def test_single_trial_search_is_explicitly_inconclusive() -> None:
    assert expected_maximum_sharpe([0.2])["status"] == "INCONCLUSIVE_DSR_SEARCH_POPULATION"


def test_zero_return_variance_is_inconclusive() -> None:
    result = deflated_sharpe([0.0] * 100, benchmark_sharpe=0.1, search_n=5, sigma_sr=0.2)
    assert result["reason_code"] == "INCONCLUSIVE_DSR_NUMERICS"


def test_published_equation_fixture_is_reproducible() -> None:
    result = probabilistic_sharpe_ratio(0.15, 0.10, 120, -0.25, 4.5)
    denominator = math.sqrt(1 - (-0.25 * 0.15) + ((4.5 - 1) / 4) * 0.15**2)
    expected = 0.5 * (1 + math.erf(((0.15 - 0.10) * math.sqrt(119) / denominator) / math.sqrt(2)))
    assert math.isclose(float(result["probability"]), expected, rel_tol=1e-12)


def test_return_moments_use_non_excess_kurtosis() -> None:
    moments = return_moments([-2, -1, 0, 1, 2, 0, 0, 0])
    assert moments.kurtosis is not None and moments.kurtosis > 0


def test_persisted_permutation_p_value_excludes_sentence_punctuation() -> None:
    matched = re.search(r"p=([0-9]+(?:\.[0-9]+)?)", "Deterministic 2,000 sign-flip p=0.5952.")
    assert matched and float(matched.group(1)) == 0.5952
