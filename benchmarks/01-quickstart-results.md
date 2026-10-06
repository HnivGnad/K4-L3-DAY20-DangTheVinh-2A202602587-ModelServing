# 01 - Measure: latency baseline

Model `Qwen3.5 0.8B` · host `Windows-AMD64` · llama.cpp `b10488`
Settings: `threads=8` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `Q4_K_M` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 17638 | 300 / 361 | 13.3 / 14.3 | 1090 / 1249 / 1249 | 74.9 |
| UD-Q2_K_XL | 0.39 | 25002 | 247 / 309 | 13.7 / 14.7 | 1110 / 1200 / 1200 | 73.2 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.02x SLOWER** than `Q4_K_M` here, despite being 0.11 GB smaller. That is a real result, not a mistake: fewer bits only buys speed when decode is limited by memory bandwidth. On a machine that is compute-limited instead — few cores, no GPU offload — the extra dequantization work of a heavily-quantized format can cost more than the bytes it saves. Say which case yours is.

## Observation

`UD-Q2_K_XL` saves 0.11 GB (22%) but is not a speed win here: median decode is
73.2 tok/s versus 74.9 tok/s for `Q4_K_M`, and its cold start is 7.4 seconds
slower. This points to dequantization/compute overhead rather than weight bandwidth
as the current limit. The C5 five-prompt quality gate is reported separately; the
small memory saving is not enough to justify choosing Q2 as the default.
