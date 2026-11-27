import pandas as pd
import pytest

import bloom_graphs
import build_graph
import centrality
import classify

QUESTIONS = [
    (1, "Why does my loop skip items?", 10),
    (2, "How to create a dictionary from two lists", 10),
    (3, "How do I get the last element", 11),
    (4, "Remove a prefix from a string", 11),
    (5, "What does the yield keyword do?", 12),
]
ANSWERS = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 3)]


@pytest.fixture
def project(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    pd.DataFrame({
        "question_id": [q[0] for q in QUESTIONS],
        "title": [q[1] for q in QUESTIONS],
        "body_text": "",
        "asker_id": [q[2] for q in QUESTIONS],
        "asker_name": [f"user{q[2]}" for q in QUESTIONS],
    }).to_csv(tmp_path / "data" / "questions.csv", index=False)
    pd.DataFrame({
        "answer_id": range(len(ANSWERS)),
        "question_id": [a[1] for a in ANSWERS],
        "answerer_id": [a[0] for a in ANSWERS],
        "answerer_name": [f"user{a[0]}" for a in ANSWERS],
    }).to_csv(tmp_path / "data" / "answers.csv", index=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["build_graph.py", "--top", "4"])
    return tmp_path


def test_full_pipeline(project):
    build_graph.main()
    centrality.main()
    classify.main()
    bloom_graphs.main()

    out = project / "output"
    for name in ["original_graph.png", "bloom_graph.png", "bloom_levels.png"]:
        assert (out / name).stat().st_size > 0

    nodes = pd.read_csv(out / "top_nodes.csv")
    assert set(nodes["user_id"]) == {1, 10, 11, 12}

    cent = pd.read_csv(out / "centrality.csv").set_index("user_id")
    assert set(cent.index) == {1, 10, 11, 12}
    assert cent.loc[1, "out_degree"] == pytest.approx(3 / 4)
    assert cent.loc[1, "in_degree"] == 0

    levels = pd.read_csv(project / "data" / "questions_bloom.csv")["bloom_level"].tolist()
    assert levels == ["Analyzing", "Creating", "Applying", "Unclassified", "Understanding"]

    bloom = pd.read_csv(out / "bloom_edges.csv")
    assert set(zip(bloom["source"], bloom["target"], bloom["bloom_level"])) == {
        (1, 10, "Analyzing"), (1, 10, "Creating"),
        (1, 11, "Applying"), (1, 12, "Understanding"),
    }
