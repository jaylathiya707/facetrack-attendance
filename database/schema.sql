CREATE DATABASE IF NOT EXISTS facetrack_attendance;
USE facetrack_attendance;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    enrollment_number VARCHAR(50) NOT NULL UNIQUE,
    division VARCHAR(10) NOT NULL,
    semester INT NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    face_encoding JSON NOT NULL, -- Storing facial encoding as a JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    attendance_date DATE NOT NULL,
    attendance_time TIME NOT NULL,
    status ENUM('Present', 'Absent') DEFAULT 'Present',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY unique_attendance (student_id, attendance_date) -- Prevents duplicate attendance for the same day
);
