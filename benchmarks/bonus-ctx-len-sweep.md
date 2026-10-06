# Bonus - Context-length sweep (prefill cost)

Host `Windows-AMD64` · llama.cpp `b10488` ·
`threads=8` `ngl=99` · RAM 31.7 GB

| Prompt tokens | Prefill (tok/s) | TTFT contribution (ms) | vs linear scaling |
|:--|--:|--:|--:|
| 256 | 3604.3 | 71.0 | 1.00x |
| 1024 | 4080.5 | 251.0 | 0.88x |
| 2048 | 4071.9 | 503.0 | 0.89x |
| 4096 | 3788.9 | 1081.1 | 0.95x |

At 4096 tokens, prefill costs **1081 ms**, which is
**0.95x** linear scaling -- so on this hardware, over this range, prefill is
still growing **roughly linearly**, not quadratically.

That is the correct finding, not a failed experiment. Attention is O(N^2), but it is only
one term: the per-layer linear projections and MLP are O(N), and on a 2B-class model at
short prompts they dominate. The quadratic term only overtakes them once N gets large
enough. Your prefill cost is currently bounded by throughput, not by sequence length.

To find where it *does* bend, extend the grid:

```bash
.venv/bin/python bonus/sweeps/ctx-len-sweep.py --grid 1024,4096,8192,16384,32768
```

Watch the "vs linear" column: the first row that climbs meaningfully above 1.0 is where
attention starts to matter on your machine. Report that crossover point.

Either way, this is the number to remember when someone proposes stuffing more retrieved
context into a RAG prompt "because the context window allows it". Prefill is paid in full,
on every request, before the first token appears.

## Finding

No quadratic bend is visible through 4,096 tokens: the longest point costs
1,081.1 ms, only 0.95x the linear projection from 256 tokens. Prefill nevertheless
crosses one second at 4K, already comparable to the roughly one-second steady-state
completions observed after warm-up. For this small RAG pipeline I would therefore
budget retrieved context to about 2K tokens (503 ms prefill) unless recall testing
shows that the extra chunks justify doubling TTFT.
