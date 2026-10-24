import json
from collections import defaultdict
import re
import math
import networkx as nx
import pandas as pd

#local files
from config import *
import utils
from ZAP.zap.zap import Zap

from mqt.qmap.na.zoned import ZonedNeutralAtomArchitecture, RoutingAwareCompiler, InitialPlacementStrategy
from mqt.core import load

#QMAP benchmark
def run_qmap(arch_path: Path, circuit_path: Path,
             initial_placement: InitialPlacementStrategy = InitialPlacementStrategy.Default) \
                -> (str, ZonedNeutralAtomArchitecture):
    arch = ZonedNeutralAtomArchitecture.from_json_file(str(arch_path))
    compiler = RoutingAwareCompiler(
        arch,
        initial_placement_strategy=initial_placement,
        warn_unsupported_gates=True)

    circ = load(circuit_path)
    code = compiler.compile(circ)

    return code, arch

# ZAP benchmark
def run_ZAP(arch_path: str, circuit_path: Path, output_path: Path) -> None:

    with open(str(arch_path), "r") as f:
        architecture = json.load(f)

    zap = Zap(
        benchmark=str(circuit_path),
        architecture=architecture,
        initial_mapping=[],
        output_dir=str(output_path),
        scheduling_strategy="asap_separate",
        placement_strategy="baseline",
        routing_strategy="baseline"
    )

    zap.solve(simulation=False,animation=False)

#ZAP output translation
def json_to_naviz_converter(input_path: Path, output_path: Path) -> None:

    with open(input_path, "r") as f:
        data = json.load(f)

    stages = data["stages"]["stage"]
    gate_lookup = data["gate_lookup"]
    lines = []

    stage_gate_lookups = {}

    for stage_id, stage in stages.items():
        stage_lookup = defaultdict(list)

        # Pair up each inner gate list with its corresponding index
        for gate_pair, idx in zip(stage["gates"], stage["idx"]):
            # Extract the single gate index from the duplicate list [g, g]
            gate_num = gate_pair[0]
            stage_lookup[gate_num].append(idx)

        stage_gate_lookups[stage_id] = stage_lookup

    print(f"test: {stage_gate_lookups.get("0")}")

    for inst in data["instructions"]:
        match inst["type"]:
            case "Init":
                for loc in inst["locs"]:
                    lines.append(f"atom ({loc['x']}, {loc['y']}) atom{loc['id']}\n")
            case "Activate":
                for q_idx in inst["qs"]:
                    lines.append(f"@+ load atom{q_idx}\n")
            case "BigMove" | "Park":
                for q_idx, loc in zip(inst["qs"], inst["locs"]):
                    lines.append(f"@+ move ({loc['x_end']}, {loc['y_end']}) atom{q_idx}\n")
            case "Deactivate":
                for q_idx in inst["qs"]:
                    lines.append(f"@+ store atom{q_idx}\n")
            case "1qGate":
                gate_id_lookup = stage_gate_lookups.get(str(inst["stage"]))
                gate_id_count = defaultdict(int)
                for q_idx, gate_idx in zip(inst["qs"], inst["gates"]):
                    count = gate_id_count[gate_idx]
                    gate_id_count[gate_idx] += 1
                    gate_id = gate_id_lookup[gate_idx][count]
                    gate = gate_lookup[str(gate_id)]["name"]
                    angle = gate_lookup[str(gate_id)]["params"][0]
                    lines.append(f"@+ {gate} {angle:.5f} atom{q_idx}\n")
            case "2qGate":
                lines.append(f"@+ cz zone_cz0\n")
            case "Crosstalk":
                pass
            case unknown:
                raise ValueError(f"Unsupported instruction type: {unknown}")

    with open(output_path, "w") as f:
        f.writelines(lines)

#Helper functions for simulation
def read_multi_line(data):
    lines = []
    for line in data:
        if line.strip() == "]":
            break
        lines.append(line)
    return lines

def zone_check(arch: dict, qubit_id: int, coords: tuple, zone_set: set):
    _, y = coords
    _, y2 = arch["entanglement_zones"][0]["offset"]

    if y >= int(y2):
        zone_set.add(qubit_id)
    else:
        zone_set.discard(qubit_id)

