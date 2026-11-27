import pandas as pd

from build_graph import load_edges, select_users, user_activity, user_names


def make_data():
    q = pd.DataFrame({
        "question_id": [1, 2, 3, 4],
        "asker_id": [10, 10, 20, 30],
        "asker_name": ["Bea", "Bea", "Cy", "Di"],
    })
    a = pd.DataFrame({
        "answer_id": [100, 101, 102, 103, 104, 105],
        "question_id": [1, 2, 2, 3, 4, 1],
        "answerer_id": [1, 1, 2, 1, 30, 10],
        "answerer_name": ["Al", "Al", "Ed", "Al", "Di", "Bea"],
    })
    return q, a


def edge_dict(edges):
    return {(r.answerer_id, r.asker_id): r.weight for r in edges.itertuples()}


def test_load_edges_counts_questions_answered_per_pair():
    q, a = make_data()
    edges, _ = load_edges(q, a)
    assert edge_dict(edges) == {(1, 10): 2, (2, 10): 1, (1, 20): 1}


def test_load_edges_drops_self_answers():
    q, a = make_data()
    edges, answers = load_edges(q, a)
    assert (30, 30) not in edge_dict(edges)
    assert (10, 10) not in edge_dict(edges)
    assert len(answers) == 4


def test_user_activity_is_questions_asked_plus_answers_given():
    q, a = make_data()
    _, answers = load_edges(q, a)
    act = user_activity(q, answers)
    assert act.loc[1].to_dict() == {"questions_asked": 0, "answers_given": 3, "activity": 3}
    assert act.loc[10].to_dict() == {"questions_asked": 2, "answers_given": 0, "activity": 2}
    assert act.loc[30, "activity"] == 1


def test_select_users_starts_with_heaviest_pair():
    q, a = make_data()
    edges, answers = load_edges(q, a)
    assert select_users(edges, user_activity(q, answers), 2) == {1, 10}


def test_select_users_breaks_ties_by_activity_and_respects_limit():
    q, a = make_data()
    edges, answers = load_edges(q, a)
    selected = select_users(edges, user_activity(q, answers), 3)
    assert selected == {1, 10, 20}


def test_user_names_covers_askers_and_answerers():
    q, a = make_data()
    assert user_names(q, a) == {10: "Bea", 20: "Cy", 30: "Di", 1: "Al", 2: "Ed"}
