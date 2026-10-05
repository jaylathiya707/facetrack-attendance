from flask import Flask, request, jsonify, g
from flask_cors import CORS
import base64
import numpy as np
import cv2
import face_recognition
import json
from datetime import datetime, date, time as dtime, timedelta
import os
import bcrypt
import jwt
from functools import wraps
from database import get_db_connection
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask(__name__)
CORS(app)

# Constants
TZ = pytz.timezone('Asia/Kolkata')
JWT_SECRET = os.getenv('JWT_SECRET', 'super_secret_key_change_in_production')

# Helper: Log Audit
def log_audit(admin_username, action, entity, entity_id, description, ip_address):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO audit_logs (admin_username, action, entity, entity_id, description, ip_address) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (admin_username, action, entity, entity_id, description, ip_address))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Audit log failed: {e}")
        finally:
            conn.close()

# Helper: Decode Image
def decode_base64_image(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

# Auth Middleware
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.admin_user = data['username']
        except Exception as e:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.student_id = data['student_id']
        except Exception as e:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        return f(*args, **kwargs)
    return decorated


# ----------------- ADMIN AUTH -----------------
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ip = request.remote_addr

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_users WHERE username = %s", (username,))
        admin = cursor.fetchone()
        
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
            token = jwt.encode({
                'username': username,
                'exp': datetime.now(TZ) + timedelta(hours=8)
            }, JWT_SECRET, algorithm="HS256")
            
            log_audit(username, "Login", "Admin", username, "Successful admin login", ip)
            return jsonify({'token': token, 'username': username}), 200
        else:
            log_audit(username, "Failed Login", "Admin", username, "Failed login attempt", ip)
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

# ----------------- BRANCHES -----------------
@app.route('/api/admin/branches', methods=['GET', 'POST'])
@admin_required
def manage_branches():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM branches ORDER BY name")
        branches = cursor.fetchall()
        cursor.close(); conn.close()
        for b in branches: b['created_at'] = str(b['created_at'])
        return jsonify(branches), 200
        
    elif request.method == 'POST':
        name = request.json.get('name')
        if not name: return jsonify({'error': 'Name is required'}), 400
        try:
            cursor.execute("INSERT INTO branches (name) VALUES (%s)", (name,))
            conn.commit()
            branch_id = cursor.lastrowid
            log_audit(g.admin_user, "Create", "Branch", str(branch_id), f"Created branch {name}", request.remote_addr)
            return jsonify({'message': 'Branch created', 'id': branch_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        finally:
            cursor.close(); conn.close()

@app.route('/api/admin/branches/<int:id>', methods=['DELETE'])
@admin_required
def delete_branch(id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM branches WHERE id = %s", (id,))
        conn.commit()
        log_audit(g.admin_user, "Delete", "Branch", str(id), f"Deleted branch ID {id}", request.remote_addr)
        return jsonify({'message': 'Branch deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@app.route('/api/branches', methods=['GET'])
def get_public_branches():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM branches ORDER BY name")
    branches = cursor.fetchall()
    cursor.close(); conn.close()
    for b in branches: b['created_at'] = str(b['created_at'])
    return jsonify(branches), 200

# ----------------- DIVISIONS -----------------
@app.route('/api/admin/divisions', methods=['GET', 'POST'])
@admin_required
def manage_divisions():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT d.*, b.name as branch_name 
            FROM divisions d 
            JOIN branches b ON d.branch_id = b.id 
            ORDER BY b.name, d.name
        """)
        divisions = cursor.fetchall()
        for d in divisions: d['created_at'] = str(d['created_at'])
        cursor.close(); conn.close()
        return jsonify(divisions), 200
        
    elif request.method == 'POST':
        branch_id = request.json.get('branch_id')
        name = request.json.get('name')
        if not branch_id or not name: return jsonify({'error': 'Branch ID and Name required'}), 400
        try:
            cursor.execute("INSERT INTO divisions (branch_id, name) VALUES (%s, %s)", (branch_id, name))
            conn.commit()
            div_id = cursor.lastrowid
            log_audit(g.admin_user, "Create", "Division", str(div_id), f"Created division {name} for branch {branch_id}", request.remote_addr)
            return jsonify({'message': 'Division created', 'id': div_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        finally:
            cursor.close(); conn.close()

@app.route('/api/admin/divisions/<int:id>', methods=['DELETE'])
@admin_required
def delete_division(id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM divisions WHERE id = %s", (id,))
        conn.commit()
        log_audit(g.admin_user, "Delete", "Division", str(id), f"Deleted division ID {id}", request.remote_addr)
        return jsonify({'message': 'Division deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@app.route('/api/divisions', methods=['GET'])
def get_public_divisions():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, b.name as branch_name 
        FROM divisions d 
        JOIN branches b ON d.branch_id = b.id 
        ORDER BY b.name, d.name
    """)
    divisions = cursor.fetchall()
    for d in divisions: d['created_at'] = str(d['created_at'])
    cursor.close(); conn.close()
    return jsonify(divisions), 200


# ----------------- STUDENT AUTH & DASHBOARD -----------------
@app.route('/api/students/login', methods=['POST'])
def student_login():
    data = request.json
    enrollment = data.get('enrollment_number')
    password = data.get('password')
    if not enrollment or not password:
        return jsonify({'error': 'Enrollment number and password required'}), 400
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE enrollment_number = %s", (enrollment,))
        student = cursor.fetchone()
        if student and bcrypt.checkpw(password.encode('utf-8'), student['password_hash'].encode('utf-8')):
            token = jwt.encode({'student_id': student['student_id'], 'exp': datetime.now(TZ) + timedelta(hours=24)}, JWT_SECRET, algorithm="HS256")
            return jsonify({'token': token, 'student': {'name': student['name'], 'student_id': student['student_id']}}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@app.route('/api/students/me', methods=['GET'])
@student_required
def get_student_me():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch Student Info
        cursor.execute("""
            SELECT s.student_id, s.name, s.enrollment_number, s.semester, s.email,
                   b.name as branch_name, d.name as division_name
            FROM students s
            LEFT JOIN branches b ON s.branch_id = b.id
            LEFT JOIN divisions d ON s.division_id = d.id
            WHERE s.student_id = %s
        """, (g.student_id,))
        student = cursor.fetchone()
        
        if not student: return jsonify({'error': 'Student not found'}), 404
        
        # Fetch recent attendance
        cursor.execute("""
            SELECT a.attendance_date, a.attendance_time, a.status, sess.subject
            FROM attendance a
            JOIN attendance_sessions sess ON a.session_id = sess.id
            WHERE a.student_id = %s
            ORDER BY a.attendance_date DESC, a.attendance_time DESC
        """, (g.student_id,))
        recent_attendance = cursor.fetchall()
        for r in recent_attendance:
            r['attendance_date'] = str(r['attendance_date'])
            r['attendance_time'] = str(r['attendance_time'])

        # Calculate stats
        cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE student_id = %s AND status='Present'", (g.student_id,))
        present_count = cursor.fetchone()['present']
        cursor.execute("SELECT COUNT(*) as absent FROM attendance WHERE student_id = %s AND status='Absent'", (g.student_id,))
        absent_count = cursor.fetchone()['absent']
        total = present_count + absent_count
        attendance_percentage = (present_count / total * 100) if total > 0 else 0

        return jsonify({
            'profile': student,
            'stats': {
                'present': present_count,
                'absent': absent_count,
                'total': total,
                'percentage': round(attendance_percentage, 1)
            },
            'recent_attendance': recent_attendance
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()


# ----------------- STUDENTS MANAGEMENT -----------------
@app.route('/api/students/register', methods=['POST'])
def register_student():
    data = request.json
    try:
        student_id = data.get('student_id')
        name = data.get('name')
        enrollment_number = data.get('enrollment_number')
        branch_id = data.get('branch_id')
        division_id = data.get('division_id')
        semester = data.get('semester')
        email = data.get('email')
        password = data.get('password')
        image_base64 = data.get('image')

        if not all([student_id, name, enrollment_number, branch_id, division_id, semester, email, password, image_base64]):
            return jsonify({'error': 'All fields are required.'}), 400

        img = decode_base64_image(image_base64)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_img)
        
        if len(face_encodings) == 0:
            return jsonify({'error': 'No face detected.'}), 400
        elif len(face_encodings) > 1:
            return jsonify({'error': 'Multiple faces detected.'}), 400
            
        encoding_list = face_encodings[0].tolist()
        
        conn = get_db_connection()
        if not conn: return jsonify({'error': 'DB error'}), 500
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM students WHERE student_id = %s OR enrollment_number = %s OR email = %s", 
                       (student_id, enrollment_number, email))
        if cursor.fetchone():
            return jsonify({'error': 'Student already exists.'}), 400

        query = """
        INSERT INTO students (student_id, name, enrollment_number, password_hash, branch_id, division_id, semester, email, face_encoding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        cursor.execute(query, (student_id, name, enrollment_number, hashed, branch_id, division_id, semester, email, json.dumps(encoding_list)))
        conn.commit()
        log_audit("system/user", "Create", "Student", student_id, f"Registered student {name}", request.remote_addr)
        
        cursor.close(); conn.close()
        return jsonify({'message': 'Student registered successfully!'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    # Allow filtering
    branch_id = request.args.get('branch_id')
    division_id = request.args.get('division_id')
    semester = request.args.get('semester')

    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT s.student_id, s.name, s.enrollment_number, s.semester, s.email, s.created_at,
               b.name as branch_name, d.name as division_name, s.branch_id, s.division_id
        FROM students s
        LEFT JOIN branches b ON s.branch_id = b.id
        LEFT JOIN divisions d ON s.division_id = d.id
        WHERE 1=1
    """
    params = []
    if branch_id:
        query += " AND s.branch_id = %s"
        params.append(branch_id)
    if division_id:
        query += " AND s.division_id = %s"
        params.append(division_id)
    if semester:
        query += " AND s.semester = %s"
        params.append(semester)
        
    query += " ORDER BY s.created_at DESC"
    
    try:
        cursor.execute(query, tuple(params))
        students = cursor.fetchall()
        for s in students: s['created_at'] = str(s['created_at'])
        return jsonify(students), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@app.route('/api/records', methods=['GET'])
def get_records():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT a.attendance_date, a.attendance_time, a.status, s.name, s.student_id, d.name as division
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN divisions d ON s.division_id = d.id
        ORDER BY a.attendance_date DESC, a.attendance_time DESC
    """
    
    try:
        cursor.execute(query)
        records = cursor.fetchall()
        for r in records:
            r['attendance_date'] = str(r['attendance_date'])
            r['attendance_time'] = str(r['attendance_time'])
        return jsonify(records), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@app.route('/api/admin/students/<student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        log_audit(g.admin_user, "Delete", "Student", student_id, f"Deleted student {student_id}", request.remote_addr)
        return jsonify({'message': 'Student deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@app.route('/api/admin/students/<student_id>/transfer', methods=['PUT'])
@admin_required
def transfer_student(student_id):
    data = request.json
    branch_id = data.get('branch_id')
    division_id = data.get('division_id')
    semester = data.get('semester')
    
    # If branch_id or division_id are empty strings, convert to None
    if branch_id == '': branch_id = None
    if division_id == '': division_id = None
    
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB error'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students 
            SET branch_id = %s, division_id = %s, semester = %s
            WHERE student_id = %s
        """, (branch_id, division_id, semester, student_id))
        conn.commit()
        log_audit(g.admin_user, "Transfer", "Student", student_id, f"Transferred to branch {branch_id}, div {division_id}", request.remote_addr)
        return jsonify({'message': 'Student transferred successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()


# ----------------- RECURRING SCHEDULES & ATTENDANCE SESSIONS -----------------
@app.route('/api/admin/schedules', methods=['GET', 'POST'])
@admin_required
def manage_schedules():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT s.*, b.name as branch_name, d.name as division_name
            FROM recurring_schedules s
            JOIN branches b ON s.branch_id = b.id
            JOIN divisions d ON s.division_id = d.id
            ORDER BY FIELD(s.day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), s.start_time
        """)
        schedules = cursor.fetchall()
        for s in schedules:
            s['start_time'] = str(s['start_time'])
            s['end_time'] = str(s['end_time'])
            s['created_at'] = str(s['created_at'])
        cursor.close(); conn.close()
        return jsonify(schedules), 200
        
    elif request.method == 'POST':
        data = request.json
        try:
            query = """
            INSERT INTO recurring_schedules 
            (branch_id, division_id, semester, subject, day_of_week, start_time, end_time, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(query, (
                data['branch_id'], data['division_id'], data['semester'], data.get('subject'),
                data['day_of_week'], data['start_time'], data['end_time']
            ))
            conn.commit()
            schedule_id = cursor.lastrowid
            log_audit(g.admin_user, "Create", "Schedule", str(schedule_id), f"Created schedule for {data['day_of_week']}", request.remote_addr)
            return jsonify({'message': 'Schedule created', 'id': schedule_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        finally:
            cursor.close(); conn.close()

@app.route('/api/admin/schedules/<int:id>', methods=['DELETE'])
@admin_required
def delete_schedule(id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM recurring_schedules WHERE id = %s", (id,))
        conn.commit()
        log_audit(g.admin_user, "Delete", "Schedule", str(id), f"Deleted schedule {id}", request.remote_addr)
        return jsonify({'message': 'Schedule deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close(); conn.close()

@app.route('/api/admin/sessions', methods=['GET'])
@admin_required
def manage_sessions():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database error'}), 500
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT s.*, b.name as branch_name, d.name as division_name
            FROM attendance_sessions s
            JOIN branches b ON s.branch_id = b.id
            JOIN divisions d ON s.division_id = d.id
            ORDER BY s.session_date DESC, s.start_time DESC
        """)
        sessions = cursor.fetchall()
        for s in sessions:
            s['session_date'] = str(s['session_date'])
            s['start_time'] = str(s['start_time'])
            s['end_time'] = str(s['end_time'])
            s['created_at'] = str(s['created_at'])
        cursor.close(); conn.close()
        return jsonify(sessions), 200

# ----------------- ATTENDANCE MARKING -----------------
@app.route('/api/attendance/mark', methods=['POST'])
def mark_attendance():
    data = request.json
    try:
        image_base64 = data.get('image')
        if not image_base64: return jsonify({'error': 'Image is required.'}), 400

        img = decode_base64_image(image_base64)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        unknown_encodings = face_recognition.face_encodings(rgb_img)
        
        if len(unknown_encodings) == 0: return jsonify({'error': 'No face detected.'}), 400
        unknown_encoding = unknown_encodings[0]
        
        conn = get_db_connection()
        if not conn: return jsonify({'error': 'DB error'}), 500
        cursor = conn.cursor(dictionary=True)

        now = datetime.now(TZ)
        current_date = now.date()
        current_time = now.time()

        cursor.execute("""
            SELECT * FROM attendance_sessions 
            WHERE status = 'ACTIVE' 
            AND session_date = %s 
            AND start_time <= %s 
            AND end_time >= %s
        """, (current_date, current_time, current_time))
        active_sessions = cursor.fetchall()

        if not active_sessions:
            cursor.close(); conn.close()
            return jsonify({'error': 'No active attendance session at this time.'}), 400

        valid_students = []
        for sess in active_sessions:
            cursor.execute("""
                SELECT student_id, name, face_encoding, branch_id, division_id, semester 
                FROM students 
                WHERE branch_id = %s AND division_id = %s AND semester = %s
            """, (sess['branch_id'], sess['division_id'], sess['semester']))
            valid_students.extend(cursor.fetchall())

        if not valid_students:
            cursor.close(); conn.close()
            return jsonify({'error': 'No students enrolled for the currently active sessions.'}), 404

        known_encodings = []
        for s in valid_students:
            known_encodings.append(np.array(json.loads(s['face_encoding'])))

        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                student = valid_students[best_match_index]
                
                matched_session = next((s for s in active_sessions if s['branch_id'] == student['branch_id'] and s['division_id'] == student['division_id'] and s['semester'] == student['semester']), None)
                
                if not matched_session:
                    cursor.close(); conn.close()
                    return jsonify({'error': 'Student does not belong to active session.'}), 400

                cursor.execute("SELECT * FROM attendance WHERE student_id = %s AND session_id = %s", (student['student_id'], matched_session['id']))
                if cursor.fetchone():
                    cursor.close(); conn.close()
                    return jsonify({
                        'message': 'Attendance already marked for this session.',
                        'student_name': student['name'], 'student_id': student['student_id'], 'status': 'Already Present'
                    }), 200
                
                cursor.execute("""
                    INSERT INTO attendance (session_id, student_id, attendance_date, attendance_time, status) 
                    VALUES (%s, %s, %s, %s, 'Present')
                """, (matched_session['id'], student['student_id'], current_date, current_time))
                conn.commit()
                
                cursor.close(); conn.close()
                return jsonify({
                    'message': 'Attendance marked successfully.',
                    'student_name': student['name'], 'student_id': student['student_id'],
                    'date': current_date.strftime("%Y-%m-%d"), 'time': current_time.strftime("%I:%M %p"), 'status': 'Present'
                }), 200

        cursor.close(); conn.close()
        return jsonify({'error': 'Face not recognized for the current active sessions.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------- BACKGROUND SCHEDULER (AUTO ABSENT) -----------------
def process_schedules_and_absents():
    """Runs periodically to instantiate daily sessions and mark missing students absent for expired sessions."""
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor(dictionary=True)
        now = datetime.now(TZ)
        current_date = now.date()
        current_time = now.time()
        current_day = now.strftime('%A')

        # 1. Create Active Sessions from Recurring Schedules if it's time
        cursor.execute("SELECT * FROM recurring_schedules WHERE is_active = TRUE AND day_of_week = %s", (current_day,))
        schedules = cursor.fetchall()
        
        for sched in schedules:
            # Check if this schedule is already instantiated for today
            cursor.execute("SELECT id FROM attendance_sessions WHERE schedule_id = %s AND session_date = %s", (sched['id'], current_date))
            if not cursor.fetchone():
                # We instantiate it if we are at or past the start time
                # Wait, if we are past end_time, it will be immediately finalized. That's fine.
                start_val = sched['start_time']
                if isinstance(start_val, timedelta):
                    start_dt = datetime.combine(current_date, dtime.min) + start_val
                else:
                    start_dt = datetime.combine(current_date, start_val)

                if current_time >= (start_dt - timedelta(minutes=5)).time():
                    cursor.execute("""
                        INSERT INTO attendance_sessions 
                        (schedule_id, branch_id, division_id, semester, subject, session_date, start_time, end_time, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                    """, (sched['id'], sched['branch_id'], sched['division_id'], sched['semester'], sched['subject'], current_date, sched['start_time'], sched['end_time']))
                    conn.commit()
                    print(f"Created active session for recurring schedule {sched['id']}")

        # 2. Finalize expired sessions and mark absent
        cursor.execute("""
            SELECT * FROM attendance_sessions 
            WHERE status = 'ACTIVE' 
            AND (session_date < %s OR (session_date = %s AND end_time < %s))
        """, (current_date, current_date, current_time))
        
        expired_sessions = cursor.fetchall()
        for session in expired_sessions:
            sess_id = session['id']
            cursor.execute("""
                SELECT student_id FROM students 
                WHERE branch_id = %s AND division_id = %s AND semester = %s
            """, (session['branch_id'], session['division_id'], session['semester']))
            all_students = [row['student_id'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT student_id FROM attendance WHERE session_id = %s AND status = 'Present'", (sess_id,))
            present_students = [row['student_id'] for row in cursor.fetchall()]
            
            absent_students = set(all_students) - set(present_students)
            
            for st_id in absent_students:
                try:
                    cursor.execute("""
                        INSERT INTO attendance (session_id, student_id, attendance_date, attendance_time, status) 
                        VALUES (%s, %s, %s, %s, 'Absent')
                    """, (sess_id, st_id, session['session_date'], session['end_time']))
                except:
                    pass
                    
            cursor.execute("UPDATE attendance_sessions SET status = 'FINALIZED' WHERE id = %s", (sess_id,))
            conn.commit()
            print(f"Session {sess_id} finalized. {len(absent_students)} students marked absent.")
            
    except Exception as e:
        print(f"Error in scheduler task: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=process_schedules_and_absents, trigger="interval", seconds=60)
scheduler.start()

# ----------------- DASHBOARD & REPORTS -----------------
@app.route('/api/admin/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        today = datetime.now(TZ).date()
        cursor.execute("SELECT COUNT(*) as c FROM attendance WHERE attendance_date = %s AND status = 'Present'", (today,))
        present_today = cursor.fetchone()['c']
        
        cursor.execute("SELECT COUNT(*) as c FROM attendance WHERE attendance_date = %s AND status = 'Absent'", (today,))
        absent_today = cursor.fetchone()['c']
        
        cursor.execute("SELECT COUNT(*) as c FROM branches")
        total_branches = cursor.fetchone()['c']
        
        cursor.execute("SELECT COUNT(*) as c FROM divisions")
        total_divisions = cursor.fetchone()['c']
        
        return jsonify({
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'total_branches': total_branches,
            'total_divisions': total_divisions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close(); conn.close()

@app.route('/api/admin/audit_logs', methods=['GET'])
@admin_required
def get_audit_logs():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100")
        logs = cursor.fetchall()
        for log in logs: log['created_at'] = str(log['created_at'])
        return jsonify(logs), 200
    finally:
        cursor.close(); conn.close()

@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def get_reports():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'DB Error'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.attendance_date, a.status, s.name, s.student_id, b.name as branch_name, d.name as division_name, sess.subject
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            JOIN attendance_sessions sess ON a.session_id = sess.id
            LEFT JOIN branches b ON s.branch_id = b.id
            LEFT JOIN divisions d ON s.division_id = d.id
            ORDER BY a.attendance_date DESC, a.attendance_time DESC
        """
        cursor.execute(query)
        reports = cursor.fetchall()
        for r in reports:
            r['attendance_date'] = str(r['attendance_date'])
        return jsonify(reports), 200
    finally:
        cursor.close(); conn.close()

import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