def cz_pairs(ids: set, locs: dict):
    coord_maps = defaultdict(dict)

    for q_id in ids:
        x, y = locs[q_id]
        coord_maps[y][x] = q_id

    for y in coord_maps:
        coord_maps[y] = dict(sorted(coord_maps[y].items()))

    pairs = []
    singles = []
    for coord_map in coord_maps.values():
        items = list(coord_map.items())
        i = 0
        n = len(items)

        while i < n:
            x1, id1 = items[i]

            if i + 1 < n:
                x2, id2 = items[i + 1]
                if (x2 - x1) <= 4:
                    pairs.append((id1, id2))
                    i += 2
                    continue

            singles.append(id1)
            i += 1

    return pairs, singles

def simulation(arch_path: Path, input_path: Path, output_path: Path, csv_data) -> float | int:

    qubit_count = 0
    gate1_count = 0
    gate2_count = 0
    zone_count = 0
    tran_count = 0
    talk_count = 0
    total_time = 0
    active_time = defaultdict(float)
    qubit_loc = {}
    ent_zone = set()

    with open(arch_path, "r") as f:
        arch = json.load(f)

    clean_chars = str.maketrans("", "", "(),\n@+")

    with open(input_path, "r") as data:
        for line in data:
            cleaned_line = line.translate(clean_chars).strip()

            if not cleaned_line:
                continue

            cmd, *args = cleaned_line.split()

            match cmd:
                case "atom":
                    qubit_count += 1
                    x, y, id = args
                    id = int(re.sub("atom", "", id))

                    qubit_loc[id] = (float(x), float(y))
                case "ry" | "rz":
                    gate1_count += 1
                    _, id = args
                    id = int(re.sub("atom", "", id))

                    active_time[id] += t_1
                    total_time += t_1
                case "cz":
                    zone_count += 1
                    tmp_gate_count = 0

                    pairs, singles = cz_pairs(ent_zone, qubit_loc)

                    for id in singles:
                        active_time[id] += t_2
                        talk_count += 1
                    for id1, id2 in pairs:
                        active_time[id1] += t_2
                        active_time[id2] += t_2
                        tmp_gate_count += 1
                    gate2_count += tmp_gate_count/2
                    total_time += t_2
                case "load" | "store":
                    if args[0] == "[":
                        ids = []
                        for subline in read_multi_line(data):
                            id = subline.translate(clean_chars).strip()
                            id = int(re.sub("atom", "", id))
                            ids.append(id)

                        tran_count += 1
                        for id in ids:
                            active_time[id] += t_t
                        total_time += t_t
                    else:
                        id = int(re.sub("atom", "", args[0]))

                        tran_count += 1
                        active_time[id] += t_t
                        total_time += t_t
                case "move":
                    if args[0] == "[":
                        ids = []
                        maxtime = 0
                        for subline in read_multi_line(data):
                            cleaned_subline = subline.translate(clean_chars).strip()
                            x, y, id = cleaned_subline.split()
                            id = int(re.sub("atom", "", id))
                            ids.append(id)

                            coord = (float(x), float(y))
                            dist = math.dist(qubit_loc[id], coord)
                            qubit_loc[id] = coord

                            time = 2 * math.sqrt(dist / ACC)
                            maxtime = time if time > maxtime else maxtime

                            zone_check(arch, id, coord, ent_zone)

                        for id in ids:
                            active_time[id] += maxtime
                        total_time += maxtime

                    else:
                        x, y, id = args
                        id = int(re.sub("atom", "", id))

                        coord = (float(x), float(y))
                        dist = math.dist(qubit_loc[id], coord)
                        qubit_loc[id] = coord
                        zone_check(arch, id, coord, ent_zone)

                        time = 2 * math.sqrt(dist / ACC)

                        active_time[id] += time
                        total_time += time
                case _:
                    pass

        tmp = 1
        for _, time in active_time.items():
            tmp *= math.exp(- time / 1500000) # 1.5s straight out of ZAP paper T2
        print(f"f1: {FIDEL_Q1}, g1c: {gate1_count}, f2: {FIDEL_Q2}, g2c: {gate2_count}, ftr: {FIDEL_TRAN},"
              f" fta: {FIDEL_TALK}, tac: {talk_count} , trc: {tran_count}, tmp: {tmp}")

        fidel = FIDEL_Q1**gate1_count * FIDEL_Q2**gate2_count * FIDEL_TALK**talk_count * FIDEL_TRAN**tran_count * tmp
        csv_data["fidelity"].append(fidel)
        csv_data["1QGC"].append(gate1_count)
        csv_data["2QGC"].append(gate2_count)
        csv_data["transitions"].append(tran_count)

        return fidel

