# MQT QMAP & ZAP Neutral-Atom Compilation Analysis

Benchmarking wrapper and utility scripts aiming at comparing zoned neutral-atom quantum compilation in **MQT QMAP** and
**ZAP** and custom initial placement heuristics (e.g. **COBRA** and **PairBlock**) developed for a B.Sc. Thesis at TUM.

## Repository Structure

```text
├── QMAP/               # Forked mqt-qmap submodule (C++/Python core)
├── ZAP/                # Forked neutral-atom-compilation submodule
├── input/              # Target architectures and benchmark circuit definitions
├── output/             # Generated batch results, CSV metrics, and .naviz traces
├── src/                # Python wrapper, translators, and benchmark runner
├── requirements.txt    # Pinned Python dependencies
├── setup.sh            # One-time environment and C++ submodule build script
└── run.sh              # Script to simplify the user execution experience
```

## Prerequisites

- Python 3.12 (tested) & uv
- C++20 compiler & CMake

## Setup

```bash
chmod +x setup.sh run.sh && ./setup.sh
```

## Usage

Due to the number of configuration parameters required, edit the `main()` function in
[`src/benchmarks.py`](src/benchmarks.py) directly to set your benchmarks, strategies, and batch ID, then run:

```bash
./run.sh
```

### main function:

This is a fully functional example of how to use the main function and those the whole wrapper with explanatory
comments:

```python
from mqt.qmap.na.zoned import InitialPlacementStrategy as IPS
from src import utils
from src.benchmarks import IpsParams, run_batch

# 1. Define benchmarks: {"output_subdir": ("mqt_bench_name", [qubit_counts])}
benchmarks = {
    "qaoa": ("qaoa", [10, 20, 30, 40, 50, 60, 70]),
    "qft": ("qft", [10, 20, 30, 40, 50, 60, 70]),
    "arith": ("multiplier", [8, 16, 32, 64]),
    "ghz": ("ghz", [10, 20, 30, 40, 50, 60, 70]),
    "graph": ("graphstate", [10, 20, 30, 40, 50, 60, 70]),
}

# 2. Define initial placement strategies to evaluate
ips_list = [
    IpsParams(),  # Default
    IpsParams(IPS.BasicPair),
]

# 3. (Optional) Generate and transpile missing circuits into native gates (RY, RZ, CZ)
# Note: Safe to always run: skips any circuit files that already exist.
utils.batch_transpiler(benchmarks)

# 4. Execute benchmark batch
run_batch(
    benchmarks_input=benchmarks,
    batch_id=0,
    ips_list=ips_list,
    architecture="qmap_default.json",  # optional | default: square_architecture.json
    purpose="First time trying to run this script."  # optional | default: (N/A)
)
```

## License

- **This repository (`src/`, `input/`):** [MIT License](LICENSE)
- **MQT QMAP (`QMAP/`):** Modified from [cda-tum/mqt-qmap](https://github.com/cda-tum/mqt-qmap) (MIT
  License)[[1]](#references)
- **ZAP (`ZAP/`):** Modified
  from [BAQIS-Quantum/neutral-atom-compilation](https://github.com/BAQIS-Quantum/neutral-atom-compilation) (MIT
  License)[[2]](#references)

Benchmarking wrapper comparing zoned neutral-atom quantum compilation in **MQT QMAP** [[1]](#references) and
**ZAP** [[2]](#references).

## References

1. Y. Stade, W.-H. Lin, J. Cong, and R. Wille, *"Routing-Aware Placement for Zoned Neutral Atom-based Quantum
   Computing,"* arXiv:2505.22715, 2025. [[arXiv]](https://arxiv.org/abs/2505.22715)
2. C. Huang et al., "ZAP: Zoned Architecture and Performant Compiler for Field-Programmable Atom Array,"
   doi: 10.1109/TQE.2026.3696707. [[ieeexplore]](https://ieeexplore.ieee.org/document/11535023)




