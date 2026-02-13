"""
Ejecuta pyperplan en paralelo con timeouts agresivos y logging detallado.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DOMAINS_DIR = os.path.join(BASE_DIR, "domains")
TIMEOUT = 60  # 60s per run — plenty for pyperplan

CONFIGS = {
    "PP-ASTAR-FF": {"search": "astar", "heuristic": "hff"},
    "PP-GBF-FF": {"search": "gbf", "heuristic": "hff"},
    "PP-ASTAR-ADD": {"search": "astar", "heuristic": "hadd"},
}

PROBLEMS = {
    "blocksworld": {
        "domain": os.path.join(DOMAINS_DIR, "blocksworld", "domain.pddl"),
        "instances": [
            ("BW-1", "instance-4.pddl", 5),
            ("BW-2", "instance-10.pddl", 7),
            ("BW-3", "instance-17.pddl", 9),
            ("BW-4", "instance-25.pddl", 12),
            ("BW-5", "instance-35.pddl", 17),
        ],
    },
    "gripper": {
        "domain": os.path.join(DOMAINS_DIR, "gripper", "domain.pddl"),
        "instances": [
            ("GR-1", "instance-1.pddl", 4),
            ("GR-2", "instance-4.pddl", 10),
            ("GR-3", "instance-7.pddl", 16),
            ("GR-4", "instance-10.pddl", 22),
            ("GR-5", "instance-14.pddl", 30),
        ],
    },
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_single(domain_file, problem_file, search, heuristic, config_name, prob_id, domain_name, complexity):
    """Run one pyperplan configuration on one problem."""
    label = f"{config_name}/{prob_id}"
    log(f"START  {label} ({domain_name}, {complexity} objs, {search}+{heuristic})")

    # Copy files to temp dir to avoid .soln race conditions between parallel runs
    tmpdir = tempfile.mkdtemp(prefix=f"pp_{config_name}_{prob_id}_")
    tmp_domain = os.path.join(tmpdir, "domain.pddl")
    tmp_problem = os.path.join(tmpdir, "problem.pddl")
    shutil.copy2(domain_file, tmp_domain)
    shutil.copy2(problem_file, tmp_problem)

    cmd = [
        sys.executable, "-m", "pyperplan",
        "-s", search,
        "-H", heuristic,
        tmp_domain,
        tmp_problem,
    ]

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        elapsed = time.time() - start
        output = result.stdout + "\n" + result.stderr

        # Read plan file from temp dir
        plan_file = tmp_problem + ".soln"
        plan_length = None
        plan_actions = []
        if os.path.exists(plan_file):
            with open(plan_file) as f:
                plan_actions = [l.strip() for l in f if l.strip()]
            plan_length = len(plan_actions)

        # Parse nodes from output
        nodes_expanded = None
        for line in output.split("\n"):
            if "expanded" in line.lower():
                nums = [int(w) for w in line.split() if w.isdigit()]
                if nums:
                    nodes_expanded = nums[0]

        status = f"plan={plan_length}" if plan_length else "NO PLAN"
        log(f"DONE   {label} -> {status}, {elapsed:.2f}s, nodes={nodes_expanded}")
        shutil.rmtree(tmpdir, ignore_errors=True)

        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "search": search, "heuristic": heuristic,
            "solved": plan_length is not None, "plan_length": plan_length,
            "time": round(elapsed, 4), "nodes_expanded": nodes_expanded,
            "output": output[:1500], "plan_actions": plan_actions[:5],
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        log(f"TIMEOUT {label} after {elapsed:.1f}s")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "search": search, "heuristic": heuristic,
            "solved": False, "plan_length": None,
            "time": round(elapsed, 4), "nodes_expanded": None,
            "output": "TIMEOUT", "plan_actions": [],
        }
    except Exception as e:
        elapsed = time.time() - start
        log(f"ERROR  {label}: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {
            "planner": config_name, "domain": domain_name, "problem": prob_id,
            "complexity": complexity, "search": search, "heuristic": heuristic,
            "solved": False, "plan_length": None,
            "time": round(elapsed, 4), "nodes_expanded": None,
            "output": f"ERROR: {e}", "plan_actions": [],
        }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Build all jobs
    jobs = []
    for domain_name, info in PROBLEMS.items():
        domain_file = info["domain"]
        for prob_id, inst_file, complexity in info["instances"]:
            problem_file = os.path.join(DOMAINS_DIR, domain_name, "instances", inst_file)
            for config_name, cfg in CONFIGS.items():
                jobs.append((domain_file, problem_file, cfg["search"], cfg["heuristic"],
                             config_name, prob_id, domain_name, complexity))

    log(f"Lanzando {len(jobs)} ejecuciones en paralelo (max 6 workers)...")
    all_results = []

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(run_single, *job): job for job in jobs}
        for future in as_completed(futures):
            all_results.append(future.result())

    # Sort for consistent output
    all_results.sort(key=lambda r: (r["domain"], r["problem"], r["planner"]))

    output_file = os.path.join(RESULTS_DIR, "pyperplan_results.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    # Quick summary
    solved = sum(1 for r in all_results if r["solved"])
    log(f"\nRESUMEN: {solved}/{len(all_results)} resueltos")
    for r in all_results:
        s = "OK" if r["solved"] else "TIMEOUT/FAIL"
        log(f"  {r['planner']:15s} {r['problem']:5s} -> {s:7s} plan={str(r['plan_length']):>5s} t={r['time']:.2f}s")
    log(f"Guardado en {output_file}")


if __name__ == "__main__":
    main()
