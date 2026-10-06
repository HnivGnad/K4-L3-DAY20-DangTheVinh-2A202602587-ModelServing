# Bonus C5 - Smallest useful quantization

Model `Qwen3.5 0.8B` - host `Windows-AMD64` - temperature 0 - 5 constrained prompts

| Quantization | Checks passed | Mean E2E (ms) |
|:--|--:|--:|
| Q4_K_M | 2/5 | 7018.7 |
| UD-Q2_K_XL | 2/5 | 13529.9 |

The checks use transparent substring/format assertions rather than an LLM judge.
They cover arithmetic, grounded extraction, translation, sorting, and strict
instruction following. This is a smoke-quality gate, not a broad quality benchmark.

## Observed outputs

- **Q4_K_M / arithmetic** (fail, 17998.1 ms): `331`
- **Q4_K_M / grounded fact** (fail, 16321.9 ms): `90`
- **Q4_K_M / translation** (pass, 232.7 ms): `Hello`
- **Q4_K_M / sorting** (fail, 300.1 ms): `1, 2, 3, 7`
- **Q4_K_M / instruction** (pass, 240.9 ms): `BLUE`
- **UD-Q2_K_XL / arithmetic** (pass, 47436.0 ms): `17 * 23 = 391`
- **UD-Q2_K_XL / grounded fact** (fail, 19360.1 ms): `90`
- **UD-Q2_K_XL / translation** (fail, 266.3 ms): echoed the Vietnamese source phrase
- **UD-Q2_K_XL / sorting** (fail, 344.7 ms): `1, 2, 3`
- **UD-Q2_K_XL / instruction** (pass, 242.6 ms): `BLUE`

## Finding

Both quantizations passed only 2/5 checks, confirming that this 0.8B model is not
reliable for strict arithmetic/formatting without validation. The observed lower-quant
failure requested by C5 is translation: Q4 returned `Hello`, while Q2 echoed the source
phrase; Q2 also dropped `11` entirely in sorting. Q4 has failures too, but it was twice
as fast on mean E2E here (7.0 s versus 13.5 s) and costs only 0.11 GB more. I would ship
Q4 under this RAM budget and place validators/retries around structured tasks.
