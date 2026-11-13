import re

import pandas as pd

VERBS = {
    "Remembering": "define duplicate enumerate find identify label list locate memorize name recall recognize reference retrieve select state",
    "Understanding": "annotate classify comment convert demonstrate describe differentiate discuss exemplify explain infer interpret paraphrase report summarize translate",
    "Applying": "apply backup build calculate code compile compute configure connect decrypt deploy diagram document edit encrypt execute graph illustrate implement install investigate iterate manipulate map measure modify operate perform produce provision randomize recover restore schedule solve store train use virtualize write",
    "Analyzing": "analyze articulate attribute automate categorize compare contextualize contrast correlate decompose deconstruct deduce detect discriminate distinguish examine generalize integrate model monitor organize outline predict simulate structure trace translate update",
    "Evaluating": "adapt administer appraise argue assess choose critique debate debug decide defend estimate evaluate judge justify optimize prioritize prove support test validate value verify",
    "Creating": "assemble collaborate compose construct create design develop devise formulate generate hypothesize invent make plan program script secure visualize",
}

IRREGULAR = {
    "wrote": "write", "written": "write", "made": "make",
    "built": "build", "chose": "choose", "chosen": "choose",
}

PATTERNS = [
    (r"\b(best|better|fastest|most efficient|most pythonic|should i|pros and cons)\b", "Evaluating"),
    (r"\b(difference|differences|versus|vs)\b|\bwhy\b", "Analyzing"),
    (r"^how (does|is|are)\b", "Understanding"),
    (r"^(what|which)\b.*\b(is|are|does|do|means?)\b", "Understanding"),
]

CUES = {
    "to", "i", "we", "you", "they", "can", "could", "should", "would", "will",
    "must", "may", "might", "do", "does", "did", "cannot", "not", "just",
    "also", "then", "please", "don't", "doesn't", "didn't", "can't",
    "couldn't", "won't", "wouldn't", "shouldn't",
}


def forms(verb):
    stem = verb[:-1] if verb.endswith("e") else verb
    out = {verb, stem + "ing", verb + "ed", stem + "ed",
           verb + verb[-1] + "ing", verb + verb[-1] + "ed"}
    if verb.endswith("y"):
        out.add(verb[:-1] + "ied")
    return out


WORD_LEVEL = {}
for level, words in VERBS.items():
    for verb in words.split():
        for form in forms(verb):
            WORD_LEVEL.setdefault(form, level)
for form, verb in IRREGULAR.items():
    WORD_LEVEL.setdefault(form, next(l for l, w in VERBS.items() if verb in w.split()))


def first_sentences(text, n=3):
    return " ".join(re.split(r"(?<=[.?!])\s+", text)[:n])


def find_verb(text):
    words = re.findall(r"[a-z']+", text.lower())
    for i, word in enumerate(words):
        level = WORD_LEVEL.get(word)
        if level and (i == 0 or words[i - 1] in CUES or words[i - 1].endswith("ly")):
            return level, word
    return None


def classify(title, body):
    lowered = title.lower()
    for pattern, level in PATTERNS:
        m = re.search(pattern, lowered)
        if m:
            return level, m.group(0)
    for text in (title, first_sentences(body)):
        hit = find_verb(text)
        if hit:
            return hit
    if re.match(r"how\b", lowered):
        return "Applying", "how"
    return "Unclassified", ""


def main():
    q = pd.read_csv("data/questions.csv").fillna({"title": "", "body_text": ""})

    results = [classify(r.title, r.body_text) for r in q.itertuples()]
    q["bloom_level"] = [r[0] for r in results]
    q["matched"] = [r[1] for r in results]

    q[["question_id", "title", "bloom_level", "matched"]].to_csv(
        "data/questions_bloom.csv", index=False)
    print(q["bloom_level"].value_counts().to_string())


if __name__ == "__main__":
    main()