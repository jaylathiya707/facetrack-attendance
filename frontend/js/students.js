document.addEventListener('DOMContentLoaded', () => {
    loadStudents();

    const startCameraBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const video = document.getElementById('regVideo');
    const canvas = document.getElementById('regCanvas');
    const cameraPreview = document.getElementById('cameraPreview');
    const snapshotPreview = document.getElementById('snapshotPreview');
    const capturedImage = document.getElementById('capturedImage');
    const submitBtn = document.getElementById('submitBtn');
    const form = document.getElementById('registrationForm');
    
    let stream = null;
    let base64Image = null;

    startCameraBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            cameraPreview.style.display = 'block';
            startCameraBtn.style.display = 'none';
            captureBtn.style.display = 'inline-flex';
        } catch (err) {
            console.error("Camera access denied", err);
            showAlert('Camera access denied. Please allow camera permissions.', 'error');
        }
    });

    captureBtn.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        base64Image = canvas.toDataURL('image/jpeg');
        
        capturedImage.src = base64Image;
        cameraPreview.style.display = 'none';
        snapshotPreview.style.display = 'block';
        captureBtn.style.display = 'none';
        submitBtn.disabled = false;
        
        // Stop stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });

    retakeBtn.addEventListener('click', async () => {
        snapshotPreview.style.display = 'none';
        base64Image = null;
        submitBtn.disabled = true;
        
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            cameraPreview.style.display = 'block';
            captureBtn.style.display = 'inline-flex';
        } catch (err) {
            showAlert('Camera access denied.', 'error');
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!base64Image) {
            showAlert('Please capture a face image first.', 'warning');
            return;
        }

        const submitLoader = document.getElementById('submitLoader');
        const btnText = submitBtn.childNodes[1]; // text node
        
        submitBtn.disabled = true;
        submitLoader.style.display = 'inline-block';
        
        const studentData = {
            student_id: document.getElementById('studentId').value,
            name: document.getElementById('studentName').value,
            enrollment_number: document.getElementById('enrollmentNo').value,
            division: document.getElementById('division').value,
            semester: document.getElementById('semester').value,
            email: document.getElementById('email').value,
            image: base64Image
        };

        try {
            const res = await fetchAPI('/students/register', {
                method: 'POST',
                body: JSON.stringify(studentData)
            });
            
            showAlert(res.message, 'success');
            form.reset();
            snapshotPreview.style.display = 'none';
            startCameraBtn.style.display = 'inline-flex';
            base64Image = null;
            
            loadStudents(); // Reload list
        } catch (err) {
            showAlert(err.message, 'error');
            submitBtn.disabled = false;
        } finally {
            submitLoader.style.display = 'none';
        }
    });

    async function loadStudents() {
        try {
            const students = await fetchAPI('/students');
            const tbody = document.getElementById('studentsTableBody');
            
            if (students.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color: var(--text-secondary);">No students registered yet.</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            students.forEach(student => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-family: 'Outfit'; font-weight: 500;">${student.student_id}</td>
                    <td>${student.name}</td>
                    <td>${student.division} - Sem ${student.semester}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (err) {
            console.error("Failed to load students", err);
        }
    }
});
