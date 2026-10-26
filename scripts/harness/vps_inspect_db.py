import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.28.33.20', port=22, username='root', password='Hoangphuc2006@##', timeout=15)

commands = [
    "cat /opt/apps/pwd301/deploy/compose.production.yml",
    "docker exec pwd301-production-db-1 /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"AdminStrongPassw0rd!\" -C -Q \"SELECT name FROM sys.databases;\" || docker exec pwd301-production-db-1 /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P \"AdminStrongPassw0rd!\" -C -Q \"SELECT name FROM sys.databases;\"",
    "grep -E '^(MSSQL_|DATABASE_|SA_PASSWORD)' /opt/apps/pwd301/.env /opt/apps/pwd301/.env.production 2>/dev/null",
]

for cmd in commands:
    print(f"=== $ {cmd} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(out)
    if err:
        print("[ERR]", err)

ssh.close()

