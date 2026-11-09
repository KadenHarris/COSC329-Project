"""
Week 8: collect StackOverflow questions + answers for one tag via the
Stack Exchange API and save cleaned CSVs.

Usage:
    python fetch_data.py --tag python --max-questions 3000 --key YOUR_API_KEY

Outputs (in --outdir, default ./data):
    raw/questions_raw.json, raw/answers_raw.json   (unmodified API responses)
    questions.csv  question_id, title, body_text, asker_id, asker_name,
                   score, answer_count, creation_date, tags
    answers.csv    answer_id, question_id, answerer_id, answerer_name,
                   score, is_accepted

Cleaning applied:
    - questions/answers from deleted users (no user_id) are dropped
    - HTML is stripped from question bodies and code blocks are removed
    - self-answers (answerer == asker) are dropped in build_graph.py
"""
import argparse
import html
import json
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

API = "https://api.stackexchange.com/2.3"


def api_get(session, path, params, retries=5):
    """GET with backoff handling. Returns the parsed JSON response."""
    for attempt in range(retries):
        resp = session.get(f"{API}{path}", params=params, timeout=30)
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code == 200:
            # The API may tell us to wait before the next request.
            wait = data.get("backoff", 0)
            time.sleep(max(wait + 1, 0.15) if wait else 0.15)
            if data.get("quota_remaining", 1) < 10:
                raise SystemExit("API quota nearly exhausted; try again tomorrow "
                                 "or use an API key.")
            return data
        # throttle / transient errors: wait and retry
        print(f"  HTTP {resp.status_code} {data.get('error_message', '')} "
              f"(attempt {attempt + 1}/{retries})")
        time.sleep(5 * (attempt + 1))
    raise SystemExit(f"Request failed after {retries} attempts: {path}")


def fetch_questions(session, tag, max_questions, key):
    """Most-voted answered questions for a tag, with body text."""
    items, page = [], 1
    while len(items) < max_questions:
        params = {
            "site": "stackoverflow", "tagged": tag, "sort": "votes",
            "order": "desc", "pagesize": 100, "page": page,
            "filter": "withbody",
        }
        if key:
            params["key"] = key
        data = api_get(session, "/questions", params)
        items.extend(q for q in data.get("items", []) if q.get("answer_count", 0) > 0)
        print(f"questions page {page}: {len(items)} collected "
              f"(quota left {data.get('quota_remaining')})")
        if not data.get("has_more"):
            break
        page += 1
    return items[:max_questions]


def fetch_answers(session, question_ids, key):
    """Answers for questions, 100 question ids per request."""
    items = []
    for i in range(0, len(question_ids), 100):
        chunk = ";".join(str(q) for q in question_ids[i:i + 100])
        page = 1
        while True:
            params = {"site": "stackoverflow", "pagesize": 100, "page": page}
            if key:
                params["key"] = key
            data = api_get(session, f"/questions/{chunk}/answers", params)
            items.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page += 1
        print(f"answers: {len(items)} collected "
              f"({min(i + 100, len(question_ids))}/{len(question_ids)} questions)")
    return items


def clean_body(html_body):
    """Strip HTML and drop code blocks, leaving the question's prose."""
    soup = BeautifulSoup(html_body or "", "html.parser")
    for tag in soup(["pre", "code"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def has_user(item):
    owner = item.get("owner") or {}
    return owner.get("user_id") is not None and owner.get("user_type") != "does_not_exist"


def load_env():
    """Minimal .env reader (KEY=value lines). Real environment variables win.
    Looks in the current directory and next to this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (".env", os.path.join(here, ".env")):
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k.startswith("export "):
                    k = k[len("export "):].strip()
                os.environ.setdefault(k, v.strip().strip('"').strip("'"))


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="python")
    ap.add_argument("--max-questions", type=int, default=3000)
    ap.add_argument("--key", default=os.environ.get("SE_API_KEY"),
                    help="Stack Apps API key (or set SE_API_KEY)")
    ap.add_argument("--outdir", default="data")
    args = ap.parse_args()

    if not args.key:
        print("Warning: no API key found (set SE_API_KEY in .env or pass --key). "
              "Running without a key limits you to ~300 requests/day.")

    os.makedirs(os.path.join(args.outdir, "raw"), exist_ok=True)
    session = requests.Session()

    questions = fetch_questions(session, args.tag, args.max_questions, args.key)
    with open(os.path.join(args.outdir, "raw", "questions_raw.json"), "w") as f:
        json.dump(questions, f)

    answers = fetch_answers(session, [q["question_id"] for q in questions], args.key)
    with open(os.path.join(args.outdir, "raw", "answers_raw.json"), "w") as f:
        json.dump(answers, f)

    q_rows = [{
        "question_id": q["question_id"],
        "title": html.unescape(q.get("title", "")),
        "body_text": clean_body(q.get("body")),
        "asker_id": q["owner"]["user_id"],
        "asker_name": html.unescape(q["owner"].get("display_name", "")),
        "score": q.get("score"),
        "answer_count": q.get("answer_count"),
        "creation_date": q.get("creation_date"),
        "tags": ";".join(q.get("tags", [])),
    } for q in questions if has_user(q)]

    a_rows = [{
        "answer_id": a["answer_id"],
        "question_id": a["question_id"],
        "answerer_id": a["owner"]["user_id"],
        "answerer_name": html.unescape(a["owner"].get("display_name", "")),
        "score": a.get("score"),
        "is_accepted": a.get("is_accepted"),
    } for a in answers if has_user(a)]

    pd.DataFrame(q_rows).to_csv(os.path.join(args.outdir, "questions.csv"), index=False)
    pd.DataFrame(a_rows).to_csv(os.path.join(args.outdir, "answers.csv"), index=False)
    print(f"Saved {len(q_rows)} questions and {len(a_rows)} answers to {args.outdir}/")


if __name__ == "__main__":
    main()