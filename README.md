# FaceTrack - Face Recognition Attendance System

FaceTrack is a modern, full-stack face recognition attendance system developed for the FSD Innovative Assignment. It provides an efficient and fast way to manage student attendance using computer vision.

## Features

- **Student Registration**: Register students with their details and face encoding.
- **Face Registration**: Capture student faces using a webcam directly from the browser.
- **Automated Attendance**: Mark attendance simply by scanning a face through the webcam.
- **Duplicate Prevention**: Prevents the same student from being marked present multiple times in a single day.
- **Dashboard**: View real-time statistics (total students, present today, absent today, attendance percentage).
- **Records & Reports**: View historical attendance data with filters (Date, Student ID, Division) and export to CSV.
- **Modern UI**: A premium, responsive interface featuring glassmorphism and dynamic design.

## Technologies Used

- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript (Vanilla)
- **Backend**: Python 3, Flask, Flask-CORS
- **Computer Vision**: OpenCV, dlib, face_recognition
- **Database**: MySQL (via XAMPP)

## Project Structure

```text
face-attendance-system/
│
├── frontend/
│   ├── index.html           # Dashboard
│   ├── students.html        # Registration
│   ├── attendance.html      # Take Attendance
│   ├── records.html         # View Records
│   ├── css/
│   │   └── style.css        # Premium Glassmorphism UI
│   └── js/
│       ├── api.js           # API Helper
│       ├── main.js          # Dashboard Logic
│       ├── students.js      # Registration Logic
│       ├── attendance.js    # Camera/Scanning Logic
│       └── records.js       # Filtering & Export Logic
│
├── backend/
│   ├── app.py               # Main Flask API
│   ├── database.py          # MySQL Connection Handling
│   └── requirements.txt     # Python Dependencies
│
├── database/
│   └── schema.sql           # MySQL Database Schema
│
├── .env                     # Environment Variables
├── .env.example
└── README.md
```

## Requirements

- **XAMPP** (For MySQL server)
- **Python 3.8+** (Required for the backend)
- **C++ Build Tools** (Required on Windows to compile `dlib` if not using pre-built wheels)
- **Modern Web Browser** (Chrome/Edge/Firefox) with Webcam access

## Setup Instructions

### 1. XAMPP & MySQL Database Setup

1. Install and open **XAMPP Control Panel**.
2. Start the **MySQL** module.
3. Open `http://localhost/phpmyadmin` in your browser.
4. Go to the **Import** tab.
5. Choose the file `database/schema.sql` from this repository and click **Import**.
   - *Alternatively, create a database named `facetrack_attendance` and paste the contents of `schema.sql` into the SQL tab.*

### 2. Python Backend Setup

1. Open a terminal in the project root directory.
2. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   # Activate it (Windows)
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
   > **Note on `face_recognition`**: Installing this on Windows might require Visual Studio C++ Build tools because it compiles `dlib`. If you encounter errors, install CMake (`pip install cmake`) and ensure C++ tools are installed.
4. Ensure the `.env` file exists in the root directory and matches your XAMPP MySQL configuration:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=facetrack_attendance
   PORT=5000
   ```
5. Run the Flask server:
   ```bash
   python backend/app.py
   ```
   The backend should now be running on `http://localhost:5000`.

### 3. Frontend Setup

1. You can serve the frontend files using any simple HTTP server, or simply open the HTML files directly.
2. To run a simple server:
   ```bash
   # From the project root
   python -m http.server 8000
   ```
3. Open `http://localhost:8000/frontend/index.html` in your browser.
   *(Or just double-click `frontend/index.html` to open it in your browser).*

## How to Use the System

### How to Register a Student and Face Data
1. Navigate to the **Students** page.
2. Fill in the student details (ID, Name, Enrollment Number, Division, Semester, Email).
3. Under Face Registration, click **Start Camera**. (Allow camera permissions if prompted).
4. Look at the camera and click **Capture Face**.
5. Click **Register Student**. The face encoding and details will be saved to MySQL.

### How to Take Attendance
1. Navigate to the **Take Attendance** page.
2. Click **Start Camera**.
3. Have the registered student look at the camera.
4. Click **Scan Face**.
5. The system will identify the student and mark them present. If they are already marked present for the day, it will display an "Already Marked" warning.

### How to View Reports
1. Navigate to the **Records & Reports** page.
2. View all attendance records.
3. Use the filters (Date, Student ID/Name, Division) to narrow down results.
4. Click **Export CSV** to download the filtered data.

## Testing Results

The system has been comprehensively tested for:
- **Database**: Successful connection, correct schema creation, and CRUD operations.
- **Face Recognition**: 
  - Detects faces correctly using `face_recognition` library.
  - Recognizes known students with high accuracy.
  - Rejects unknown faces.
- **Duplicate Prevention**: Handles duplicate scans smoothly by notifying the user instead of duplicating database records.
- **Frontend-Backend Integration**: API endpoints successfully receive base64 image strings, decode them, process them, and return appropriate JSON responses.

## Known Limitations

- **Lighting**: Face recognition accuracy may drop in extremely low light or harsh backlighting.
- **Multiple Faces**: The current setup rejects the scan if multiple faces are in the frame to prevent ambiguity during attendance marking.
- **Scalability**: Processing large numbers of faces sequentially in Python (without vectorization optimizations or parallel processing) might slow down identification as the database grows significantly.

## Suggestions for Future Improvements

- Implement real-time continuous scanning (webcam feed processed live via WebSockets) instead of manual capture-and-scan.
- Add an Admin Authentication layer to secure the dashboard and registration endpoints.
- Support multiple face detections simultaneously to mark attendance for a group of students at once.
- Migrate to a more scalable model endpoint (e.g., deploying the face recognition model as a microservice on a GPU instance).
