# Tutorial 1: Your First Semantic Search

Welcome to RAG-Challenge. In this tutorial you will send your first
natural-language question to the system and understand every piece of the
response. By the end you will be comfortable querying match data from the
terminal and from the web UI.

## What you'll learn

- How the RAG (Retrieval-Augmented Generation) pipeline works
- How to query match data using natural language
- How to interpret search results and similarity scores

## Prerequisites

- Docker stack running (`docker compose up`)
- Seed data loaded (`make seed`)
- A terminal with `curl` available

## What is RAG?

RAG stands for **Retrieval-Augmented Generation**. Instead of asking an LLM to
answer from memory alone, we first *retrieve* the most relevant pieces of
context from a vector database, then feed those pieces into the LLM prompt so
it can ground its answer in real data.

The full pipeline looks like this:

```
Question → Embed → Vector Search → Top-K results → LLM prompt → Answer
```

Every match in the database is split into 15-second event buckets. Each bucket
has a short narrative summary that has been converted into a 1536-dimension
vector using OpenAI's `text-embedding-3-small` model. When you ask a question,
the system embeds your question with the same model and finds the closest
vectors using cosine distance.

## Step 1: Ask your first question

Open a terminal and run:

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who scored the goals in the match?",
    "match_id": 3943043,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 3
  }'
```

This queries the **Euro 2024 Final** (Spain 2-1 England). The system will
embed your question, search the match's event vectors, retrieve the three
closest results, and ask the LLM to generate an answer.

> Tip: pipe through `| python -m json.tool` (or `| jq .`) for pretty output.

## Step 2: Understand the response

The JSON response contains these key fields:

| Field | Description |
|-------|-------------|
| `answer` | LLM-generated response based on the retrieved context. |
| `question` | Your original query string. |
| `normalized_question` | The query translated to English (useful when you ask in other languages). |
| `search_results` | Array of the top-K matching events, ordered by relevance. |

Each entry inside `search_results` includes:

| Field | Description |
|-------|-------------|
| `event.summary` | The 15-second bucket narrative that matched your query. |
| `event.period` | Match period (1 = first half, 2 = second half, etc.). |
| `event.minute` | Minute of the match when the event occurred. |
| `similarity_score` | Cosine distance between query and event vectors. **Lower = more similar.** |
| `rank` | Ordering position (1 = best match). |

For the Euro 2024 Final you should see results mentioning Nico Williams
(47th minute) and Mikel Oyarzabal (86th minute), with similarity scores
around 0.55-0.60.

## Step 3: Try different questions

Each question type pulls different events from the vector store.

**Tactical question:**

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What defensive actions did each team execute?",
    "match_id": 3943043,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 5
  }'
```

**Factual question:**

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was the final scoreline?",
    "match_id": 3943043,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 3
  }'
```

**Statistical question:**

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which players had the most passes?",
    "match_id": 3943043,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 5
  }'
```

Notice how the similarity scores and retrieved events change depending on the
type of question. Tactical questions tend to surface defensive and pressing
events, while statistical ones pull passing summaries.

## Step 4: Change the match

Switch to the **2022 World Cup Final** (Argentina 3-3 France, penalties):

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who scored the goals?",
    "match_id": 3869685,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 5
  }'
```

This match went to extra time and penalties, so it contains more event
buckets than a standard 90-minute game. You should see results mentioning
Messi, Mbappe, and Di Maria across different periods.

## Step 5: Use the web UI

If you prefer a graphical interface:

1. Open **http://localhost:5173/chat** in your browser.
2. Select a match from the dropdown.
3. Type a question and press Enter.

In the **Mode** dropdown in the header you can switch to developer mode, which
shows similarity scores, the retrieved event summaries, and lets you choose
between search algorithms and embedding models.

## How it works under the hood

Here is what happens each time you submit a question:

1. **Normalize** -- If the question is not in English, it is translated first.
2. **Embed** -- The question is sent to OpenAI `text-embedding-3-small`,
   returning a 1536-dimension vector.
3. **Search** -- PostgreSQL with pgvector finds the top-K most similar event
   vectors using cosine distance (`<=>` operator).
4. **Context** -- The matched event summaries are assembled into an LLM prompt.
5. **Answer** -- The prompt is sent to `gpt-4o-mini`, which generates a
   grounded answer referencing only the retrieved context.

## What's next?

- **Tutorial 2:** Compare different search algorithms (cosine vs inner product)
- **Tutorial 3:** Understand how embeddings work

## Golden set

The file `data/golden_set.json` contains 12 pre-defined questions covering both
seed matches. Use it to benchmark the system after changes:

```bash
cat data/golden_set.json | python -m json.tool
```

Each entry includes the question, `match_id`, expected answer keywords, and
the search parameters used. This is useful for regression testing after you
modify prompts, switch models, or tune `top_n`.
