from pathlib import Path
import platform
import psutil
from datetime import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import re

from qiskit import QuantumCircuit, qasm2, transpile
from qiskit.circuit.library import SXGate
from qiskit.synthesis import OneQubitEulerDecomposer

from config import QMAP_OUTPUT, CIRCUIT_INPUT

from mqt.qmap.na.zoned import ZonedNeutralAtomArchitecture
from mqt.bench import get_benchmark, BenchmarkLevel

# Replaces u(0,0,y) gates with ry gates
def sanitize_naviz_file(naviz_path: Path | str) -> None:
    naviz_path = Path(naviz_path)
    content = naviz_path.read_text()

    # Matches: u <theta> 0.00000 0.00000 <target>
    # Replaces with: ry <theta> <target>
    pattern = r"\bu\s+([-\d\.]+)\s+0\.00000\s+0\.00000\s+(\S+)"
    updated_content = re.sub(pattern, r"ry \1 \2", content)

    naviz_path.write_text(updated_content)

def qmap_single_output(code: str, arch: ZonedNeutralAtomArchitecture) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M")
    RUN_DIR = QMAP_OUTPUT / f"benchmark_{timestamp}"
    RUN_DIR.mkdir(exist_ok=True)

    arch.to_namachine_file(str(RUN_DIR / "my_chip.namachine"))

    with open(RUN_DIR / "run.naviz", "w") as f:
        f.write(str(code))

    sanitize_naviz_file(RUN_DIR / "run.naviz")

# Initialises and writes base information of the batch
def init_markdown(dir_path: Path, batch_id: int, benchmarks: list[tuple[str, str, Path]], purpose: str):
    date = datetime.now().strftime("%d/%m/%Y")
    time = datetime.now().strftime("%H:%M")
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / "BENCHMARK_SPEC.md"

    system_info = {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
    }

    print("Initialising markdown...")
    markdown_content = f"""# Batch {batch_id}

## Summary
- Batch size: {len(benchmarks)}
- Date: {date}
- Time: {time}

## System Specifications
- **Operating System:** {system_info['os']}
- **Architecture:** {system_info['architecture']}
- **Total RAM:** {system_info['total_ram_gb']} GB

## Purpose
    {purpose}

## Batches
"""

    # 3. Write the content to the markdown file
    file_path.write_text(markdown_content)

#Appends information about each benchmark and its results.
def ap_markdown(dir_path: Path, bench_id: int, benchmark: tuple[str, str, Path], QMAP_RESULTS: float | int,
                QMAP_INITMAP_RESULTS: float | int, ZAP_RESULTS: float | int):
    file_path = dir_path / "BENCHMARK_SPEC.md"
    arch_name, circuit_name, _ = benchmark

    markdown_content = f"""### Benchmark {bench_id}

**Benchmark Specs:**
- Quantum architecture: {arch_name}
- Benchmark name: {circuit_name}

**Benchmark Results:**
- QMAP (IPS: Default) Results: {QMAP_RESULTS}
- QMAP (IPS: ZAP) Results: {QMAP_INITMAP_RESULTS}
- ZAP Results: {ZAP_RESULTS}
- QMAP / ZAP: {QMAP_RESULTS / ZAP_RESULTS}
"""

    with open(file_path, "a") as f:
        f.write(markdown_content)

#transpilers
def transpilation(qc: str | QuantumCircuit, output_path: Path, qc_name: str = "") -> None:
    custom_gates = [
        qasm2.CustomInstruction("sx", 0, 1, SXGate, builtin=True)
    ]

    if type(qc) == str:
        circuit = qasm2.load(str(CIRCUIT_INPUT / f"{qc}.qasm"), custom_instructions=custom_gates)
    else:
        circuit = qc

    intermediate_circuit = transpile(
        circuit,
        basis_gates=["u", "cz"],
        optimization_level=2
    )

    # 2. Decompose every 'u' directly into exact Rz - Ry - Rz rotations
    decomposer = OneQubitEulerDecomposer(basis="ZYZ")
    transpiled_circuit = QuantumCircuit(*intermediate_circuit.qregs, *intermediate_circuit.cregs)

    for instruction in intermediate_circuit.data:
        op = instruction.operation
        qubits = instruction.qubits
        clbits = instruction.clbits

        if op.name == "u":
            # Unrolls U(theta, phi, lambda) into explicit Rz and Ry gates
            decomp_qc = decomposer(op)
            transpiled_circuit.compose(decomp_qc, qubits=qubits, inplace=True)
        else:
            transpiled_circuit.append(op, qubits, clbits)

    transpiled_circuit = transpile(
        transpiled_circuit,
        basis_gates=["cz", "rz", "ry"],
        optimization_level=2
    )
    transpiled_circuit.remove_final_measurements(inplace=True)
    print("Gate counts:", transpiled_circuit.count_ops())

    if type(qc) == str:
        qc_name = qc

    qasm2.dump(transpiled_circuit, output_path / f"{qc_name}.qasm")

def batch_transpiler(benchmarks: dict[str, tuple[str, list[int]]]) -> None:

    for directory, (circuit, sizes) in benchmarks.items():
        for size in sizes:
            qc = get_benchmark(circuit, BenchmarkLevel.INDEP, size)
            circuit_label = f"{circuit}_n{size}"
            transpilation(qc, CIRCUIT_INPUT / directory, circuit_label)

def batch_translator(input: dict[str, tuple[str, list[int]]], arch_name: str) -> list[tuple[str, str, Path]]:

    output: list[tuple[str, str, Path]] = []
    for directory, (circuit, sizes) in input.items():
        for size in sizes:
            circuit_label = f"{circuit}_n{size}.qasm"
            output.append((arch_name, circuit_label, (CIRCUIT_INPUT / directory / circuit_label)))

    return output

def plotter(csv, output_path: Path):
    # Use the PGF backend
    mpl.use("pgf")
    mpl.rcParams.update(
        {
            "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "text.usetex": True,
            "pgf.rcfonts": False,
        }
    )

    for benchmark, rest in csv.groupby("benchmarks"):
        fig, ax = plt.subplots(figsize=(5.5, 3.5))

        for compiler, group in rest.groupby("compiler"):
            ax.plot(
                group["qubits"],
                group["fidelity"],
                marker="o",
                label=f"{benchmark} ({compiler})",
            )

        if benchmark == "qft" or benchmark == "multiplier" or benchmark == "qaoa":
            ax.set_yscale("log")

        ax.set_xlabel(r"Qubits ($x$)")
        ax.set_ylabel(r"Fidelity ($y$)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()

        filename = f"plot_{benchmark}.pgf".replace(" ", "_")
        fig.savefig(output_path / filename, bbox_inches="tight")

        plt.close(fig)