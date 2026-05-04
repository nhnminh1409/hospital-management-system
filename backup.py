import os
import subprocess
import mysql.connector
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME

# --- PURE PYTHON BACKUP LOGIC (FALLBACK) ---
def get_tables(cursor):
    cursor.execute("SHOW TABLES")
    return [row[0] for row in cursor.fetchall()]

def get_table_structure(cursor, table_name):
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    return cursor.fetchone()[1]

def get_table_data(cursor, table_name):
    cursor.execute(f"SELECT * FROM `{table_name}`")
    rows = cursor.fetchall()
    if not rows: return []
    insert_statements = []
    for row in rows:
        formatted_values = []
        for val in row:
            if val is None: formatted_values.append("NULL")
            elif isinstance(val, (int, float)): formatted_values.append(str(val))
            else:
                escaped_val = str(val).replace("'", "''")
                formatted_values.append(f"'{escaped_val}'")
        values_str = ", ".join(formatted_values)
        insert_statements.append(f"INSERT INTO `{table_name}` VALUES ({values_str});")
    return insert_statements

def run_pure_python_backup(backup_path):
    print(f"[*] Switching to Pure Python fallback...")
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=DB_PORT, database=DB_NAME)
        cursor = conn.cursor()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(f"-- Automated Python Fallback Backup\nUSE `{DB_NAME}`;\n")
            for table in get_tables(cursor):
                f.write(get_table_structure(cursor, table) + ";\n")
                for stmt in get_table_data(cursor, table): f.write(stmt + "\n")
            
            # Procedures & Triggers
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (DB_NAME,))
            for proc in [row[1] for row in cursor.fetchall()]:
                cursor.execute(f"SHOW CREATE PROCEDURE `{proc}`")
                f.write(f"DELIMITER //\n{cursor.fetchone()[2]} //\nDELIMITER ;\n")
        conn.close()
        print("✅ SUCCESS: Backup created via Python fallback.")
        return True
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return False

# --- MAIN BACKUP RUNNER ---
def run_backup():
    backup_dir = "database_backups"
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{DB_NAME}_backup_{timestamp}.sql")

    # 1. TRY MYSQLDUMP FIRST (The professional way)
    # Using MySQL Workbench path as requested/suggested
    mysqldump_paths = [
        r"D:\Program Files\MySQL\MySQL Workbench 8.0 CE\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Workbench 8.0 CE\mysqldump.exe",
        r"D:\MySQL\MySQL Server 9.5\bin\mysqldump.exe",
        "mysqldump"
    ]
    
    success = False
    for exe_path in mysqldump_paths:
        if exe_path != "mysqldump" and not os.path.exists(exe_path): continue
        
        print(f"[*] Trying mysqldump at: {exe_path}")
        cmd = [exe_path, f"--host={DB_HOST}", f"--port={DB_PORT}", f"--user={DB_USER}", f"--password={DB_PASSWORD}", f"--result-file={backup_path}", DB_NAME]
        
        try:
            env = os.environ.copy()
            mysqldump_dir = os.path.dirname(exe_path) if os.path.isabs(exe_path) else None
            if mysqldump_dir: env["PATH"] = mysqldump_dir + os.pathsep + env.get("PATH", "")
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=mysqldump_dir, env=env)
            if result.returncode == 0:
                print("✅ SUCCESS: Backup completed via mysqldump.")
                success = True
                break
            else:
                print(f"    - Notice: {exe_path} failed with error (likely DLLs).")
        except Exception:
            continue

    # 2. IF MYSQLDUMP FAILED, USE PURE PYTHON
    if not success:
        success = run_pure_python_backup(backup_path)

    if success:
        print(f"[*] Final backup file: {backup_path}")

if __name__ == "__main__":
    run_backup()
