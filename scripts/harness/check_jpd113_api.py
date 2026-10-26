# -*- coding: utf-8 -*-
import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=15)

script_content = '''
from backend import create_app, db
from backend.models.course import Course
from backend.models.identity import User
from backend.services.course_service import get_student_course_detail

app = create_app()
with app.app_context():
    u = db.session.query(User).filter(User.email == 'tqtphamnguyenhoangphuc@gmail.com').first()
    c = db.session.query(Course).filter(Course.course_code == 'JPD113').first()
    detail = get_student_course_detail(actor=u, course_id=c.id, session=db.session)
    lus = detail.get('learning_units', [])
    print("JPD113 Learning Units:", len(lus))
    total_lessons = sum(len(lu.get('lessons', [])) for lu in lus)
    print("Total lessons in learning units:", total_lessons)
    for i, lu in enumerate(lus):
        print(f" Unit {i+1}: {lu.get('title')} ({len(lu.get('lessons', []))} lessons)")
        for l in lu.get('lessons', []):
            print(f"   - Lesson {l.get('id')}: {l.get('title')} (quiz: {bool(l.get('quiz'))})")
'''

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_jpd.py", "w") as f:
    f.write(script_content)
sftp.close()

cmd = "docker cp /tmp/test_jpd.py $(docker ps -q -f name=web):/app/test_jpd.py && docker exec $(docker ps -q -f name=web) python /app/test_jpd.py"
_, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))
print("STDERR:", stderr.read().decode("utf-8", errors="replace"))

ssh.close()
