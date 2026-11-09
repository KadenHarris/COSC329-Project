# StackOverflow Knowledge Network

Builds and analyzes a knowledge network from StackOverflow for a single tag.

### Setup

```bash
pip install -r requirements.txt
```

Get a free API key at https://stackapps.com/apps/oauth/register and put it in your `env` file.

```bash
# Collect data
python3 fetch_data.py --tag python --max-questions 3000
```
