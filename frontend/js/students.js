const API_URL = 'http://localhost:5000/api';
const alertContainer = document.getElementById('alertContainer');

function showAlert(message, type = 'success') {
    alertContainer.innerHTML = `<div class="alert alert-${type}"><i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i> ${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 5000);
}

// Load Branches
async function loadBranches() {
    try {
        const res = await fetch(`${API_URL}/branches`);
        const branches = await res.json();
        const branchSelect = document.getElementById('branch_id');
        if (branches.length > 0) {
            branchSelect.innerHTML = '<option value="">Select Branch</option>' + branches.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
        }
    } catch(err) {
        console.log(err);
    }
}

// Load Divisions based on branch
async function loadDivisions(branchId) {
    try {
        const res = await fetch(`${API_URL}/divisions`);
        const divs = await res.json();
        const filtered = divs.filter(d => d.branch_id == branchId);
        const divSelect = document.getElementById('division_id');
        divSelect.innerHTML = '<option value="">Select Division</option>' + filtered.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    } catch(err) {
        console.log(err);
    }
}

document.getElementById('branch_id')?.addEventListener('change', (e) => {
    loadDivisions(e.target.value);
});


// Camera Logic
const video = document.getElementById('regVideo');
const canvas = document.getElementById('regCanvas');
const captureBtn = document.getElementById('captureBtn');
const startCameraBtn = document.getElementById('startCameraBtn');
const cameraPreview = document.getElementById('cameraPreview');
const snapshotPreview = document.getElementById('snapshotPreview');
const capturedImage = document.getElementById('capturedImage');
const retakeBtn = document.getElementById('retakeBtn');
const submitBtn = document.getElementById('submitBtn');
let stream = null;
let imageBase64 = null;

startCameraBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        cameraPreview.style.display = 'block';
        startCameraBtn.style.display = 'none';
        captureBtn.style.display = 'block';
    } catch (err) {
        showAlert('Camera access denied or unavailable.', 'error');
    }
});

captureBtn.addEventListener('click', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    imageBase64 = canvas.toDataURL('image/jpeg');
    
    capturedImage.src = imageBase64;
    cameraPreview.style.display = 'none';
    snapshotPreview.style.display = 'block';
    
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    submitBtn.disabled = false;
});

retakeBtn.addEventListener('click', async () => {
    snapshotPreview.style.display = 'none';
    submitBtn.disabled = true;
    imageBase64 = null;
    startCameraBtn.click();
});

// Form Submission
document.getElementById('registrationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!imageBase64) {
        showAlert('Please capture a face first.', 'warning');
        return;
    }

    const payload = {
        student_id: document.getElementById('studentId').value,
        name: document.getElementById('studentName').value,
        enrollment_number: document.getElementById('enrollmentNo').value,
        branch_id: document.getElementById('branch_id').value,
        division_id: document.getElementById('division_id').value,
        semester: document.getElementById('semester').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        image: imageBase64
    };

    submitBtn.disabled = true;
    document.getElementById('submitLoader').style.display = 'inline-block';

    try {
        const res = await fetch(`${API_URL}/students/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (res.ok) {
            showAlert('Student registered successfully! They can now login with their enrollment number.', 'success');
            document.getElementById('registrationForm').reset();
            retakeBtn.click(); // Reset camera
        } else {
            showAlert(data.error || 'Registration failed.', 'error');
        }
    } catch (err) {
        showAlert('Network error occurred.', 'error');
    } finally {
        submitBtn.disabled = false;
        document.getElementById('submitLoader').style.display = 'none';
    }
});

// Initial load
document.addEventListener('DOMContentLoaded', loadBranches);
