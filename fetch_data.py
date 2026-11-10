import argparse
import html
import os
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

API = "https://api.stackexchange.com/2.3"


def load_env():
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


def api_get(session, path, params, retries=5):
    for attempt in range(retries):
        resp = session.get(f"{API}{path}", params=params, timeout=30)
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code == 200:
            wait = data.get("backoff", 0)
            time.sleep(wait + 1 if wait else 0.15)
            if data.get("quota_remaining", 1) < 10:
                raise SystemExit("API quota nearly exhausted; try again tomorrow.")
            return data
        print(f"  HTTP {resp.status_code} {data.get('error_message', '')} "
              f"(attempt {attempt + 1}/{retries})")
        time.sleep(5 * (attempt + 1))
    raise SystemExit(f"Request failed after {retries} attempts: {path}")


def fetch_questions(session, tag, max_questions, key):
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
    soup = BeautifulSoup(html_body or "", "html.parser")
    for tag in soup(["pre", "code"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def has_user(item):
    owner = item.get("owner") or {}
    return owner.get("user_id") is not None and owner.get("user_type") != "does_not_exist"


def main():
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="python")
    ap.add_argument("--max-questions", type=int, default=3000)
    args = ap.parse_args()

    key = os.environ.get("SE_API_KEY")
    if not key:
        print("Warning: SE_API_KEY not found in .env; limited to ~300 requests/day.")

    os.makedirs("data", exist_ok=True)
    session = requests.Session()

    questions = fetch_questions(session, args.tag, args.max_questions, key)
    answers = fetch_answers(session, [q["question_id"] for q in questions], key)

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

    pd.DataFrame(q_rows).to_csv("data/questions.csv", index=False)
    pd.DataFrame(a_rows).to_csv("data/answers.csv", index=False)
    print(f"Saved {len(q_rows)} questions and {len(a_rows)} answers to data/")


if __name__ == "__main__":
    main()