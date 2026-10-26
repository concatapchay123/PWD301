# -*- coding: utf-8 -*-
import sys
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("103.28.33.20", 22, "root", "Hoangphuc2006@##", timeout=15)

sql = """
USE pwd301;
SELECT c.id, c.course_code, c.title, c.status,
       (SELECT COUNT(*) FROM learning_units lu WHERE lu.course_id = c.id) as units_count,
       (SELECT COUNT(*) FROM lessons l JOIN learning_units lu ON l.learning_unit_id = lu.id WHERE lu.course_id = c.id) as lessons_count,
       (SELECT COUNT(*) FROM assessments a WHERE a.course_id = c.id AND a.status = 'PUBLISHED') as published_assessments_count
FROM courses c;
"""
clean = " ".join(sql.split())
cmd = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{clean}\" -y 0"
_, stdout, _ = ssh.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace"))

# Check published assessments details for all courses
sql2 = """
USE pwd301;
SELECT a.id, a.course_id, c.course_code, a.title, a.assessment_type, a.status, a.passing_score
FROM assessments a
JOIN courses c ON a.course_id = c.id
WHERE a.status = 'PUBLISHED';
"""
clean2 = " ".join(sql2.split())
cmd2 = f"docker exec $(docker ps -q -f name=db) /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'AdminStrongPassw0rd!' -C -Q \"{clean2}\" -y 0"
_, stdout2, _ = ssh.exec_command(cmd2)
print("PUBLISHED ASSESSMENTS:")
print(stdout2.read().decode("utf-8", errors="replace"))

ssh.close()
