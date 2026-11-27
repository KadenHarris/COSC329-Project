import pandas as pd
import pytest

from centrality import compute_centrality


@pytest.fixture
def scores():
    edges = pd.DataFrame({
        "answerer_id": ["A", "A", "D"],
        "asker_id": ["B", "C", "B"],
        "weight": [1, 1, 1],
    })
    return compute_centrality(edges)


def test_out_degree_is_share_of_users_answered(scores):
    assert scores.loc["A", "out_degree"] == pytest.approx(2 / 3)
    assert scores.loc["D", "out_degree"] == pytest.approx(1 / 3)
    assert scores.loc["B", "out_degree"] == 0


def test_in_degree_is_share_of_users_who_answered(scores):
    assert scores.loc["B", "in_degree"] == pytest.approx(2 / 3)
    assert scores.loc["C", "in_degree"] == pytest.approx(1 / 3)
    assert scores.loc["A", "in_degree"] == 0


def test_hub_scores_favour_the_answerer_of_more_askers(scores):
    assert scores.loc["A", "hub"] == pytest.approx(0.618, abs=1e-3)
    assert scores.loc["D", "hub"] == pytest.approx(0.382, abs=1e-3)
    assert scores.loc["B", "hub"] == pytest.approx(0, abs=1e-9)


def test_authority_scores_favour_the_asker_answered_by_more_hubs(scores):
    assert scores.loc["B", "authority"] == pytest.approx(0.618, abs=1e-3)
    assert scores.loc["C", "authority"] == pytest.approx(0.382, abs=1e-3)
    assert scores.loc["A", "authority"] == pytest.approx(0, abs=1e-9)
