"""Migration script to encrypt existing plaintext email and display_name in the local SQL Server database.

Enforces the canonical PPTQ LMS field-level encryption format:
  PPTQ LMS$aes256$v1$<iv_base64>$<ciphertext_base64>
Matching the password hash format:
  PPTQ LMS$argon2id$v1$<salt_base64>$<hash_base64>
"""

import sys
sys.path.insert(0, "src")

from backend import create_app
from backend.extensions import db
from backend.models.identity import User
from backend.services.db_crypto_service import encrypt_field, decrypt_field, PPTQ_FIELD_ENCRYPTION_PREFIX

def run_migration():
    app = create_app("development")
    with app.app_context():
        # Raw SQL query to see actual DB strings before migration
        raw_users = db.session.execute(db.text(
            "SELECT id, email, password_hash, display_name FROM users ORDER BY id"
        )).fetchall()
        
        print(f"Total users found: {len(raw_users)}")
        migrated_count = 0
        
        for row in raw_users:
            user_id = row[0]
            raw_email = row[1]
            raw_pwd = row[2]
            raw_name = row[3]
            
            # Check if email is already encrypted
            email_is_enc = raw_email.startswith(PPTQ_FIELD_ENCRYPTION_PREFIX) if raw_email else False
            name_is_enc = raw_name.startswith(PPTQ_FIELD_ENCRYPTION_PREFIX) if raw_name else False
            
            if not email_is_enc or not name_is_enc:
                new_email = raw_email if email_is_enc else encrypt_field(raw_email, field_type="email")
                new_name = raw_name if name_is_enc else encrypt_field(raw_name, field_type="name")
                
                db.session.execute(
                    db.text("UPDATE users SET email = :email, display_name = :name WHERE id = :id"),
                    {"email": new_email, "name": new_name, "id": user_id}
                )
                migrated_count += 1
                sys.stdout.buffer.write(
                    f"Migrated User ID {user_id}: email encrypted={not email_is_enc}, name encrypted={not name_is_enc}\n".encode("utf-8")
                )
                
        db.session.commit()
        print(f"Migration completed. Total users updated: {migrated_count}")
        
        # Verify in DB
        verify_rows = db.session.execute(db.text(
            "SELECT id, email, email_normalized, password_hash, display_name FROM users ORDER BY id"
        )).fetchall()
        
        print("\n--- DATABASE VERIFICATION (DBeaver view of 'users' table) ---")
        for r in verify_rows[:5]:
            sys.stdout.buffer.write(
                f"ID {r[0]}:\n"
                f"  email:            {r[1]}\n"
                f"  email_normalized: {r[2]}\n"
                f"  password_hash:    {r[3][:45]}...\n"
                f"  display_name:     {r[4]}\n".encode("utf-8")
            )

if __name__ == "__main__":
    run_migration()
