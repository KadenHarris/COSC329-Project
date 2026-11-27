# StackOverflow Knowledge Network

Builds and analyzes a knowledge network from StackOverflow for a single tag (e.g., Python).
- Nodes: users (sized by questions asked + answers given)
- Edges: answerer -> asker (weighted by number of questions answered)
- Analyzes in/out-degree centrality, HITS hub and authority scores, and a Bloom's taxonomy level for each question


### File Structure

| File/Folder | Feature (from plan) | Status | Description |
|---|---|---|---|
| `fetch_data.py` | 1. Data collection | Done | collects & cleans data from the Stack Exchange API |
| `build_graph.py` | 2. Original network | Done | constructs and draws the original network |
| `centrality.py` | 3. Centrality | Done | computes degree centrality & hub/authority scores |
| `classification.py` | 4. Bloom's classification | Done | computes Bloom's level for each question |
| `bloom_graphs.py` | 5. Bloom's graphs | Done (30 passing) | constructs and draws Bloom's graphs |
| `tests/` | 6. Testing | Done | automated unit tests |
| `data/` | | | `questions.csv`, `answers.csv`, `questions_bloom.csv` |
| `output/` | | | figures & tables produced by the files above |
| `requirements.txt` | | | dependencies |
| `pytest.ini` | | | test settings |

### Setup

An API key is required if you decide to run `fetch_data.py` on your own (however I provided pre-fetched data in the [releases section](https://github.com/KadenHarris/COSC329-Project/releases/tag/data) as well). Get a free API key at https://stackapps.com/apps/oauth/register and put it in a `.env` file at the project root as such: `SE_API_KEY=your_key_here`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Project

Run the scripts in this order from the project root, after completing the setup above.

```bash
# Collect data (skip this if you downloaded the data from the releases section)
python3 fetch_data.py --tag python --max-questions 3000

# Build the graph
python3 build_graph.py --top 20

# Calculate centrality measures
python3 centrality.py

# Question classification
python3 classification.py

# Bloom graphs
python3 bloom_graphs.py
```

| Scripts | Writes |
|---|---|
| `fetch_data.py` | `data/questions.csv`, `data/answers.csv` |
| `build_graph.py` | `output/original_graph.png`, `output/top_nodes.csv`, `output/top_edges.csv` |
| `centrality.py` | `output/centrality.csv` |
| `classify_questions.py` | `data/questions_bloom.csv` |
| `bloom_graphs.py` | `output/bloom_graph.png`, `output/bloom_levels.png`, `output/bloom_edges.csv` |


### Testing

```bash
python3 -m pytest
```

| Test | Description |
|---|---|
| `tests/test_fetch_data.py` | HTML and code blocks stripped, deleted users and unanswered questions are dropped, HTML entities (e.g., `&amp;`) decoded, CSVs written correctly |
| `tests/test_build_graph.py` | Edge weights count questions answered per pair, self-answers removed, activity = questions asked + answers given, user selection starts with the strongest pair and breaks ties by activity |
| `tests/test_centrality.py` | On a 4 user network, in/out-degree are the expected shares, hub & authority scores match values calculated by hand (0.618, 0.382) |
| `tests/test_classify.py` | 11 example titles get the expected Bloom's level, table words used as nouns (e.g. "the list") are ignored, verbs in verb positions are found, title takes priority over body |
| `tests/test_bloom_graphs.py` | User A answers 10 of B's questions (3 Remembering, 2 Analyzing, 5 Evaluating) giving 3 edges with thickness 3, 2 and 5, Unclassified questions are excluded |
| `tests/test_pipeline.py` | Runs every step in order on a 5 question dataset and checks all outputs are created and correct |


### Limitations

No known bugs present at the moment

- ~22% of questions don't match any rule, mostly because common words like "remove", "get", "check", and "split" are not in the ACM table (so these are excluded from the Bloom's graphs)
- "make" and "create" are counted as Creating and "convert" as Understanding, so some simple questions get a higher level than their difficulty really suggests
- Classification is rule based and not checked against hand labels, so the accuracy on real data is unknown
- Of the 20 users drawn, there is only 1 Analyzing answer and 0 Evaluating answers (so the Evaluating panel is empty)
- Data is sorted by most voted questions for the given tag instead of a random sample, so older more well known questions are favoured as well as longer standing answerers
- Most top users only ever ask or answer, so few pairs are connected in both directions

---

StackOverflow content is licensed under CC BY-SA. Data collected via the Stack Exchange API is attributed to StackOverflow and its contributors.
