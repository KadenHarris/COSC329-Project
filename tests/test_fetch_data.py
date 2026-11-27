import pandas as pd

import fetch_data
from fetch_data import clean_body, has_user

QUESTIONS = [
    {"question_id": 1, "title": "How do I &quot;sort&quot; a list?",
     "body": "<p>Hi</p><pre><code>x = 1</code></pre><p>thanks</p>",
     "owner": {"user_id": 10, "display_name": "Alice &amp; Co", "user_type": "registered"},
     "score": 5, "answer_count": 2, "creation_date": 1, "tags": ["python", "list"]},
    {"question_id": 2, "title": "Asked by a deleted user", "body": "<p>x</p>",
     "owner": {"user_type": "does_not_exist", "display_name": "user1"},
     "score": 1, "answer_count": 1, "creation_date": 2, "tags": ["python"]},
    {"question_id": 3, "title": "No answers", "body": "",
     "owner": {"user_id": 11, "display_name": "Bob"},
     "score": 0, "answer_count": 0, "creation_date": 3, "tags": ["python"]},
]

ANSWERS = [
    {"answer_id": 100, "question_id": 1, "score": 3, "is_accepted": True,
     "owner": {"user_id": 12, "display_name": "Carol", "user_type": "registered"}},
    {"answer_id": 101, "question_id": 1, "score": 0, "is_accepted": False,
     "owner": {"user_type": "does_not_exist"}},
]


def fake_api_get(session, path, params, retries=5):
    items = QUESTIONS if path == "/questions" else ANSWERS
    return {"items": items, "has_more": False, "quota_remaining": 9000}


def test_clean_body_strips_html_and_code():
    html = "<p>Hi <b>there</b></p><pre><code>x = 1</code></pre><p>Use <code>len</code> here</p>"
    assert clean_body(html) == "Hi there Use here"


def test_has_user_rejects_deleted_and_missing_owners():
    assert has_user({"owner": {"user_id": 5, "user_type": "registered"}})
    assert not has_user({"owner": {"user_type": "does_not_exist"}})
    assert not has_user({})


def test_main_writes_cleaned_csvs(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "api_get", fake_api_get)
    monkeypatch.setenv("SE_API_KEY", "test")
    monkeypatch.setattr("sys.argv", ["fetch_data.py"])
    monkeypatch.chdir(tmp_path)

    fetch_data.main()

    q = pd.read_csv(tmp_path / "data" / "questions.csv")
    a = pd.read_csv(tmp_path / "data" / "answers.csv")
    assert list(q["question_id"]) == [1]
    assert q.loc[0, "title"] == 'How do I "sort" a list?'
    assert q.loc[0, "asker_name"] == "Alice & Co"
    assert q.loc[0, "body_text"] == "Hi thanks"
    assert q.loc[0, "tags"] == "python;list"
    assert list(a["answer_id"]) == [100]
