import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.28.33.20', port=22, username='root', password='Hoangphuc2006@##', timeout=15)

cmd = """docker exec -i pwd301-production-web-1 python << 'EOF'
from backend import create_app
from backend.extensions import db
from backend.models.identity import User
from backend.models.course import Course, Enrollment
from backend.models.wallet import UserBalance

app = create_app()
with app.app_context():
    print('=== PRODUCTION LIVE DATABASE STATS ===')
    print('Total Users in DB:', db.session.query(User).count())
    print('Total Courses in DB:', db.session.query(Course).count())
    print('Total Enrollments in DB:', db.session.query(Enrollment).count())
    print('Total User Balances in DB:', db.session.query(UserBalance).count())
    admin = db.session.query(User).filter(User.email == 'admin@backend.local').first()
    if admin:
        print(f'Admin Account: {admin.email} | Role: {admin.primary_role} | SubRole: {admin.admin_sub_role}')
    for c in db.session.query(Course).all():
        print(f'Course [{c.id}]: {c.title} | Price: {c.price} | TrailerAssetId: {c.trailer_file_asset_id}')
EOF
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print('[ERR]', err)
ssh.close()
