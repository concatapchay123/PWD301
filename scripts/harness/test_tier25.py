import sys
sys.path.insert(0, '.')
import time
import threading
from scripts.benchmark_engine import BenchmarkHarness, BenchmarkClient

harness = BenchmarkHarness()
concurrency = 25
clients = []
for i in range(concurrency):
    email = f"student{(i % 4) + 1}@backend.local"
    token = harness.token_pool.get(email)
    c = BenchmarkClient(i, harness.base_url, token=token)
    clients.append(c)

results = []
stop_event = threading.Event()
threads = []
for c in clients:
    t = threading.Thread(target=harness.run_user_journey, args=(c, stop_event, results))
    threads.append(t)
    t.start()

time.sleep(2.0)
stop_event.set()
for t in threads:
    t.join()

failed = [r for r in results if not r.is_success]
print(f"Total: {len(results)}, Failed: {len(failed)}")
status_counts = {}
for r in failed:
    status_counts[r.status_code] = status_counts.get(r.status_code, 0) + 1

print("Failed status codes:", status_counts)
if failed:
    sample = failed[0]
    print(f"Sample failed: {sample.scenario} status={sample.status_code} error={sample.error}")
