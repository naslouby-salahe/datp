from __future__ import annotations

import pytest

from datp.training.fl.convergence import ConvergenceMonitor


def _feed(monitor: ConvergenceMonitor, losses: list[float]) -> int | None:
    for r, loss in enumerate(losses, start=1):
        monitor.record(r, loss)
        if monitor.should_stop(r):
            return r
    return None


class TestConvergenceTrigger:
    def test_convergence_triggers_at_expected_round(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=5,
            rounds_max=100,
            relative_threshold=0.03,
            window=6,
        )
        # Decreasing losses for rounds 1-8, then flat plateau from round 9+
        losses = [1.0, 0.8, 0.6, 0.5, 0.4, 0.35, 0.32, 0.30]
        losses += [0.30] * 10

        stop_round = _feed(monitor, losses)

        assert stop_round is not None
        # Must not fire before rounds_initial (5) or before window (6) losses
        assert stop_round >= 5
        assert stop_round >= 6  # need at least window=6 recorded
        assert monitor.converged_round == stop_round

    def test_gradual_convergence(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=10,
            rounds_max=200,
            relative_threshold=0.05,
            window=10,
        )
        # Exponential decay that flattens, then a long plateau
        losses = [1.0 * (0.95**i) for i in range(30)]
        losses += [losses[-1]] * 20  # flat tail

        stop_round = _feed(monitor, losses)

        assert stop_round is not None
        assert stop_round >= 10  # respects rounds_initial


# rounds_initial guard


class TestRoundsInitialGuard:
    def test_convergence_does_not_fire_before_rounds_initial(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=20,
            rounds_max=100,
            relative_threshold=0.05,
            window=4,
        )
        # Flat losses from the start — convergence criterion would be
        # satisfied if rounds_initial were not enforced.
        flat_losses = [0.5] * 19

        for r, loss in enumerate(flat_losses, start=1):
            monitor.record(r, loss)
            assert not monitor.should_stop(r), (
                f"should_stop fired at round {r}, before rounds_initial=20"
            )

        # Round 20: now it should fire (flat losses, window satisfied)
        monitor.record(20, 0.5)
        assert monitor.should_stop(20)


# Hard cap at rounds_max


class TestHardCap:
    def test_convergence_hard_cap_at_rounds_max(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=5,
            rounds_max=10,
            relative_threshold=0.001,  # Very tight — unlikely to trigger
            window=4,
        )
        # Steadily decreasing — won't satisfy 0.001 threshold easily
        losses = [1.0 - 0.05 * i for i in range(10)]

        stop_round = _feed(monitor, losses)

        assert stop_round == 10, f"Expected hard cap at round 10, got {stop_round}"

    def test_hard_cap_does_not_require_recorded_losses(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=5,
            rounds_max=10,
            relative_threshold=0.03,
            window=4,
        )
        assert monitor.should_stop(10)


# Insufficient history


class TestInsufficientHistory:
    def test_convergence_does_not_fire_without_enough_history(self) -> None:
        window = 8
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=100,
            relative_threshold=0.05,
            window=window,
        )
        # Record window-1 flat losses (would converge with enough data)
        for r in range(1, window):
            monitor.record(r, 0.5)
            assert not monitor.should_stop(r), (
                f"should_stop fired with only {r} recorded losses "
                f"(need window={window})"
            )

        # One more should finally allow convergence check
        monitor.record(window, 0.5)
        assert monitor.should_stop(window)


# from_config


class TestFromConfig:
    def test_from_config(self) -> None:
        from datp.config.compose import BASE_CONFIG
        from datp.config.models import ConvergenceConfig, FederationConfig

        cfg = BASE_CONFIG.model_copy(
            update={
                "federation": FederationConfig(
                    local_epochs=5,
                    convergence=ConvergenceConfig(
                        rounds_initial=40,
                        rounds_max=150,
                        relative_threshold=0.005,
                        window=10,
                        round_timeout_s=300,
                    ),
                ),
            }
        )
        monitor = ConvergenceMonitor.from_config(cfg)

        assert monitor._rounds_initial == 40
        assert monitor._rounds_max == 150
        assert monitor._relative_threshold == 0.005
        assert monitor._window == 10

    def test_from_config_missing_key_raises(self) -> None:
        with pytest.raises(AttributeError):
            ConvergenceMonitor.from_config({"federation": {}})


