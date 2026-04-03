"""Tests for the composite_score function from backtest.py."""

from backtest import composite_score


class TestCompositeScoreGatesPass:
    """All gates pass with normal metrics -- score should be near 1.0."""

    def test_ideal_sprint(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": 50000,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        assert 0.85 <= score <= 1.0, f"Expected near 1.0, got {score}"

    def test_gates_pass_moderate_tokens(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": 200000,
            "loc_added": 400,
            "active_session_time_s": 1800,
            "context_compressions": 1,
        }
        score = composite_score(m)
        assert 0.5 <= score <= 1.0, f"Expected reasonable score, got {score}"


class TestCompositeScoreGatesFail:
    """Gates fail -- quality component should be 0.0."""

    def test_gates_fail_zeroes_quality(self):
        m = {
            "gates_first_pass": False,
            "new_work_tokens": 50000,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        # quality is 40% of total, so max possible is 0.60
        assert score <= 0.60, f"Expected <= 0.60 with failed gates, got {score}"

    def test_gates_fail_vs_pass_lower(self):
        base = {
            "new_work_tokens": 100000,
            "loc_added": 400,
            "active_session_time_s": 1200,
            "context_compressions": 0,
        }
        fail_score = composite_score({**base, "gates_first_pass": False})
        pass_score = composite_score({**base, "gates_first_pass": True})
        assert fail_score < pass_score


class TestCompositeScoreGatesNone:
    """Gates None (planning-only sprints) -- quality component should be 0.5."""

    def test_gates_none_mid_quality(self):
        m = {
            "gates_first_pass": None,
            "new_work_tokens": 50000,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        # quality component = 0.5 * 0.40 = 0.20 instead of 0.40
        # Should be between fail (0.0 quality) and pass (1.0 quality)
        fail_score = composite_score({**m, "gates_first_pass": False})
        pass_score = composite_score({**m, "gates_first_pass": True})
        assert fail_score < score < pass_score


class TestCompositeScoreMissingTokens:
    """Missing new_work_tokens -- should use sensible default (0.5)."""

    def test_missing_new_work_tokens(self):
        m = {
            "gates_first_pass": True,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        # token_score defaults to 0.5 when nw is None
        assert 0.5 <= score <= 1.0, f"Expected reasonable score, got {score}"

    def test_none_new_work_tokens(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": None,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        assert isinstance(score, float)

    def test_zero_loc_defaults_token_score(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": 100000,
            "loc_added": 0,
            "active_session_time_s": 600,
            "context_compressions": 0,
        }
        score = composite_score(m)
        # loc=0 means token_score defaults to 0.5
        assert isinstance(score, float)


class TestCompositeScoreHighCompressions:
    """High context compressions -- autonomy should be 0.0."""

    def test_five_compressions_zero_autonomy(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": 50000,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 5,
        }
        score = composite_score(m)
        # autonomy = max(0, 1 - 5/5) = 0.0, so lose 0.15 * 1.0 = 0.15
        score_no_comp = composite_score({**m, "context_compressions": 0})
        assert score < score_no_comp

    def test_ten_compressions_clamped(self):
        m = {
            "gates_first_pass": True,
            "new_work_tokens": 50000,
            "loc_added": 500,
            "active_session_time_s": 600,
            "context_compressions": 10,
        }
        score = composite_score(m)
        # autonomy = max(0, 1 - 10/5) = 0.0 (clamped)
        score_five = composite_score({**m, "context_compressions": 5})
        assert score == score_five, "Compressions beyond 5 should not further reduce score"
