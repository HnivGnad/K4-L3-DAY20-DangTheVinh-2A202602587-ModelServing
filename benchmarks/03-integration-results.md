# 03 - Integrate: RAG pipeline run

Host `Windows-AMD64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.2 | 36679.1 | 36679.3 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.2 | 3060.9 | 3061.4 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.2 | 3314.8 | 3315.1 |

Mean per stage (ms): embed **0.0** · retrieve **0.2** ·
llm **14351.6** · total **14351.9**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Based on the context provided, **Goodput** is more useful than raw throughput because it explicitly accounts for the **SLOs (Service Level Objects)** and **TPOT (Throughput at Saturation)** targets.

While raw throughput measures the total requests per second without regard for these constraints, Goodput filters for only the requests that met the TTFT (Throughput at Target) and TPOT targets. This 

**What problem does PagedAttention actually solve?**

> PagedAttention solves the problem of **internal fragmentation in GPU memory** by storing the KV cache in non-contiguous pages.

This is achieved by removing the internal fragmentation that would otherwise waste most of the GPU's memory capacity.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps when **prefill is compute-bound** and **decode is memory-bandwidth-bound**, as stated in the context. This separation allows the engine to utilize different resources for each phase: prefill can be optimized for CPU computation, while decode can be optimized for memory bandwidth.


## Integration reading

- N16 Cloud/IaC: stubbed (local process only).
- N17 Data pipeline: stubbed (the fixture corpus is loaded in-process).
- N18 Lakehouse: stubbed (no external table/storage engine).
- N19 Vector + features: stubbed (keyword-overlap retrieval, no vector database).
- N20 Serving: real `llama-server` HTTP endpoint.

The LLM stage dominates at 14,351.6 ms mean, effectively 100% of total latency;
embed and retrieve together stay below 1 ms. That is expected for an in-memory
toy retriever, although the first query was inflated by residual server work after
the load test. To halve latency I would attack serving first: use the tuned
four-thread setting, cap output length, and isolate/restart the serving replica
between load and latency-sensitive traffic. Optimizing the stub retrieval path
cannot materially change this total.
