# 02 - Serve: load test + saturation reading

Host `Windows-AMD64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=8` ·
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 4 | 0.14 | 29000 | 29000 | 29000 | 3.9 | 0.0% |
| 50 | 0 | 0.00 | 0 | 0 | 0 | 0.0 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **0.00x** (0% of linear) |
| P95 latency | **0.00x** |
| Effective concurrency at 50 users | 0.0 vs `--parallel 4` slots (occupancy/slot ratio 0.00) |

**Saturated.** Throughput stopped scaling (0.00x delivered for 5x offered, 0% of linear) even though effective concurrency (0.0) sits below 4 slots. Something other than decode-slot count is the limit -- look at memory bandwidth, or context/KV pressure.

P95 grew no faster than throughput (0.00x vs 0.00x), so this server still has headroom at 50 users.

> **Small sample.** Only 0 requests completed in the
> shorter run, so these percentiles are indicative rather than solid. Note also that
> locust averages only *completed* requests: when the run ends with requests still
> queued, effective concurrency is an **under**-estimate. Trust the throughput-scaling
> row over the concurrency row here, and run longer (`-t 3m`) if you want firmer numbers.

## Reading

The server is already at its practical limit by ten users: 0.14 RPS with 29 s P95
gives 3.9 effective concurrent requests, essentially all four configured slots.
At 50 users, no request completed before the 60-second cutoff even though the
Prometheus trace showed four requests processing and a peak average decode width
of 2.09. Thus the zero P95/RPS row is censored data, not headroom: completion
latency exceeded the test window and queued/in-flight work is absent from Locust's
completed-request statistics.

I would first reduce per-request decode work (a smaller output cap or stricter SLO
budget) before increasing `--parallel`: the existing slots are occupied and more
concurrent decodes would further divide limited memory bandwidth. For capacity,
replicating the server is safer than deepening the queue on this GPU.
