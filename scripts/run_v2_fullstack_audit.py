"""Master Runner for PWD301 Real-Browser QA Campaign (80 Iterations).
Executes Block 1 through Block 8 against live Chromium browser,
saves all telemetry and evidence, and generates the 21 Master Deliverables.
Supports --start-iter N to resume seamlessly.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from scripts.qa_harness import (
    test_block_1,
    test_block_2,
    test_block_3,
    test_block_4,
    test_block_5,
    test_block_6,
    test_block_7,
    test_block_8,
)
from scripts.qa_harness.generate_master_deliverables import build_all_deliverables

BLOCKS = [
    ("Block 1: Discovery & Critical User Journeys", test_block_1, 1, 10),
    ("Block 2: Forms, Validation, CRUD & Persistence", test_block_2, 11, 20),
    ("Block 3: Business Workflows & Invariants", test_block_3, 21, 30),
    ("Block 4: Frontend Deep QA & UX Friction", test_block_4, 31, 40),
    ("Block 5: Backend, Integration & Data Integrity", test_block_5, 41, 50),
    ("Block 6: Security Boundaries & RBAC", test_block_6, 51, 60),
    ("Block 7: Concurrency, State & Reliability", test_block_7, 61, 70),
    ("Block 8: Deep Exploratory & Quality Audit", test_block_8, 71, 80),
]


def run_campaign(start_iter: int = 1):
    t_start = time.time()
    print("=" * 70, flush=True)
    print("STARTING PWD301 80-ITERATION REAL-BROWSER QA CAMPAIGN (V2)", flush=True)
    print("Zero Fake Testing Contract: Real Playwright Chromium Browser First", flush=True)
    print("Target Environment: http://127.0.0.1:5000", flush=True)
    print(f"Starting from Iteration: {start_iter:03d}", flush=True)
    print("=" * 70, flush=True)

    for block_name, mod, b_start_iter, b_end_iter in BLOCKS:
        if b_end_iter < start_iter:
            print(f">>> Skipping {block_name} (already completed prior to Iteration {start_iter:03d})", flush=True)
            continue

        b_start = time.time()
        print(f"\n>>> Running {block_name} (Iterations {b_start_iter:03d} - {b_end_iter:03d})...", flush=True)
        for i in range(b_start_iter, b_end_iter + 1):
            if i < start_iter:
                continue

            func_name = f"run_iter_{i:03d}"
            func = getattr(mod, func_name, None)
            if func:
                iter_t0 = time.time()
                for attempt in range(2):
                    try:
                        func()
                        print(f"  [+] {func_name} completed in {time.time() - iter_t0:.2f}s", flush=True)
                        break
                    except Exception as err:
                        if attempt == 0:
                            print(f"  [!] {func_name} failed with {err}. Retrying in 3s...", flush=True)
                            time.sleep(3)
                        else:
                            print(f"  [-] {func_name} failed on retry: {err}", flush=True)
                            raise
            else:
                print(f"  [-] Function {func_name} not found in {mod.__name__}", flush=True)
        print(f">>> {block_name} finished in {time.time() - b_start:.2f}s", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("GENERATING 21 MASTER DELIVERABLES IN qa-fullstack-audit/...", flush=True)
    build_all_deliverables()
    print("=" * 70, flush=True)
    print(f"ALL 80 ITERATIONS & 21 DELIVERABLES COMPLETED IN {time.time() - t_start:.2f}s", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-iter", type=int, default=1, help="Iteration number to start/resume from")
    args = parser.parse_args()
    run_campaign(start_iter=args.start_iter)