class TestBaseConfigDefaults:
    def test_base_config_relative_threshold_is_0005(self) -> None:
        from datp.config.compose import BASE_CONFIG

        assert BASE_CONFIG.federation.convergence.relative_threshold == 0.005

    def test_base_config_window_is_10(self) -> None:
        from datp.config.compose import BASE_CONFIG

        assert BASE_CONFIG.federation.convergence.window == 10

    def test_base_config_rounds_initial_is_40(self) -> None:
        from datp.config.compose import BASE_CONFIG

        assert BASE_CONFIG.federation.convergence.rounds_initial == 40

    def test_base_config_rounds_max_is_150(self) -> None:
        from datp.config.compose import BASE_CONFIG

        assert BASE_CONFIG.federation.convergence.rounds_max == 150


class TestValidationErrors:
    def test_rounds_initial_below_one(self) -> None:
        with pytest.raises(ValueError, match=r"rounds_initial must be >= 1"):
            ConvergenceMonitor(
                rounds_initial=0,
                rounds_max=10,
                relative_threshold=0.03,
                window=4,
            )

    def test_rounds_max_below_rounds_initial(self) -> None:
        with pytest.raises(ValueError, match=r"rounds_max must be >= rounds_initial"):
            ConvergenceMonitor(
                rounds_initial=20,
                rounds_max=10,
                relative_threshold=0.03,
                window=4,
            )

    def test_window_below_two(self) -> None:
        with pytest.raises(ValueError, match=r"window must be >= 2"):
            ConvergenceMonitor(
                rounds_initial=5,
                rounds_max=50,
                relative_threshold=0.03,
                window=1,
            )

    def test_error_messages_include_module_prefix(self) -> None:
        with pytest.raises(ValueError, match=r"\[training\.fl\.convergence\]"):
            ConvergenceMonitor(
                rounds_initial=-1,
                rounds_max=10,
                relative_threshold=0.03,
                window=4,
            )


# converged_round logging


class TestConvergedRoundLogged:
    def test_converged_round_logged(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=100,
            relative_threshold=0.05,
            window=4,
        )
        # Before window is filled, converged_round must be None
        for r in range(1, 4):  # rounds 1, 2, 3 — only 3 losses
            monitor.record(r, 0.5)
            monitor.should_stop(r)

        assert monitor.converged_round is None  # only 3 recorded, need 4

        # Round 4 fills the window with flat losses — convergence fires
        monitor.record(4, 0.5)
        assert monitor.should_stop(4)
        assert monitor.converged_round == 4

    def test_converged_round_none_before_convergence(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=10,
            rounds_max=100,
            relative_threshold=0.001,
            window=4,
        )
        # Only record 2 rounds — not enough to converge
        monitor.record(1, 1.0)
        monitor.record(2, 0.5)
        monitor.should_stop(2)

        assert monitor.converged_round is None

    def test_first_converged_round_is_preserved(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=100,
            relative_threshold=0.05,
            window=4,
        )
        for r in range(1, 5):
            monitor.record(r, 0.5)

        assert monitor.should_stop(4)
        assert monitor.converged_round == 4

        monitor.record(5, 0.5)
        assert monitor.should_stop(5)
        assert monitor.converged_round == 4


class TestPreweightedScalar:
    def test_monitor_accepts_preweighted_scalar(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.05,
            window=4,
        )
        # Simulate pre-weighted values (not raw per-client losses)
        preweighted = [0.123, 0.119, 0.115, 0.114, 0.114, 0.114]

        # Record all values manually — _feed stops early on convergence
        for r, loss in enumerate(preweighted, start=1):
            monitor.record(r, loss)

        # All values accepted without TypeError or re-weighting
        assert monitor.num_recorded == len(preweighted)
        assert monitor.should_stop(len(preweighted))

    def test_num_recorded_tracks_calls(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=5,
            rounds_max=50,
            relative_threshold=0.03,
            window=4,
        )
        assert monitor.num_recorded == 0
        monitor.record(1, 0.5)
        assert monitor.num_recorded == 1
        monitor.record(2, 0.4)
        assert monitor.num_recorded == 2


# Edge cases


class TestEdgeCases:
    def test_near_zero_loss_converges(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.05,
            window=4,
        )
        # Very small losses (near zero)
        losses = [1e-15, 1e-15, 1e-15, 1e-15]
        stop_round = _feed(monitor, losses)
        # Should converge (rel_change forced to 0.0)
        assert stop_round is not None

    def test_window_odd_size(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.05,
            window=5,
        )
        losses = [0.5] * 5
        stop_round = _feed(monitor, losses)
        assert stop_round is not None


