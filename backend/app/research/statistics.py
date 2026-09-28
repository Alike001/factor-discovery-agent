from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

EULER_MASCHERONI = 0.5772156649015329
METHOD_VERSION = "phase3-evidence-v1"


@dataclass(frozen=True)
class ReturnMoments:
    observations: int
    sharpe: float | None
    skew: float | None
    kurtosis: float | None


def return_moments(returns: list[float]) -> ReturnMoments:
    """Per-period Sharpe, adjusted sample skew, and unbiased non-excess kurtosis."""
    size = len(returns)
    if size < 4:
        return ReturnMoments(size, None, None, None)
    mean = statistics.mean(returns)
    sample_std = statistics.stdev(returns)
    if sample_std <= 0:
        return ReturnMoments(size, None, None, None)
    standardized = [(value - mean) / sample_std for value in returns]
    skew = size / ((size - 1) * (size - 2)) * sum(value**3 for value in standardized)
    biased_m2 = sum((value - mean) ** 2 for value in returns) / size
    biased_m4 = sum((value - mean) ** 4 for value in returns) / size
    biased_non_excess = biased_m4 / (biased_m2**2)
    excess = ((size - 1) / ((size - 2) * (size - 3))) * (
        (size + 1) * (biased_non_excess - 3) + 6
    )
    return ReturnMoments(size, mean / sample_std, skew, excess + 3)


def expected_maximum_sharpe(
    sharpes: list[float], *, expected_mean: float = 0.0
) -> dict[str, float | int | str]:
    if len(sharpes) < 2:
        return {"status": "INCONCLUSIVE_DSR_SEARCH_POPULATION", "search_n": len(sharpes)}
    sigma = statistics.stdev(sharpes)
    if not math.isfinite(sigma) or sigma <= 0:
        return {"status": "INCONCLUSIVE_DSR_SEARCH_POPULATION", "search_n": len(sharpes)}
    normal = statistics.NormalDist()
    size = len(sharpes)
    max_z = (1 - EULER_MASCHERONI) * normal.inv_cdf(1 - 1 / size) + EULER_MASCHERONI * normal.inv_cdf(1 - 1 / (size * math.e))
    return {
        "status": "OK",
        "search_n": size,
        "sigma_sr": sigma,
        "expected_mean_sr": expected_mean,
        "max_z": max_z,
        "sr_star": expected_mean + sigma * max_z,
    }


def probabilistic_sharpe_ratio(
    observed_sharpe: float,
    benchmark_sharpe: float,
    observations: int,
    skew: float,
    kurtosis: float,
) -> dict[str, float | int | str]:
    if observations < 2 or not all(math.isfinite(value) for value in (observed_sharpe, benchmark_sharpe, skew, kurtosis)):
        return {"status": "INCONCLUSIVE_DSR_NUMERICS", "observations": observations}
    variance_term = 1 - skew * observed_sharpe + ((kurtosis - 1) / 4) * observed_sharpe**2
    if variance_term <= 0:
        return {"status": "INCONCLUSIVE_DSR_NUMERICS", "observations": observations}
    statistic = (observed_sharpe - benchmark_sharpe) * math.sqrt(observations - 1) / math.sqrt(variance_term)
    return {
        "status": "OK",
        "observations": observations,
        "test_statistic": statistic,
        "probability": statistics.NormalDist().cdf(statistic),
    }


def deflated_sharpe(
    returns: list[float], *, benchmark_sharpe: float, search_n: int, sigma_sr: float,
    threshold: float = 0.90,
) -> dict[str, float | int | str | None]:
    moments = return_moments(returns)
    if moments.sharpe is None or moments.skew is None or moments.kurtosis is None:
        return {
            "status": "INCONCLUSIVE",
            "reason_code": "INCONCLUSIVE_DSR_NUMERICS",
            "observations": moments.observations,
            "observed_sharpe": moments.sharpe,
            "probability": None,
            "threshold": threshold,
            "search_n": search_n,
            "sigma_sr": sigma_sr,
            "method_version": METHOD_VERSION,
        }
    psr = probabilistic_sharpe_ratio(
        moments.sharpe, benchmark_sharpe, moments.observations, moments.skew, moments.kurtosis
    )
    if psr["status"] != "OK":
        probability = None
        outcome = "INCONCLUSIVE"
        reason = str(psr["status"])
    else:
        probability = float(psr["probability"])
        outcome = "PASS" if probability >= threshold else "FAIL"
        reason = "DSR_THRESHOLD_MET" if outcome == "PASS" else "DSR_THRESHOLD_NOT_MET"
    return {
        "status": outcome,
        "reason_code": reason,
        "observations": moments.observations,
        "observed_sharpe": moments.sharpe,
        "benchmark_sharpe": benchmark_sharpe,
        "sigma_sr": sigma_sr,
        "skew": moments.skew,
        "kurtosis": moments.kurtosis,
        "probability": probability,
        "threshold": threshold,
        "search_n": search_n,
        "method_version": METHOD_VERSION,
    }
