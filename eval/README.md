# Eval Kit — Vietnamese Legal Compliance Agent

This directory contains scripts to measure real metrics for the project:

## Scripts

| Script | Measures | Prerequisites |
|--------|----------|---------------|
| `gen_test_set.py` | Generates 30 test queries from real DB data | PostgreSQL running |
| `eval_retrieval.py` | Hybrid vs Vector-only vs BM25-only accuracy (Hit@5) | PostgreSQL + Qdrant + BM25 index |
| `measure_latency.py` | Simple vs Complex query response latency | FastAPI backend running |
| `measure_ingestion.py` | Full pipeline throughput (parse → embed → BM25) | PostgreSQL + Qdrant running |

## Usage

```bash
# 1. Start infrastructure
docker compose up -d postgres qdrant redis

# 2. Activate venv
agent-legal\Scripts\activate

# 3. Generate test set (needs PostgreSQL with data)
python eval/gen_test_set.py

# 4. Run retrieval accuracy eval
python eval/eval_retrieval.py

# 5. Start API backend (separate terminal)
python api/main.py

# 6. Run latency measurement
python eval/measure_latency.py

# 7. Run ingestion benchmark (WARNING: deletes and re-ingests all data!)
python eval/measure_ingestion.py
```

## Output Format

```
Hybrid Search accuracy:  XX/30 (XX.X%)
Vector-only accuracy:    XX/30 (XX.X%)
BM25-only accuracy:      XX/30 (XX.X%)
Improvement: +XX.X percentage points

Simple query latency (n=15):  avg=X.XXs, min=X.XXs, max=X.XXs
Complex query latency (n=10): avg=X.XXs, min=X.XXs, max=X.XXs

Ingestion pipeline: 143 pages, 223 articles processed in XX.Xs
```