#Batch functions
def run_batch(benchmarks: list[tuple[str, str, Path]], batch_id: int, purpose: str = "N/A"):

    #Create Batch directory
    BATCH_DIR = WORKSPACE_ROOT / "batches" / f"batch_{batch_id}"
    bench_id = 0
    csv_data: dict[str, list[float | int | str]] = defaultdict(list)

    utils.init_markdown(BATCH_DIR, batch_id, benchmarks, purpose)

    for benchmark in benchmarks:
        arch_name, circuit_name, circuit_path = benchmark
        arch_path = ARCH_INPUT / arch_name
        print(f"running benchmark: {circuit_name}")

        BENCH_DIR = BATCH_DIR / f"benchmark_{bench_id}"

        BENCH_DIR.mkdir(exist_ok=True)

        print("---running QMAP (IPS: Default) ---")
        code, arch = run_qmap(arch_path, circuit_path)
        arch.to_namachine_file(str(BENCH_DIR / "architecture.namachine"))
        with open(BENCH_DIR / "QMAP.naviz", "w") as f:
            f.write(str(code))
        utils.sanitize_naviz_file(BENCH_DIR / "QMAP.naviz")

        print("---running QMAP (IPS: ZAP) ---")
        code, arch = run_qmap(arch_path, circuit_path, InitialPlacementStrategy.ZAP)
        with open(BENCH_DIR / "QMAP_InitMap.naviz", "w") as f:
            f.write(str(code))
        utils.sanitize_naviz_file(BENCH_DIR / "QMAP_InitMap.naviz")

        print("---running ZAP---")
        run_ZAP(arch_path, circuit_path, BENCH_DIR / "ZAP")
        json_filename = Path(circuit_name).with_stem(Path(circuit_name).stem + "_code").with_suffix(".json")
        INPUT_TMP = BENCH_DIR / "ZAP" / "code" / json_filename
        json_to_naviz_converter(INPUT_TMP, BENCH_DIR / "ZAP.naviz")

        print("Initiating simulations...")

        tokens = re.split(r"[_.]", circuit_name)

        print(tokens)

        bench = tokens[0]
        qubits = tokens[1].replace("n", "")

        for i in range(3):
            csv_data["benchmarks"].append(bench)
            csv_data["qubits"].append(qubits)

        csv_data["compiler"].append("QMAP")
        QMAP_RESULTS = simulation(arch_path, BENCH_DIR / "QMAP.naviz", BENCH_DIR, csv_data)
        csv_data["compiler"].append("QMAP ZAPMAP")
        QMAP_INITMAP_RESULTS = simulation(arch_path, BENCH_DIR / "QMAP_InitMap.naviz", BENCH_DIR, csv_data)
        csv_data["compiler"].append("ZAP")
        ZAP_RESULTS = simulation(arch_path, BENCH_DIR / "ZAP.naviz", BENCH_DIR, csv_data)
        utils.ap_markdown(BATCH_DIR, bench_id, benchmark, QMAP_RESULTS, QMAP_INITMAP_RESULTS , ZAP_RESULTS)

        df = pd.DataFrame(csv_data)
        df.to_csv(BATCH_DIR / "data.csv", index=False)
        Path(BATCH_DIR / "plots").mkdir(parents=True, exist_ok=True)
        utils.plotter(df, BATCH_DIR / "plots")

        bench_id += 1

def main():
    benchmarks = {
        "qaoa": ("qaoa", [10, 20, 30, 40, 50]),
    }

    benchmarks2 = {
        "qft": ("qft", [10, 20, 30, 40, 50]),
        "graph": ("graphstate", [60, 70, 80, 90, 100]),
    }

    tmp = {"qft": ("qft", [10, 20])}

    #utils.batch_transpiler(benchmarks)
    benchmark_list = utils.batch_translator(benchmarks, "square_architecture.json")
    run_batch(benchmark_list, 9, "testing csv")


if __name__ == "__main__":
    main()