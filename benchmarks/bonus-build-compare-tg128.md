# Bonus B1 - Prebuilt vs source build

Host `Windows-AMD64` · CPU `11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz`
Vector extensions detected: AVX-512, AVX2
llama.cpp `b10488` both sides · `threads=8` ·
**both pinned to `ngl=0`** so this isolates the compiler ·
metric `tg128`, 2 repetitions

> **Backend mismatch, handled.** The prebuilt binary sees
> `['Vulkan0: Intel(R) UHD Graphics (16243 MiB, 15475 MiB free)', 'Vulkan1: NVIDIA RTX A2000 Laptop GPU (3962 MiB, 3367 MiB free)']` and your source build sees `(no devices)`.
> Left at `-ngl 99` this comparison would have measured the accelerator and printed
> it under a compiler headline, so both sides were pinned to `-ngl 0`.

| Binary | Built for | tg128 (tok/s) | Relative |
|:--|--:|--:|--:|
| prebuilt release | runtime CPU dispatch | 32.7 | 1.00x |
| your source build | this CPU (`-DGGML_NATIVE=ON`) | 32.5 | 0.99x |

On this machine, **they are within 3% -- no meaningful difference**.

before: 32.7 tok/s (prebuilt release)
after:  32.5 tok/s (source build, -DGGML_NATIVE=ON)
speedup: 0.99x

Same source revision, same model, same backend, same `-ngl` -- the only difference
is what the compiler was allowed to assume about the CPU.
A gap this small usually means the prebuilt binary already dispatches to the right kernels at runtime (releases ship one libggml-cpu-*.so per microarchitecture and pick via CPUID), or that this workload is bandwidth-bound rather than instruction-bound. Both are real findings -- say which one you think it is.


## Explanation

The source build reached 32.5 tok/s versus 32.7 tok/s for the prebuilt release,
a 0.99x ratio that is well inside normal run-to-run noise. The i7-11800H exposes
AVX2 and AVX-512, but the release already ships multiple CPU kernels and selects
an appropriate implementation at runtime. Decode also streams the 0.5 GB weight
set repeatedly, so memory bandwidth matters more than generating a few more
specialized instructions. `GGML_NATIVE=ON` therefore had little unused CPU
capability to recover; the tiny prebuilt lead is not a meaningful regression.
