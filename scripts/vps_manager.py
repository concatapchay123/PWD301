import os
import sys
import paramiko

VPS_HOST = os.getenv("VPS_HOST", "127.0.0.1")
VPS_PORT = int(os.getenv("VPS_PORT", "22"))
VPS_USER = os.getenv("VPS_USER", "root")
VPS_PASS = os.getenv("VPS_PASS", "")

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=VPS_HOST,
        port=VPS_PORT,
        username=VPS_USER,
        password=VPS_PASS,
        timeout=15,
        look_for_keys=False,
        allow_agent=False
    )
    return client

def test_connection():
    print(f"Connecting to {VPS_USER}@{VPS_HOST}:{VPS_PORT}...")
    client = get_ssh_client()
    print("[OK] SSH connection established successfully!\n")
    
    commands = [
        ("System Info", "uname -a"),
        ("OS Release", "cat /etc/os-release | grep PRETTY_NAME"),
        ("Uptime", "uptime"),
        ("CPU Info", "lscpu | grep 'Model name' | head -n 1"),
        ("Memory (RAM)", "free -h"),
        ("Disk Usage", "df -h /"),
        ("Active Docker Containers", "docker ps 2>/dev/null || echo 'Docker not running/installed'")
    ]
    
    for title, cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        print(f"--- {title} ---")
        if out:
            print(out)
        if err:
            print(f"[stderr]: {err}")
        print()
        
    client.close()
    print("[OK] Connection test completed.")

if __name__ == "__main__":
    test_connection()
