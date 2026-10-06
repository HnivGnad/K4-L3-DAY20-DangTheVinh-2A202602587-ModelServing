# 02 - Continuous batching under load (u50)

Host `Windows-AMD64` · `--parallel 4` · 15 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 2.09 of 4 slots (52%) |
| `requests_processing` | 4 |
| `requests_deferred` | 0 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 275 |

Highest sampled value was **2.09 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` stayed at zero: every request found a free slot on arrival.

## Observation

The highest sampled decode width was 2.09 of four slots while
`requests_processing` reached four. The 50-user Locust run completed no requests
inside 60 seconds, so Little's-Law concurrency cannot be computed from completed
requests and appears as zero. I trust the server gauges for this run: they sample
work actually executing, whereas Locust's summary omits the requests still queued
or in flight when the fixed window closes.
