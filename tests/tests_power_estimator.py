"""Tests for lib/power_estimator - filter and manager layer."""

import numpy as np
import pytest

from lib.power_estimator import BasePowerFilter, LinearSlopePowerFilter, PowerEstimator

WINDOWS = [7, 11, 15, 21, 27]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _feed(filt: BasePowerFilter, times_ms: list[int], energies_j: list[float]) -> None:
    for t, e in zip(times_ms, energies_j):
        filt.update(t, e)


def _make_estimator(window: int = 9) -> PowerEstimator:
    return PowerEstimator(window)


# ---------------------------------------------------------------------------
# LinearSlopePowerFilter - unit tests
# ---------------------------------------------------------------------------

class TestLinearSlopePowerFilterConstantEnergy:
    """Constant energy -> zero power."""

    @pytest.mark.parametrize("w", WINDOWS)
    def test_zero_power(self, w):
        filt = LinearSlopePowerFilter(w)
        dt = 16  # ~60 Hz
        times = [i * dt for i in range(w)]
        energies = [100.0] * w
        _feed(filt, times, energies)
        assert filt.is_valid()
        assert abs(filt.get_power_w()) < 1e-6


class TestLinearSlopePowerFilterLinearEnergy:
    """Linear energy increase E = power_w * t/1000 -> constant power output."""

    @pytest.mark.parametrize("w", WINDOWS)
    def test_constant_power(self, w):
        filt = LinearSlopePowerFilter(w)
        target_w = 500.0          # watts
        dt_ms = 16
        times = [i * dt_ms for i in range(w)]
        # E(t) = P * t_s = P * t_ms / 1000
        energies = [target_w * t / 1000.0 for t in times]
        _feed(filt, times, energies)
        assert filt.is_valid()
        assert abs(filt.get_power_w() - target_w) < 1e-6


class TestLinearSlopePowerFilterNonUniformSpacing:
    """The regression runs against actual timestamps, so irregular spacing is exact."""

    def test_irregular_timestamps_exact_slope(self):
        # Perfectly linear energy at 250 W, but with jittered/dropped sample timings.
        times = [0, 10, 35, 60, 100, 130, 175, 210]
        power = 250.0
        energies = [power * t / 1000.0 for t in times]
        filt = LinearSlopePowerFilter(len(times))
        _feed(filt, times, energies)
        assert filt.is_valid()
        assert abs(filt.get_power_w() - power) < 1e-6


class TestLinearSlopePowerFilterReset:
    def test_valid_before_reset_invalid_after(self):
        w = 9
        filt = LinearSlopePowerFilter(w)
        dt = 16
        _feed(filt, [i * dt for i in range(w)], [float(i) for i in range(w)])
        assert filt.is_valid()
        filt.reset()
        assert not filt.is_valid()

    def test_power_zero_after_reset(self):
        w = 9
        filt = LinearSlopePowerFilter(w)
        dt = 16
        _feed(filt, [i * dt for i in range(w)], [float(i * 10) for i in range(w)])
        filt.reset()
        assert filt.get_power_w() == 0.0

    def test_history_cleared_after_reset(self):
        """After reset, previous samples must not affect future output."""
        w = 9
        filt = LinearSlopePowerFilter(w)
        dt = 16
        # Feed a high-power signal, reset, feed constant energy
        _feed(filt, [i * dt for i in range(w)], [float(i * 1000) for i in range(w)])
        filt.reset()
        # Re-feed with constant energy starting from t=0 again
        _feed(filt, [i * dt for i in range(w)], [50.0] * w)
        assert abs(filt.get_power_w()) < 1e-6


class TestLinearSlopePowerFilterInsufficientHistory:
    def test_not_valid_with_fewer_than_window_samples(self):
        w = 15
        filt = LinearSlopePowerFilter(w)
        for i in range(w - 1):
            filt.update(i * 16, float(i))
            assert not filt.is_valid()

    def test_valid_exactly_at_window_size(self):
        w = 15
        filt = LinearSlopePowerFilter(w)
        for i in range(w):
            filt.update(i * 16, float(i))
        assert filt.is_valid()


class TestLinearSlopePowerFilterReference:
    """Output must equal the numpy least-squares slope over the same window."""

    def test_noisy_vs_polyfit_reference(self):
        rng = np.random.default_rng(42)
        w = 15
        n = 80
        dt_ms = 16
        target_w = 300.0

        times = [i * dt_ms for i in range(n)]
        clean = np.array([target_w * t / 1000.0 for t in times])
        energies = (clean + rng.normal(0, 0.5, n)).tolist()

        filt = LinearSlopePowerFilter(w)
        for i, (t, e) in enumerate(zip(times, energies)):
            filt.update(t, e)
            if filt.is_valid():
                win_t = np.array(times[i - w + 1:i + 1], dtype=float)
                win_e = np.array(energies[i - w + 1:i + 1])
                slope_per_ms = np.polyfit(win_t, win_e, 1)[0]
                assert abs(filt.get_power_w() - slope_per_ms * 1000.0) < 1e-6


