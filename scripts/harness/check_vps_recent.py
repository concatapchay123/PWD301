import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=10)

sql = "USE pwd301; SELECT l.id, l.title, l.markdown_content FROM lessons l WHERE l.title LIKE '%Chào hỏi%'"
cmd = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{sql}\""

_, o, e = ssh.exec_command(cmd)
print("OUT:")
print(o.read().decode())
print("ERR:")
print(e.read().decode())
ssh.close()
