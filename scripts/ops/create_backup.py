import os
import shutil
import pyodbc

def backup_db():
    os.makedirs("backups", exist_ok=True)
    public_backup = r"C:\Users\Public\PWD301_android_master.bak"
    target_backup = os.path.abspath("backups/PWD301_android_master.bak")
    
    print(f"Executing SQL Server backup to: {public_backup}")
    conn = pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=master;Trusted_Connection=yes;TrustServerCertificate=yes;", autocommit=True)
    cursor = conn.cursor()
    sql = f"BACKUP DATABASE [PWD301] TO DISK = N'{public_backup}' WITH FORMAT, INIT, COMPRESSION"
    cursor.execute(sql)
    while cursor.nextset():
        pass
    conn.close()
    
    if os.path.exists(public_backup):
        shutil.copyfile(public_backup, target_backup)
        os.remove(public_backup)
        size_mb = os.path.getsize(target_backup) / (1024 * 1024)
        print(f"[OK] Full Database Backup successfully saved to: {target_backup} ({size_mb:.2f} MB)")
    else:
        print("[!] Backup file not found at Public path.")

if __name__ == "__main__":
    backup_db()
