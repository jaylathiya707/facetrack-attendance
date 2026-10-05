import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def migrate_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "facetrack_attendance")
        )
        if not conn.is_connected():
            print("Failed to connect to MySQL")
            return
        
        cursor = conn.cursor()
        
        print("Starting migrations...")

        # 1. Admin Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. Branches
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 3. Divisions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS divisions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            branch_id INT NOT NULL,
            name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE,
            UNIQUE KEY unique_branch_division (branch_id, name)
        )
        """)

        # 4. Attendance Sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            branch_id INT NOT NULL,
            division_id INT NOT NULL,
            semester INT NOT NULL,
            subject VARCHAR(100),
            session_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status ENUM('ACTIVE', 'EXPIRED', 'FINALIZED') DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE,
            FOREIGN KEY (division_id) REFERENCES divisions(id) ON DELETE CASCADE
        )
        """)

        # 5. Audit Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_username VARCHAR(50) NOT NULL,
            action VARCHAR(100) NOT NULL,
            entity VARCHAR(50),
            entity_id VARCHAR(50),
            description TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 6. Alter Students Table
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN branch_id INT")
            cursor.execute("ALTER TABLE students ADD CONSTRAINT fk_student_branch FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                pass
            else:
                print(f"Error altering students branch_id: {err}")

        try:
            cursor.execute("ALTER TABLE students ADD COLUMN division_id INT")
            cursor.execute("ALTER TABLE students ADD CONSTRAINT fk_student_division FOREIGN KEY (division_id) REFERENCES divisions(id) ON DELETE SET NULL")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                pass
            else:
                print(f"Error altering students division_id: {err}")
                
        try:
            cursor.execute("ALTER TABLE students MODIFY COLUMN division VARCHAR(10) NULL")
        except:
            pass

        # 7. Alter Attendance Table
        try:
            cursor.execute("ALTER TABLE attendance ADD COLUMN session_id INT")
            cursor.execute("ALTER TABLE attendance ADD CONSTRAINT fk_attendance_session FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                pass
            else:
                print(f"Error altering attendance session_id: {err}")

        # Drop the UNIQUE KEY unique_attendance on (student_id, attendance_date)
        # because now attendance is per session, so a student might have multiple sessions per day.
        try:
            cursor.execute("ALTER TABLE attendance DROP INDEX unique_attendance")
        except mysql.connector.Error as err:
            pass # Index might not exist
            
        try:
            # Create a new unique key for (student_id, session_id)
            cursor.execute("ALTER TABLE attendance ADD UNIQUE KEY unique_session_attendance (student_id, session_id)")
        except mysql.connector.Error as err:
            pass

        conn.commit()
        print("Migrations completed successfully!")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    migrate_db()
