import pandas as pd

from bloom_graphs import bloom_table


def test_one_edge_per_level_with_count_as_thickness():
    answers = pd.DataFrame({
        "question_id": list(range(1, 14)),
        "answerer_id": [1] * 12 + [9],
        "asker_id": [2] * 13,
    })
    levels = (["Remembering"] * 3 + ["Analyzing"] * 2 + ["Evaluating"] * 5
              + ["Unclassified"] * 2 + ["Creating"])
    bloom = pd.Series(levels, index=range(1, 14))

    table, excluded = bloom_table(answers, bloom, {1, 2})

    result = {(r.answerer_id, r.asker_id, r.bloom_level): r.n_answers
              for r in table.itertuples()}
    assert result == {
        (1, 2, "Remembering"): 3,
        (1, 2, "Analyzing"): 2,
        (1, 2, "Evaluating"): 5,
    }
    assert excluded == 2


def test_questions_missing_from_the_bloom_file_are_excluded():
    answers = pd.DataFrame({"question_id": [1, 2], "answerer_id": [1, 1], "asker_id": [2, 2]})
    bloom = pd.Series(["Applying"], index=[1])
    table, excluded = bloom_table(answers, bloom, {1, 2})
    assert len(table) == 1
    assert excluded == 1
