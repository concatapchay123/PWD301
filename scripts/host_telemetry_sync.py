"""Lightweight background telemetry synchronization agent for PWD301.

Measures host physical machine metrics (CPU, RAM, Disks, Network) on the host OS
and writes an atomic JSON snapshot to src/pwd301/.host_telemetry.json so that
Docker containers and web workers can instantly access true physical host telemetry.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print("psutil not installed in current environment. Please run: pip install psutil")
    sys.exit(1)


def collect_host_telemetry() -> dict[str, Any]:
    hostname = socket.gethostname()
    os_name = f"{platform.system()} {platform.release()}"
    mem = psutil.virtual_memory()
    total_ram_gb = round(mem.total / (1024**3), 1)
    used_ram_gb = round(mem.used / (1024**3), 1)
    avail_ram_gb = round(mem.available / (1024**3), 1)
    ram_pct = round(mem.percent, 1)

    cpu_pct = float(psutil.cpu_percent(interval=0.2))
    cpu_count = os.cpu_count() or 1
    freq = psutil.cpu_freq()
    freq_mhz = round(freq.current, 1) if freq and freq.current else None

    # Processor model on Windows
    cpu_model = ""
    if sys.platform == "win32":
        try:
            import winreg

            k = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            cpu_model = str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
        except Exception:
            cpu_model = platform.processor() or ""
    if not cpu_model:
        cpu_model = platform.processor() or f"{cpu_count} vCPU"

    # Disk usage
    drive = os.path.splitdrive(os.getcwd())[0] or "/"
    d_usage = psutil.disk_usage(drive)
    disk_total_gb = round(d_usage.total / (1024**3), 1)
    disk_used_gb = round(d_usage.used / (1024**3), 1)
    disk_free_gb = round(d_usage.free / (1024**3), 1)
    disk_pct = round(d_usage.percent, 1)

    net_io = psutil.net_io_counters()
    net_bytes_sent = net_io.bytes_sent if net_io else 0
    net_bytes_recv = net_io.bytes_recv if net_io else 0

    return {
        "hostname": hostname,
        "os": os_name,
        "cpu": {
            "percent": cpu_pct,
            "cores": cpu_count,
            "model": cpu_model,
            "frequency_mhz": freq_mhz,
        },
        "memory": {
            "total_gb": total_ram_gb,
            "used_gb": used_ram_gb,
            "available_gb": avail_ram_gb,
            "percent": ram_pct,
        },
        "disk": {
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "free_gb": disk_free_gb,
            "percent": disk_pct,
        },
        "network": {
            "bytes_sent": net_bytes_sent,
            "bytes_recv": net_bytes_recv,
        },
        "updated_at": time.time(),
    }


def write_snapshot(target_path: Path) -> None:
    data = collect_host_telemetry()
    temp_path = target_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, target_path)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    target_path = root / "src" / "pwd301" / ".host_telemetry.json"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    one_shot = "--once" in sys.argv
    print(f"Host telemetry sync targeting: {target_path}")

    if one_shot:
        write_snapshot(target_path)
        print("Updated host telemetry snapshot successfully.")
        return

    print("Running continuous host telemetry daemon (interval 5s)... Press Ctrl+C to stop.")
    while True:
        try:
            write_snapshot(target_path)
            time.sleep(5)
        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as exc:
            print(f"Error during sync: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    main()
