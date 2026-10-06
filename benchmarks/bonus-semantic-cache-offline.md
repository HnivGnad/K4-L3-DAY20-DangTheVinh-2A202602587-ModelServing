# Bonus C8/B5 â€” Semantic-cache logic (offline baseline)

Host: Windows 10, Intel Core i7-11800H. Command:

```powershell
.\.venv\Scripts\python.exe bonus\serving-regimes\semantic-cache-demo.py --offline --sweep
```

## Results

| Threshold | Hits | Requests | Hit rate |
|--:|--:|--:|--:|
| 0.70 | 3 | 8 | 37.5% |
| 0.80 | 3 | 8 | 37.5% |
| 0.85 | 3 | 8 | 37.5% |
| 0.90 | 3 | 8 | 37.5% |
| 0.95 | 3 | 8 | 37.5% |

At threshold 0.80, three cache hits avoided three simulated 250 ms LLM calls, or
approximately **750 ms** of decode work in this logic-only run.

## Finding

This is a control experiment, not evidence that 0.80 is a production-quality
threshold. The offline bag-of-words embedder produces almost exclusively cosine
similarities of 0 or 1, so the threshold curve is flat. It cannot expose the
overlap between paraphrases and unrelated prompts needed to diagnose false hits
and false misses. The useful result is architectural: a semantic-cache hit sits
above both prefix/KV caching and inference, so it eliminates prefill and decode;
however, cache keys and timing must be isolated or salted per tenant to avoid
cross-tenant leakage. A real embedding-server run is reported separately for the
serving-regime comparison.
