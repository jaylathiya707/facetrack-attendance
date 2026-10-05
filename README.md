# FaceTrack - Complete College Attendance Management System

This is a comprehensive upgrade to the Face Recognition System for Attendance, transformed into a full college attendance management system.

## 1. What You Changed

- **Branch Management**: Added CRUD operations for academic branches (e.g., Computer Science, IT).
- **Division Management**: Added CRUD operations for divisions linked to branches.
- **Admin Panel**: Created a dedicated, secure `/admin` area for administrative tasks.
- **Admin Authentication**: Implemented JWT-based admin login with secure password hashing via `bcrypt`.
- **Attendance Schedule**: Added the ability to create attendance sessions tied to Branch, Division, Semester, and time windows.
- **Attendance Time Window**: Enforced that attendance can only be marked during active session windows using the server's timezone (Asia/Kolkata).
- **Automatic Absent Marking**: Implemented a reliable background scheduler using `APScheduler` that automatically finds expired sessions and marks remaining students as "Absent".
- **Audit Logs**: Created an automatic audit logging system to track all administrative actions.
- **Safe Deletion**: Implemented database-level cascade/nullify constraints for safe deletion of records.
- **Reports & Dashboard**: Upgraded the admin dashboard and added comprehensive reports.
- **Backend Refactoring**: Restructured the Flask application to include JWT middleware and timezone-aware logic.

## 2. Files Changed

**Created:**
- `backend/setup_admin.py` (Script to generate admin password hash)
- `backend/migrate.py` (Python migration script)
- `frontend/admin/index.html` (Admin dashboard & panel)
- `frontend/admin/login.html` (Admin login page)
- `frontend/admin/js/admin.js` (Admin panel logic)

**Modified:**
- `backend/app.py` (Completely rewritten to add JWT auth, branches, divisions, sessions, audit, and scheduler)
- `backend/requirements.txt` (Added `bcrypt`, `PyJWT`, `APScheduler`, `pytz`)
- `frontend/students.html` (Updated registration form to use branch_id and division_id)
- `frontend/js/students.js` (Updated API payload and table rendering)
- `frontend/attendance.html` (Minor adjustments)
- `database/schema.sql` (Completely rewritten with new tables and relationships)

## 3. Database Changes

**New Tables:**
- `admin_users`: Stores admin credentials securely.
- `branches`: Stores academic branches.
- `divisions`: Stores divisions linked to branches.
- `attendance_sessions`: Stores scheduled attendance sessions with start and end times.
- `audit_logs`: Tracks administrative actions.

**Modified Tables:**
- `students`: Added `branch_id` and `division_id` as foreign keys.
- `attendance`: Replaced generic date tracking with `session_id` linking to `attendance_sessions`. Added unique constraint on `(student_id, session_id)`.

**Relationships:**
- Branch 1:N Division
- Branch & Division 1:N Students
- Branch & Division 1:N Attendance Sessions
- Session 1:N Attendance Records
- Student 1:N Attendance Records

## 4. How to Run

1. Open a terminal in the project root.
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set up the `.env` file (see Configuration section).
4. Start the backend server:
   ```bash
   python backend/app.py
   ```
5. Serve the frontend (you can use XAMPP, or a simple HTTP server):
   ```bash
   python -m http.server 8000
   ```
6. Open your browser to `http://localhost:8000/frontend/index.html` (or `http://localhost/frontend` if using XAMPP).

## 5. XAMPP Setup

1. Open XAMPP Control Panel.
2. Start the **Apache** and **MySQL** modules.
3. Open `http://localhost/phpmyadmin` in your browser.
4. Create a database named `facetrack_attendance`.
5. Go to the **Import** tab.
6. Choose the file `database/schema.sql` from this repository and click **Import**.
7. Ensure your `.env` file matches your XAMPP configuration (default is usually user `root` with no password).

## 6. Admin Setup

1. Set up your `.env` file based on `.env.example`.
2. The initial admin is defined in the `.env` file as `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
3. Open a terminal and run the setup script to get the password hash:
   ```bash
   python backend/setup_admin.py
   ```
4. Copy the generated `INSERT INTO` SQL command and run it in phpMyAdmin to create the admin user.
5. Open the Admin Panel in your browser: `http://localhost:8000/frontend/admin/login.html` (or your appropriate URL).
6. Log in with the configured username and password.

## 7. Complete Application Walkthrough

1. **Admin Login**: Navigate to `/frontend/admin/login.html` and log in.
2. **Branch Management**: Go to the **Branches** tab and create a new branch (e.g., Computer Science).
3. **Division Management**: Go to the **Divisions** tab and create a division linked to the branch.
4. **Student Registration**: Go to the standard **Students** page (`/frontend/students.html`). Register a student, selecting the appropriate Branch ID and Division ID (as seen in the admin panel), and capture their face.
5. **Schedule Attendance**: Back in the Admin Panel, go to the **Schedules** tab. Create a new session for the branch/division. Set the date, start time, and end time.
6. **Take Attendance**: Navigate to the standard **Take Attendance** page (`/frontend/attendance.html`) during the scheduled time window. Scan the student's face. The system will mark them as Present.
7. **Automatic Absent**: Wait for the scheduled end time to pass. The backend scheduler (running every minute) will automatically find the expired session, mark all remaining students in that branch/division as Absent, and finalize the session.
8. **Reports & Audit**: In the Admin Panel, check the **Reports** tab to see the attendance records. Check the **Audit Logs** tab to see a history of all actions taken (e.g., session creation, student registration).

## 8. Testing Results

| Feature | Result |
| :--- | :--- |
| MySQL connection | NOT VERIFIED |
| Admin login | NOT VERIFIED |
| Student registration | NOT VERIFIED |
| Face registration | NOT VERIFIED |
| Face recognition | NOT VERIFIED |
| Branch management | NOT VERIFIED |
| Division management | NOT VERIFIED |
| Scheduling | NOT VERIFIED |
| Attendance | NOT VERIFIED |
| Duplicate prevention | NOT VERIFIED |
| Automatic absent | NOT VERIFIED |
| Reports | NOT VERIFIED |
| Audit logs | NOT VERIFIED |
| Security checks | NOT VERIFIED |

*(Testing could not be fully verified as MySQL was not accessible on the host machine during development. Please run the application locally following the instructions to verify.)*

## 9. Known Issues

- Student Registration Form: Currently requires manually typing the `Branch ID` and `Division ID` integer values. In a production environment, this should be a dropdown populated dynamically from the API.
- Missing Students: If a student is deleted, their historical attendance records are cascaded/deleted. Soft deletion would be safer.
- Frontend Paths: Hardcoded API URL (`http://localhost:5000/api`) assumes default local setup.

## 10. Future Improvements

- Add a dynamic dropdown for Branches and Divisions on the student registration page.
- Implement Soft Delete (e.g., `is_active` flag) for students to preserve historical attendance.
- Add password reset capabilities for Admin users.
- Support multiple overlapping sessions for the same branch/division if they are different subjects.
- Enhance the frontend Admin Panel with more robust validation and error handling for form submissions.
