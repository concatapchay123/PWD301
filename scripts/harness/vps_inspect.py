import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.28.33.20', port=22, username='root', password='Hoangphuc2006@##', timeout=15)

commands = [
    "pwd",
    "ls -la /root",
    "docker compose ls",
    "docker inspect pwd301-production-web-1 --format '{{.Config.Labels}}'",
    "docker inspect pwd301-production-web-1 --format '{{json .Mounts}}'",
    "find /root /opt /var -maxdepth 2 -name '*pwd*' -o -name '*PWD*' 2>/dev/null",
]

for cmd in commands:
    print(f"=== $ {cmd} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("[ERR]", err)

ssh.close()
