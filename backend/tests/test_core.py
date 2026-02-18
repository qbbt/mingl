from app.correlations import pearson
from app.indicators import ema, sma
from app.leaderboard import DEFAULT_PROFILE, compute_score


def test_pearson_basic_positive() -> None:
    value = pearson([1, 2, 3], [2, 4, 6])
    assert value > 0.99


def test_compute_score_has_expected_directionality() -> None:
    base, _ = compute_score(
        expected_value=10,
        confidence=0.7,
        volatility_penalty=1,
        decay=0.2,
        attention_cost=0.1,
        execution_reliability=0.5,
        profile=DEFAULT_PROFILE,
    )
    higher_ev, _ = compute_score(
        expected_value=20,
        confidence=0.7,
        volatility_penalty=1,
        decay=0.2,
        attention_cost=0.1,
        execution_reliability=0.5,
        profile=DEFAULT_PROFILE,
    )
    assert higher_ev > base


def test_sma_and_ema_shapes() -> None:
    values = [1, 2, 3, 4, 5]
    s = sma(values, 3)
    e = ema(values, 3)
    assert len(s) == len(values)
    assert len(e) == len(values)
    assert s[:2] == [None, None]
    assert e[0] is None


from app.allocation_engine import score_opportunity
from app.transition_engine import first_order_transition


def test_transition_and_allocation_primitives() -> None:
    t = first_order_transition(current_value=100.0, drift=1.5, control=-0.5)
    assert t.next_value == 101.0

    a = score_opportunity(expected_value=12.0, confidence=0.5, best_alternative_ev=10.0)
    assert a.opportunity_cost == 0
    assert a.score == 6.0
