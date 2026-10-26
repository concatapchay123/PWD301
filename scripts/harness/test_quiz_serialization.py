# -*- coding: utf-8 -*-
import sys
import json
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=15)

script_content = '''
import json
from backend import create_app, db
from backend.models.course import Lesson, Course
from backend.models.identity import User
from backend.blueprints.student.routes import _serialize_student_lesson, _is_pacing_defense_active

app = create_app()
with app.app_context():
    u = db.session.query(User).filter(User.email == 'tqtphamnguyenhoangphuc@gmail.com').first()
    l = db.session.query(Lesson).filter(Lesson.id == 2).first()
    print("Is pacing defense active?:", _is_pacing_defense_active())
    serialized = _serialize_student_lesson(l, None)
    quiz = serialized.get("quiz", [])
    print(f"Quiz questions count: {len(quiz)}")
    for i, q in enumerate(quiz):
        print(f"--- Question {i+1} ---")
        print("Type:", q.get("type"))
        print("Question:", q.get("question"))
        print("options:", q.get("options"))
        print("correct_index:", q.get("correct_index"))
        print("blank_answer:", q.get("blank_answer"))
        print("pairs:", q.get("pairs"))
        print("left_options:", q.get("left_options"))
'''

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_quiz_serialize.py", "w") as f:
    f.write(script_content)
sftp.close()

cmd = "docker cp /tmp/test_quiz_serialize.py $(docker ps -q -f name=web):/app/test_quiz_serialize.py && docker exec $(docker ps -q -f name=web) python /app/test_quiz_serialize.py"
_, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))
print("STDERR:", stderr.read().decode("utf-8", errors="replace"))

ssh.close()
