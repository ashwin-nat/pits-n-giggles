"""Tests for lib/power_estimator - filter and manager layer."""

import numpy as np
import pytest
from scipy.signal import savgol_filter as scipy_savgol_filter

from lib.power_estimator import BasePowerFilter, PowerEstimator, SavGolPowerFilter
from lib.power_estimator._coefficients import SAVGOL_COEFFS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _feed(filt: BasePowerFilter, times_ms: list[int], energies_j: list[float]) -> None:
    for t, e in zip(times_ms, energies_j):
        filt.update(t, e)


def _make_estimator(window: int = 9, order: int = 3) -> PowerEstimator:
    return PowerEstimator(window, order)


# ---------------------------------------------------------------------------
# SavGolPowerFilter - unit tests
# ---------------------------------------------------------------------------

class TestSavGolPowerFilterConstantEnergy:
    """Constant energy → zero power."""

    @pytest.mark.parametrize("config", list(SAVGOL_COEFFS.keys()))
    def test_zero_power(self, config):
        w, p = config
        filt = SavGolPowerFilter(w, p)
        dt = 16  # ~60 Hz
        times = [i * dt for i in range(w)]
        energies = [100.0] * w
        _feed(filt, times, energies)
        assert filt.is_valid()
        assert abs(filt.get_power_w()) < 1e-6


class TestSavGolPowerFilterLinearEnergy:
    """Linear energy increase E = power_w * t/1000 → constant power output."""

    @pytest.mark.parametrize("config", list(SAVGOL_COEFFS.keys()))
    def test_constant_power(self, config):
        w, p = config
        filt = SavGolPowerFilter(w, p)
        target_w = 500.0          # watts
        dt_ms = 16
        times = [i * dt_ms for i in range(w)]
        # E(t) = P * t_s = P * t_ms / 1000
        energies = [target_w * t / 1000.0 for t in times]
        _feed(filt, times, energies)
        assert filt.is_valid()
        assert abs(filt.get_power_w() - target_w) < 1e-3


class TestSavGolPowerFilterReset:
    def test_valid_before_reset_invalid_after(self):
        w = 9
        filt = SavGolPowerFilter(w)
        dt = 16
        _feed(filt, [i * dt for i in range(w)], [float(i) for i in range(w)])
        assert filt.is_valid()
        filt.reset()
        assert not filt.is_valid()

    def test_power_zero_after_reset(self):
        w = 9
        filt = SavGolPowerFilter(w)
        dt = 16
        _feed(filt, [i * dt for i in range(w)], [float(i * 10) for i in range(w)])
        filt.reset()
        assert filt.get_power_w() == 0.0

    def test_history_cleared_after_reset(self):
        """After reset, previous samples must not affect future output."""
        w = 9
        filt = SavGolPowerFilter(w)
        dt = 16
        # Feed a high-power signal, reset, feed constant energy
        _feed(filt, [i * dt for i in range(w)], [float(i * 1000) for i in range(w)])
        filt.reset()
        # Re-feed with constant energy starting from t=0 again
        _feed(filt, [i * dt for i in range(w)], [50.0] * w)
        assert abs(filt.get_power_w()) < 1e-6


class TestSavGolPowerFilterInsufficientHistory:
    def test_not_valid_with_fewer_than_window_samples(self):
        w = 15
        filt = SavGolPowerFilter(w)
        for i in range(w - 1):
            filt.update(i * 16, float(i))
            assert not filt.is_valid()

    def test_valid_exactly_at_window_size(self):
        w = 15
        filt = SavGolPowerFilter(w)
        for i in range(w):
            filt.update(i * 16, float(i))
        assert filt.is_valid()


class TestSavGolPowerFilterNoisyInput:
    """Noisy linear ramp: output should be close to the reference scipy derivative."""

    def test_noisy_vs_scipy_reference(self):
        rng = np.random.default_rng(42)
        w, p = 15, 3
        n = 100
        dt_ms = 16
        target_w = 300.0

        times = [i * dt_ms for i in range(n)]
        clean = np.array([target_w * t / 1000.0 for t in times])
        noise = rng.normal(0, 0.5, n)
        energies = (clean + noise).tolist()

        # Reference: scipy savgol_filter first derivative, centered (default)
        # We compare at steady-state (after warmup), using edge mode 'nearest'
        dy_scipy = scipy_savgol_filter(energies, w, p, deriv=1, delta=dt_ms / 1000.0)

        filt = SavGolPowerFilter(w, p)
        errors = []
        for i, (t, e) in enumerate(zip(times, energies)):
            filt.update(t, e)
            if filt.is_valid():
                errors.append(abs(filt.get_power_w() - dy_scipy[i]))

        # Median error vs reference should be small (within 10 W)
        assert np.median(errors) < 10.0


class TestSavGolPowerFilterUnsupportedConfig:
    def test_raises_on_bad_config(self):
        with pytest.raises(ValueError):
            SavGolPowerFilter(7, 2)


class TestSavGolOrder1NoOvershoot:
    """Order-1 (linear) fit must not overshoot on a monotonic signal: no negative output and
    no output above the input's own peak accumulation rate. Because a least-squares slope can
    never exceed the steepest rate actually present in the window, the estimate inherits any
    bound the input already respects (e.g. the game-enforced harvest limit) without that bound
    being known or hard-coded here. The cubic fit, by contrast, rings at sharp transitions.
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

    @pytest.mark.parametrize("w", [9, 15, 21])
    def test_order1_never_negative_or_overshoots(self, w):
        dt_ms, rate_w, n, plateau_start = 16, 400.0, 60, 30
        times, energies = self._kinked_energy(n, dt_ms, rate_w, plateau_start)

        filt = SavGolPowerFilter(w, 1)
        outs = []
        for t, e in zip(times, energies):
            filt.update(t, e)
            if filt.is_valid():
                outs.append(filt.get_power_w())

        assert outs                       # produced steady-state output
        assert min(outs) >= -1e-6         # no negative overshoot
        assert max(outs) <= rate_w + 1e-6  # never exceeds the input's own peak rate (no overshoot)

    def test_order3_overshoots_negative_where_order1_does_not(self):
        """Contrast: the cubic fit rings below zero on the same signal; the linear fit does not."""
        dt_ms, rate_w, n, plateau_start = 16, 400.0, 60, 30
        times, energies = self._kinked_energy(n, dt_ms, rate_w, plateau_start)

        cubic = SavGolPowerFilter(15, 3)
        linear = SavGolPowerFilter(15, 1)
        cubic_min = linear_min = float("inf")
        for t, e in zip(times, energies):
            cubic.update(t, e)
            linear.update(t, e)
            if cubic.is_valid():
                cubic_min = min(cubic_min, cubic.get_power_w())
                linear_min = min(linear_min, linear.get_power_w())

        assert cubic_min < -1e-6    # cubic overshoots negative (the artifact being avoided)
        assert linear_min >= -1e-6  # linear stays non-negative


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
