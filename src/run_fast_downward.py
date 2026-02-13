"""
Ejecuta Fast Downward via Docker en paralelo con logging detallado.
Requiere: docker pull aibasel/downward:latest
"""

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DOMAINS_DIR = os.path.join(BASE_DIR, "domains")
TIMEOUT = 120  # 2 min per run (includes Docker overhead)

# "pre" args go BEFORE domain/problem, "post" args go AFTER
CONFIGS = {
    "FD-LAMA": {"pre": ["--alias", "lama-first"], "post": []},
    "FD-ASTAR-LM": {"pre": [], "post": ["--search", "astar(lmcut())"]},
    "FD-GBFS-FF": {"pre": [], "post": ["--search", "eager_greedy([ff()])"]},
}

PROBLEMS = {
    "blocksworld": {
        "domain": "blocksworld/domain.pddl",
        "instances": [
            ("BW-1", "blocksworld/instances/instance-4.pddl", 5),
            ("BW-2", "blocksworld/instances/instance-10.pddl", 7),
            ("BW-3", "blocksworld/instances/instance-17.pddl", 9),
            ("BW-4", "blocksworld/instances/instance-25.pddl", 12),
            ("BW-5", "blocksworld/instances/instance-35.pddl", 17),
        ],
    },
    "gripper": {
        "domain": "gripper/domain.pddl",
        "instances": [
            ("GR-1", "gripper/instances/instance-1.pddl", 4),
            ("GR-2", "gripper/instances/instance-4.pddl", 10),
            ("GR-3", "gripper/instances/instance-7.pddl", 16),
            ("GR-4", "gripper/instances/instance-10.pddl", 22),
            ("GR-5", "gripper/instances/instance-14.pddl", 30),
        ],
    },
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_single(domain_path, problem_path, fd_pre_args, fd_post_args, config_name, prob_id, domain_name, complexity):
    label = f"{config_name}/{prob_id}"
    log(f"START  {label} ({domain_name}, {complexity} objs)")

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{DOMAINS_DIR}:/data:ro",
        "--memory=4g",
        "aibasel/downward",
    ] + fd_pre_args + [
        f"/data/{domain_path}",
        f"/data/{problem_path}",
    ] + fd_post_args

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        elapsed = time.time() - start
        output = result.stdout + "\n" + result.stderr

        plan_length = nodes_expanded = nodes_generated = search_time = total_time = plan_cost = None
        solved = False

        for line in output.split("\n"):
            if "Solution found" in line:
                solved = True
            m = re.search(r"Plan length: (\d+)", line)
            if m: plan_length = int(m.group(1))
            m = re.search(r"Plan cost: (\d+)", line)
            if m: plan_cost = int(m.group(1))
            m = re.search(r"Expanded (\d+) state", line)
            if m: nodes_expanded = int(m.group(1))
            m = re.search(r"Generated (\d+) state", line)
            if m: nodes_generated = int(m.group(1))
            m = re.search(r"Search time: ([\d.]+)s", line)
            if m: search_time = float(m.group(1))
            m = re.search(r"Total time: ([\d.]+)s", line)
            if m: total_time = float(m.group(1))

        status = f"plan={plan_length}, cost={plan_cost}" if solved else "NO SOLUTION"
        log(f"DONE   {label} -> {status}, {elapsed:.2f}s, nodes={nodes_expanded}")

        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "solved": solved,
            "plan_length": plan_length, "plan_cost": plan_cost,
            "time": round(elapsed, 4), "search_time": search_time,
            "total_time_fd": total_time,
            "nodes_expanded": nodes_expanded, "nodes_generated": nodes_generated,
            "output": output[:2000],
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        log(f"TIMEOUT {label} after {elapsed:.1f}s")
        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "solved": False,
            "plan_length": None, "plan_cost": None,
            "time": round(elapsed, 4), "search_time": None, "total_time_fd": None,
            "nodes_expanded": None, "nodes_generated": None, "output": "TIMEOUT",
        }
    except Exception as e:
        elapsed = time.time() - start
        log(f"ERROR  {label}: {e}")
        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "solved": False,
            "plan_length": None, "plan_cost": None,
            "time": round(elapsed, 4), "search_time": None, "total_time_fd": None,
            "nodes_expanded": None, "nodes_generated": None, "output": f"ERROR: {e}",
        }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Quick Docker check
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True, timeout=10)
    except Exception:
        log("ERROR: Docker no disponible"); return

    jobs = []
    for dn, info in PROBLEMS.items():
        dp = info["domain"]
        for pid, pp, cx in info["instances"]:
            for cn, cfg in CONFIGS.items():
                jobs.append((dp, pp, cfg["pre"], cfg["post"], cn, pid, dn, cx))

    log(f"Lanzando {len(jobs)} ejecuciones con 4 workers (Docker)...")
    all_results = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(run_single, *j): j for j in jobs}
        for f in as_completed(futures):
            all_results.append(f.result())

    all_results.sort(key=lambda r: (r["domain"], r["problem"], r["planner"]))
    out = os.path.join(RESULTS_DIR, "fast_downward_results.json")
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)

    solved = sum(1 for r in all_results if r["solved"])
    log(f"\nRESUMEN: {solved}/{len(all_results)} resueltos")
    for r in all_results:
        s = "OK" if r["solved"] else "TIMEOUT/FAIL"
        log(f"  {r['planner']:15s} {r['problem']:5s} -> {s:12s} plan={str(r['plan_length']):>5s} t={r['time']:.2f}s nodes={r['nodes_expanded']}")
    log(f"Guardado en {out}")


if __name__ == "__main__":
    main()
