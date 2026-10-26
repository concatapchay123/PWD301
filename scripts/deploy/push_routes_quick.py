# -*- coding: utf-8 -*-
import sys
import time
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=15)
sftp = ssh.open_sftp()
sftp.put("src/pwd301/blueprints/student/routes.py", "/opt/apps/pwd301/src/pwd301/blueprints/student/routes.py")
sftp.put("scripts/set_demo_vulnerable.py", "/opt/apps/pwd301/scripts/set_demo_vulnerable.py")
sftp.put("scripts/apply_defense_patch.py", "/opt/apps/pwd301/scripts/apply_defense_patch.py")
sftp.close()

_, o3, _ = ssh.exec_command("docker restart $(docker ps -q -f name=web)")
o3.read()
print("Web container restarted. Waiting 5s...")
time.sleep(5)
ssh.close()
print("Done!")
