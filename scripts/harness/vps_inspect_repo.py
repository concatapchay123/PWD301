import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.28.33.20', port=22, username='root', password='Hoangphuc2006@##', timeout=15)

commands = [
    "cd /opt/apps/pwd301 && ls -la",
    "cd /opt/apps/pwd301 && git status",
    "cd /opt/apps/pwd301 && git remote -v",
    "cd /opt/apps/pwd301 && git log -n 3 --oneline",
    "cat /opt/apps/pwd301/.env | grep -v 'SECRET' | grep -v 'KEY' | grep -v 'PASSWORD'",
    "docker volume ls",
]

for cmd in commands:
    print(f"=== $ {cmd} ===")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("[ERR]", err)

ssh.close()
