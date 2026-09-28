from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import numpy as np
import cv2
import face_recognition
import json
from datetime import datetime, date
import os
from database import get_db_connection

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

def decode_base64_image(base64_string):
    """Decodes base64 string to an OpenCV image (numpy array)."""
    # Remove header if present (e.g., "data:image/jpeg;base64,")
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@app.route('/api/students/register', methods=['POST'])
def register_student():
    data = request.json
    
    try:
        student_id = data.get('student_id')
        name = data.get('name')
        enrollment_number = data.get('enrollment_number')
        division = data.get('division')
        semester = data.get('semester')
        email = data.get('email')
        image_base64 = data.get('image')

        if not all([student_id, name, enrollment_number, division, semester, email, image_base64]):
            return jsonify({'error': 'All fields are required.'}), 400

        # Process the image to get face encoding
        img = decode_base64_image(image_base64)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Find face encodings
        face_encodings = face_recognition.face_encodings(rgb_img)
        
        if len(face_encodings) == 0:
            return jsonify({'error': 'No face detected in the image. Please try again.'}), 400
        elif len(face_encodings) > 1:
            return jsonify({'error': 'Multiple faces detected. Please ensure only one face is in the frame.'}), 400
            
        # Get the first face encoding and convert to list for JSON storage
        encoding_list = face_encodings[0].tolist()
        
        # Save to database
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed.'}), 500
            
        cursor = conn.cursor()
        
        # Check if student already exists
        cursor.execute("SELECT * FROM students WHERE student_id = %s OR enrollment_number = %s OR email = %s", 
                       (student_id, enrollment_number, email))
        if cursor.fetchone():
            return jsonify({'error': 'Student with this ID, Enrollment Number, or Email already exists.'}), 400

        insert_query = """
        INSERT INTO students (student_id, name, enrollment_number, division, semester, email, face_encoding)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (student_id, name, enrollment_number, division, semester, email, json.dumps(encoding_list)))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Student registered successfully!'}), 201
        
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/mark', methods=['POST'])
def mark_attendance():
    data = request.json
    
    try:
        image_base64 = data.get('image')
        if not image_base64:
            return jsonify({'error': 'Image is required.'}), 400

        # Process the image
        img = decode_base64_image(image_base64)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Find face encodings in the uploaded image
        unknown_encodings = face_recognition.face_encodings(rgb_img)
        
        if len(unknown_encodings) == 0:
            return jsonify({'error': 'No face detected.'}), 400
        
        unknown_encoding = unknown_encodings[0]
        
        # Fetch all registered students
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed.'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT student_id, name, face_encoding FROM students")
        students = cursor.fetchall()
        
        if not students:
            return jsonify({'error': 'No students registered in the system.'}), 404

        known_encodings = []
        known_student_ids = []
        known_names = []
        
        for student in students:
            encoding_list = json.loads(student['face_encoding'])
            known_encodings.append(np.array(encoding_list))
            known_student_ids.append(student['student_id'])
            known_names.append(student['name'])

        # Compare faces
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            student_id = known_student_ids[best_match_index]
            student_name = known_names[best_match_index]
            
            # Check if attendance already marked for today
            today = date.today()
            current_time = datetime.now().time()
            
            check_query = "SELECT * FROM attendance WHERE student_id = %s AND attendance_date = %s"
            cursor.execute(check_query, (student_id, today))
            existing_record = cursor.fetchone()
            
            if existing_record:
                cursor.close()
                conn.close()
                return jsonify({
                    'message': 'Attendance already marked for today.',
                    'student_name': student_name,
                    'student_id': student_id,
                    'status': 'Already Present'
                }), 200
            
            # Mark attendance
            insert_query = "INSERT INTO attendance (student_id, attendance_date, attendance_time, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (student_id, today, current_time, 'Present'))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'Attendance marked successfully.',
                'student_name': student_name,
                'student_id': student_id,
                'date': today.strftime("%Y-%m-%d"),
                'time': current_time.strftime("%I:%M %p"),
                'status': 'Present'
            }), 200
            
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Face not recognized. Student not found in database.'}), 404

    except Exception as e:
        print(f"Error during attendance marking: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed.'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Total Students
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # Today's Present
        today = date.today()
        cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE attendance_date = %s", (today,))
        present_today = cursor.fetchone()['present']
        
        absent_today = total_students - present_today if total_students > 0 else 0
        
        # Recent Attendance
        recent_query = """
            SELECT a.attendance_date, a.attendance_time, a.status, s.name, s.student_id 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            ORDER BY a.created_at DESC
            LIMIT 5
        """
        cursor.execute(recent_query)
        recent_attendance = cursor.fetchall()
        
        # Format dates and times for JSON serialization
        for record in recent_attendance:
            record['attendance_date'] = record['attendance_date'].strftime("%Y-%m-%d")
            
            # Ensure attendance_time is handled properly (it can be a timedelta object from MySQL)
            if hasattr(record['attendance_time'], 'seconds'):
                # Convert timedelta to time string
                total_seconds = record['attendance_time'].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                record['attendance_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                record['attendance_time'] = str(record['attendance_time'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_percentage': round((present_today/total_students*100), 2) if total_students > 0 else 0,
            'recent_attendance': recent_attendance
        }), 200

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed.'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT a.id, a.attendance_date, a.attendance_time, a.status, s.name, s.student_id, s.division
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            ORDER BY a.attendance_date DESC, a.attendance_time DESC
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        for record in records:
            record['attendance_date'] = record['attendance_date'].strftime("%Y-%m-%d")
            if hasattr(record['attendance_time'], 'seconds'):
                total_seconds = record['attendance_time'].seconds
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                record['attendance_time'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                record['attendance_time'] = str(record['attendance_time'])
                
        cursor.close()
        conn.close()
        
        return jsonify(records), 200

    except Exception as e:
        print(f"Error fetching records: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed.'}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT student_id, name, enrollment_number, division, semester, email, created_at FROM students ORDER BY created_at DESC")
        students = cursor.fetchall()
        
        for student in students:
            student['created_at'] = student['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            
        cursor.close()
        conn.close()
        
        return jsonify(students), 200

    except Exception as e:
        print(f"Error fetching students: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
