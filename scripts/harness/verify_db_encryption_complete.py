import sys
sys.path.insert(0, "src")
from backend import create_app
from backend.extensions import db
from backend.models.identity import User
from backend.services.user_service import get_user_by_email, verify_password

app = create_app("development")
with app.app_context():
    # 1. Test get_user_by_email for admin
    user = get_user_by_email("admin@backend.local")
    assert user is not None, "admin@backend.local not found!"
    sys.stdout.buffer.write(f"Loaded User ID {user.id}:\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  email:        {user.email}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  display_name: {user.display_name}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  password_hash starts with: {user.password_hash[:25]}\n".encode("utf-8"))
    
    # Verify values in memory are decrypted plaintext
    assert user.email == "admin@backend.local"
    assert user.display_name == "Administrator"
    
    # 2. Test get_user_by_email for student
    student = get_user_by_email("student1@backend.local")
    assert student is not None, "student1@backend.local not found!"
    sys.stdout.buffer.write(f"Loaded Student ID {student.id}:\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  email:        {student.email}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  display_name: {student.display_name}\n".encode("utf-8"))
    assert student.email == "student1@backend.local"
    assert "Nguyễn Văn An" in student.display_name
    
    # 3. Test verify_password
    valid = verify_password(admin_user := user, "Admin@123456")
    sys.stdout.buffer.write(f"Admin password verify: {valid}\n".encode("utf-8"))
    
    # 4. Check raw database values (to verify they are encrypted at-rest)
    raw = db.session.execute(db.text("SELECT email, password_hash, display_name FROM users WHERE id = :id"), {"id": user.id}).fetchone()
    sys.stdout.buffer.write("\nRaw DB Row (DBeaver inspection):\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  email in DB:        {raw[0]}\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  password in DB:     {raw[1][:40]}...\n".encode("utf-8"))
    sys.stdout.buffer.write(f"  display_name in DB: {raw[2]}\n".encode("utf-8"))
    
    assert raw[0].startswith("PPTQ LMS$aes256$v1$")
    assert raw[1].startswith("PPTQ LMS$argon2id$v1$")
    assert raw[2].startswith("PPTQ LMS$aes256$v1$")
    
    print("\nALL DATABASE TESTS PASSED WITH 100% SUCCESS!")
