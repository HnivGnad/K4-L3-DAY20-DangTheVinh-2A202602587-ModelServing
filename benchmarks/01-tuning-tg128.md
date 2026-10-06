# 01 - Tune: thread-count sweep

Model `Qwen3.5-0.8B-Q4_K_M.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **8 physical · 16 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 95.3 | 99% |
| 4 | 96.3 | 100% |
| 8 | 85.2 | 88% |
| 16 | 87.1 | 90% |
| 32 | 91.0 | 95% |

**Best**: `-t 4` at 96.3 tok/s
**Slowest tested**: `-t 8` at 85.2 tok/s (1.13x spread)
**Against the physical-core default** (`-t 8`, 85.2 tok/s): 1.13x

Use this in your run:

```bash
LAB_N_THREADS=4 make bench
```

## Explanation

The knee is four threads (96.3 tok/s), below the eight physical cores. Moving to
eight threads falls to 85.2 tok/s, so the best setting is 1.13x faster than the
physical-core default. Most weights are already offloaded to Vulkan; CPU threads
mainly coordinate the remaining graph and submission work. Extra threads add
synchronization and contend for cache/memory bandwidth without exposing useful
parallel work, which explains the non-monotonic curve.