class TestLinearSlopePowerFilterZeroVariance:
    """All timestamps identical → var == 0, _power_w must not change."""

    def test_power_unchanged_when_all_timestamps_equal(self):
        w = 5
        filt = LinearSlopePowerFilter(w)
        # Feed w samples all at the same timestamp — var of t will be 0.0
        for _ in range(w):
            filt.update(100, 50.0)
        assert filt.is_valid()
        assert filt.get_power_w() == 0.0


class TestLinearSlopePowerFilterBadConfig:
    @pytest.mark.parametrize("w", [1, 0, -3])
    def test_raises_on_window_below_two(self, w):
        with pytest.raises(ValueError):
            LinearSlopePowerFilter(w)


class TestLinearSlopeNoOvershoot:
    """A linear fit must not overshoot on a monotonic signal: no negative output and no output
    above the input's own peak accumulation rate. A least-squares slope over monotonic data lies
    between the slowest and steepest rate present in the window, so the estimate inherits any bound
    the input already respects (e.g. the game-enforced harvest limit) without it being hard-coded.
    """

    @staticmethod
    def _kinked_energy(n: int, dt_ms: int, rate_w: float, plateau_start: int):
        """Monotonic energy that ramps at ``rate_w`` then plateaus — a sharp kink."""
        times, energies, e = [], [], 0.0
        for i in range(n):
            times.append(i * dt_ms)
            if i < plateau_start:
                e += rate_w * dt_ms / 1000.0
            energies.append(e)
        return times, energies

    @pytest.mark.parametrize("w", WINDOWS)
    def test_never_negative_or_overshoots(self, w):
        dt_ms, rate_w, n, plateau_start = 16, 400.0, 80, 40
        times, energies = self._kinked_energy(n, dt_ms, rate_w, plateau_start)

        filt = LinearSlopePowerFilter(w)
        outs = []
        for t, e in zip(times, energies):
            filt.update(t, e)
            if filt.is_valid():
                outs.append(filt.get_power_w())

        assert outs                        # produced steady-state output
        assert min(outs) >= -1e-6          # no negative overshoot
        assert max(outs) <= rate_w + 1e-6  # never exceeds the input's own peak rate


# ---------------------------------------------------------------------------
# PowerEstimator - manager layer tests
# ---------------------------------------------------------------------------

class TestPowerEstimatorValidityPassthrough:
    def test_not_valid_before_warmup(self):
        est = _make_estimator()
        assert not est.is_valid()

    def test_valid_after_warmup(self):
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i))
        assert est.is_valid()


class TestPowerEstimatorOutputPassthrough:
    def test_power_correct_on_linear_ramp(self):
        target_w = 500.0
        dt_ms = 16
        w = 9
        est = PowerEstimator(w)
        for i in range(w):
            est.update(i * dt_ms, target_w * (i * dt_ms) / 1000.0)
        assert abs(est.get_power_w() - target_w) < 1e-3


class TestPowerEstimatorResetPropagation:
    def test_explicit_reset_invalidates(self):
        est = _make_estimator()
        for i in range(9):
            est.update(i * 16, float(i))
        assert est.is_valid()
        est.reset()
        assert not est.is_valid()

    def test_explicit_reset_clears_last_time(self):
        """After reset, no discontinuity detected on next update - clean restart."""
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i))
        est.reset()
        # Feed from t=0 again - should not trigger another reset inside
        for i in range(9):
            est.update(i * 16, float(i))
        assert est.is_valid()


class TestPowerEstimatorTimeRegression:
    def test_time_regression_triggers_reset(self):
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i))
        assert est.is_valid()
        # Send a sample with a timestamp that goes backwards
        est.update(50, 100.0)
        assert not est.is_valid()

    def test_equal_timestamp_triggers_reset(self):
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i))
        last_t = 8 * 16
        est.update(last_t, 999.0)
        assert not est.is_valid()


class TestPowerEstimatorLapChange:
    def test_lap_change_triggers_reset(self):
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i), lap_number=1)
        assert est.is_valid()
        # New lap - should reset
        est.update(9 * 16, float(9), lap_number=2)
        assert not est.is_valid()

    def test_same_lap_does_not_reset(self):
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i), lap_number=3)
        assert est.is_valid()
        est.update(9 * 16, float(9), lap_number=3)
        assert est.is_valid()

    def test_none_lap_does_not_reset(self):
        """lap_number=None should never trigger a lap-based reset."""
        est = _make_estimator(window=9)
        for i in range(9):
            est.update(i * 16, float(i), lap_number=None)
        assert est.is_valid()
        est.update(9 * 16, float(9), lap_number=None)
        assert est.is_valid()
