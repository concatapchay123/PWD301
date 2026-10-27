import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.28.33.20', port=22, username='root', password='Hoangphuc2006@##', timeout=15)

cmd = """python3 -c "
with open('/opt/apps/pwd301/src/pwd301/__init__.py') as f:
    lines = f.readlines()
print(''.join(lines[374:395]))
" """
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print('[ERR]', err)
ssh.close()