class TestConvergenceAlgorithm:
    def test_uses_start_and_end_not_half_means(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.05,
            window=4,
        )
        # Window = [1.0, 0.5, 0.5, 0.95]
        # start=1.0, end=0.95 → rel_change = |0.95-1.0|/1.0 = 0.05 (== threshold, not <)
        losses = [1.0, 0.5, 0.5, 0.95]
        for r, loss in enumerate(losses, start=1):
            monitor.record(r, loss)
        # rel_change = 0.05 is NOT < 0.05, so should NOT converge yet
        assert not monitor.should_stop(4)

    def test_converges_when_end_close_to_start(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.05,
            window=4,
        )
        # start=1.0, end=1.04 → rel_change = 0.04 < 0.05 → converged
        losses = [1.0, 0.8, 0.9, 1.04]
        for r, loss in enumerate(losses, start=1):
            monitor.record(r, loss)
        assert monitor.should_stop(4)

    def test_latest_relative_change_tracks_startend(self) -> None:
        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=50,
            relative_threshold=0.10,
            window=4,
        )
        losses = [2.0, 1.5, 1.2, 2.2]
        for r, loss in enumerate(losses, start=1):
            monitor.record(r, loss)
        monitor.should_stop(4)
        # start=2.0, end=2.2 → rel_change = 0.2/2.0 = 0.10
        assert monitor.latest_relative_change == pytest.approx(0.10, abs=1e-9)


# Strategy integration: stall detection and post-convergence scheduling


class TestStallDetection:
    def test_stall_warning_logged(self) -> None:
        import time
        from unittest.mock import MagicMock

        import numpy as np
        import structlog.testing
        from flwr.common import ndarrays_to_parameters

        from datp.training.fl.strategy import DatpFedAvg

        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=10,
            relative_threshold=0.001,
            window=2,
        )
        strategy = DatpFedAvg(
            convergence_monitor=monitor,
            round_timeout_s=0.001,
            fraction_fit=1.0,
            fraction_evaluate=1.0,
            min_fit_clients=1,
            min_evaluate_clients=1,
            min_available_clients=1,
            initial_parameters=ndarrays_to_parameters(
                [np.zeros((4, 3), dtype=np.float32)]
            ),
        )
        strategy._round_start_time = time.monotonic() - 1.0

        mock_proxy = MagicMock()
        mock_result = MagicMock()
        mock_result.num_examples = 100
        mock_result.loss = 0.5

        with structlog.testing.capture_logs() as cap:
            strategy.aggregate_evaluate(
                server_round=1,
                results=[(mock_proxy, mock_result)],
                failures=[],
            )

        assert any(
            "exceeded timeout" in entry.get("event", "")
            or "exceeded timeout" in str(entry)
            for entry in cap
        ), f"Expected stall warning but got: {cap}"


class TestConvergenceScheduling:
    def test_strategy_skips_fit_and_evaluate_after_convergence(self) -> None:
        from unittest.mock import MagicMock

        import numpy as np
        from flwr.common import ndarrays_to_parameters

        from datp.training.fl.strategy import DatpFedAvg

        monitor = ConvergenceMonitor(
            rounds_initial=1,
            rounds_max=10,
            relative_threshold=0.05,
            window=2,
        )
        strategy = DatpFedAvg(
            convergence_monitor=monitor,
            round_timeout_s=300.0,
            fraction_fit=1.0,
            fraction_evaluate=1.0,
            min_fit_clients=1,
            min_evaluate_clients=1,
            min_available_clients=1,
            initial_parameters=ndarrays_to_parameters(
                [np.zeros((2, 2), dtype=np.float32)]
            ),
        )

        mock_proxy = MagicMock()
        mock_result = MagicMock()
        mock_result.num_examples = 100
        mock_result.loss = 0.5

        monitor.record(1, 0.5)
        strategy.aggregate_evaluate(
            server_round=1,
            results=[(mock_proxy, mock_result)],
            failures=[],
        )

        assert strategy.stopped is True
        assert strategy.configure_fit(2, MagicMock(), MagicMock()) == []
        assert strategy.configure_evaluate(2, MagicMock(), MagicMock()) == []
