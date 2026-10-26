# -*- coding: utf-8 -*-
import sys
import re
import json
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=15)

sql = "USE pwd301; SELECT markdown_content FROM lessons WHERE id = 2;"
cmd = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{sql}\" -y 0"
_, stdout, stderr = ssh.exec_command(cmd)
text = stdout.read().decode("utf-8", errors="replace")

m = re.search(r"<!--\s*mini_quiz:\s*(.+?)\s*-->", text, re.DOTALL)
if m:
    try:
        parsed = json.loads(m.group(1))
        print("FOUND QUIZ JSON:")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except Exception as e:
        print("JSON parse error:", e)
        print("Raw text:", m.group(1)[:500])
else:
    print("NO mini_quiz found, checking text length:", len(text))
    pos = text.find("mini_quiz")
    if pos != -1:
        print("Substring around mini_quiz:", text[pos : pos + 1000])

ssh.close()
