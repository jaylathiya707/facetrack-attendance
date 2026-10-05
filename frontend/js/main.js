const API_URL = 'http://localhost:5000/api';

function checkAuth() {
    const token = localStorage.getItem('studentToken');
    if (token) {
        document.getElementById('loginView').classList.remove('active');
        document.getElementById('dashboardView').classList.add('active');
        loadStudentDashboard(token);
    } else {
        document.getElementById('loginView').classList.add('active');
        document.getElementById('dashboardView').classList.remove('active');
    }
}

function studentLogout() {
    localStorage.removeItem('studentToken');
    checkAuth();
}

document.getElementById('studentLoginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const enrollment = document.getElementById('enrollment').value;
    const password = document.getElementById('password').value;
    
    try {
        const res = await fetch(`${API_URL}/students/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enrollment_number: enrollment, password: password })
        });
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem('studentToken', data.token);
            checkAuth();
        } else {
            document.getElementById('loginAlert').innerHTML = `<div class="alert alert-error"><i class="fas fa-exclamation-circle"></i> ${data.error || 'Login failed'}</div>`;
        }
    } catch (err) {
        document.getElementById('loginAlert').innerHTML = `<div class="alert alert-error"><i class="fas fa-exclamation-circle"></i> Network error</div>`;
    }
});

async function loadStudentDashboard(token) {
    try {
        const res = await fetch(`${API_URL}/students/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) {
            studentLogout();
            return;
        }
        
        const data = await res.json();
        if (!data.error) {
            const p = data.profile;
            const s = data.stats;
            
            document.getElementById('studentNameDisplay').textContent = p.name;
            document.getElementById('studentIdDisplay').textContent = `(${p.student_id})`;
            document.getElementById('studentInitial').textContent = p.name.charAt(0).toUpperCase();
            
            document.getElementById('profileName').textContent = p.name;
            document.getElementById('profileEnr').textContent = p.enrollment_number;
            document.getElementById('profileBranch').textContent = p.branch_name || 'N/A';
            document.getElementById('profileDiv').textContent = p.division_name || 'N/A';
            document.getElementById('profileSem').textContent = p.semester;
            
            document.getElementById('stat-total').textContent = s.total;
            document.getElementById('stat-present').textContent = s.present;
            document.getElementById('stat-absent').textContent = s.absent;
            document.getElementById('stat-percent').textContent = s.percentage + '%';
            
            const tbody = document.getElementById('recentAttendanceTable');
            if (data.recent_attendance.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: var(--text-secondary);">No attendance records found.</td></tr>`;
            } else {
                tbody.innerHTML = data.recent_attendance.map(a => `
                    <tr>
                        <td>${a.attendance_date}</td>
                        <td>${a.attendance_time}</td>
                        <td>${a.subject || 'N/A'}</td>
                        <td><span class="badge ${a.status === 'Present' ? 'present' : 'absent'}">${a.status}</span></td>
                    </tr>
                `).join('');
            }
        }
    } catch (err) {
        console.error(err);
    }
}

// Run on load
document.addEventListener('DOMContentLoaded', checkAuth);
