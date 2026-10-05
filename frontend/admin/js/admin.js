const API_URL = 'http://localhost:5000/api';

// Auth Check
const token = localStorage.getItem('adminToken');
if (!token && !window.location.href.includes('login.html')) {
    window.location.href = 'login.html';
}

if (document.getElementById('admin-name')) {
    document.getElementById('admin-name').textContent = `Welcome, ${localStorage.getItem('adminUsername')}`;
}

function logout() {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminUsername');
    window.location.href = 'login.html';
}

// Navigation
function showSection(id) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-links a').forEach(el => el.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.getElementById(`nav-${id}`).classList.add('active');
    document.getElementById('page-title').textContent = id.charAt(0).toUpperCase() + id.slice(1);
    
    // Load data based on section
    if(id === 'dashboard') loadDashboard();
    if(id === 'branches') loadBranches();
    if(id === 'divisions') loadDivisions();
    if(id === 'students') {
        loadBranches();
        loadStudents();
    }
    if(id === 'schedules') {
        loadBranches();
        loadSchedules();
        loadSessions();
    }
    if(id === 'reports') loadReports();
    if(id === 'audit') loadAudit();
}

// Modals
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// API Helper
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Authorization': `Bearer ${token}` }
    };
    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }
    const res = await fetch(`${API_URL}${endpoint}`, options);
    if (res.status === 401) logout();
    return await res.json();
}

// Load Dashboard
async function loadDashboard() {
    const data = await apiCall('/admin/dashboard');
    if (!data.error) {
        document.getElementById('stat-students').textContent = data.total_students;
        document.getElementById('stat-present').textContent = data.present_today;
        document.getElementById('stat-absent').textContent = data.absent_today;
    }
}

// Load Branches
async function loadBranches() {
    const data = await apiCall('/admin/branches');
    if (!data.error) {
        const tbody = document.getElementById('branchesTable');
        if (tbody) {
            tbody.innerHTML = data.map(b => `
                <tr>
                    <td>${b.id}</td>
                    <td>${b.name}</td>
                    <td><button class="btn btn-danger" onclick="deleteBranch(${b.id})">Delete</button></td>
                </tr>
            `).join('');
        }
        
        // Populate branch dropdowns
        const opts = `<option value="">Select Branch</option>` + data.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
        const dbs = document.getElementById('divBranchSelect'); if(dbs) dbs.innerHTML = opts;
        const sbs = document.getElementById('schedBranchSelect'); if(sbs) sbs.innerHTML = opts;
        const tbs = document.getElementById('transBranchSelect'); if(tbs) tbs.innerHTML = opts;
    }
}

async function deleteBranch(id) {
    if(confirm('Delete this branch?')) {
        await apiCall(`/admin/branches/${id}`, 'DELETE');
        loadBranches();
    }
}

document.getElementById('branchForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await apiCall('/admin/branches', 'POST', { name: document.getElementById('branchName').value });
    closeModal('branchModal');
    loadBranches();
});

// Load Divisions
async function loadDivisions() {
    const data = await apiCall('/admin/divisions');
    if (!data.error) {
        document.getElementById('divisionsTable').innerHTML = data.map(d => `
            <tr>
                <td>${d.id}</td>
                <td>${d.branch_name}</td>
                <td>${d.name}</td>
                <td><button class="btn btn-danger" onclick="deleteDivision(${d.id})">Delete</button></td>
            </tr>
        `).join('');
    }
}

async function deleteDivision(id) {
    if(confirm('Delete division?')) {
        await apiCall(`/admin/divisions/${id}`, 'DELETE');
        loadDivisions();
    }
}

document.getElementById('divisionForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await apiCall('/admin/divisions', 'POST', { 
        branch_id: document.getElementById('divBranchSelect').value,
        name: document.getElementById('divisionName').value 
    });
    closeModal('divisionModal');
    loadDivisions();
});

// Load Students
async function loadStudents() {
    const data = await apiCall('/students');
    if (!data.error) {
        document.getElementById('studentsTable').innerHTML = data.map(s => `
            <tr>
                <td>${s.student_id}</td>
                <td>${s.name}</td>
                <td>${s.branch_name || 'N/A'}</td>
                <td>${s.division_name || 'N/A'}</td>
                <td>${s.semester}</td>
                <td>
                    <button class="btn btn-primary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="openTransferModal('${s.student_id}', '${s.branch_id}', '${s.division_id}', '${s.semester}')">Transfer</button>
                    <button class="btn btn-danger" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="deleteStudent('${s.student_id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    }
}

function openTransferModal(id, branch_id, division_id, semester) {
    document.getElementById('transferStudentId').value = id;
    if(branch_id && branch_id !== 'null') document.getElementById('transBranchSelect').value = branch_id;
    if(semester) document.getElementById('transSem').value = semester;
    // Trigger division load
    loadDivisionsForSelect('transBranchSelect', 'transDivSelect').then(() => {
        if(division_id && division_id !== 'null') document.getElementById('transDivSelect').value = division_id;
    });
    openModal('transferModal');
}

async function loadDivisionsForSelect(branchSelectId, divSelectId) {
    const branchId = document.getElementById(branchSelectId).value;
    const divs = await apiCall('/admin/divisions');
    const filtered = divs.filter(d => d.branch_id == branchId);
    document.getElementById(divSelectId).innerHTML = `<option value="">Select Division</option>` + 
        filtered.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
}

document.getElementById('transBranchSelect')?.addEventListener('change', () => loadDivisionsForSelect('transBranchSelect', 'transDivSelect'));
document.getElementById('schedBranchSelect')?.addEventListener('change', () => loadDivisionsForSelect('schedBranchSelect', 'schedDivSelect'));

document.getElementById('transferForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('transferStudentId').value;
    await apiCall(`/admin/students/${id}/transfer`, 'PUT', {
        branch_id: document.getElementById('transBranchSelect').value,
        division_id: document.getElementById('transDivSelect').value,
        semester: document.getElementById('transSem').value
    });
    closeModal('transferModal');
    loadStudents();
});

async function removeStudentFromDivision() {
    const id = document.getElementById('transferStudentId').value;
    await apiCall(`/admin/students/${id}/transfer`, 'PUT', {
        branch_id: '',
        division_id: '',
        semester: document.getElementById('transSem').value
    });
    closeModal('transferModal');
    loadStudents();
}


async function deleteStudent(id) {
    if(confirm('Warning: Deleting a student destroys historical attendance data. Are you sure you want to delete this student completely? (Use Transfer to remove them from a branch instead)')) {
        await apiCall(`/admin/students/${id}`, 'DELETE');
        loadStudents();
    }
}

// Load Schedules
async function loadSchedules() {
    const data = await apiCall('/admin/schedules');
    if (!data.error) {
        document.getElementById('recurringSchedulesTable').innerHTML = data.map(s => `
            <tr>
                <td>${s.day_of_week}</td>
                <td>${s.branch_name} - ${s.division_name}</td>
                <td>${s.subject}</td>
                <td>${s.start_time} - ${s.end_time}</td>
                <td><button class="btn btn-danger" onclick="deleteSchedule(${s.id})">Delete</button></td>
            </tr>
        `).join('');
    }
}

async function deleteSchedule(id) {
    if(confirm('Delete this recurring schedule?')) {
        await apiCall(`/admin/schedules/${id}`, 'DELETE');
        loadSchedules();
    }
}

document.getElementById('scheduleForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await apiCall('/admin/schedules', 'POST', {
        branch_id: document.getElementById('schedBranchSelect').value,
        division_id: document.getElementById('schedDivSelect').value,
        semester: document.getElementById('schedSem').value,
        subject: document.getElementById('schedSub').value,
        day_of_week: document.getElementById('schedDay').value,
        start_time: document.getElementById('schedStart').value,
        end_time: document.getElementById('schedEnd').value
    });
    closeModal('scheduleModal');
    loadSchedules();
});

// Load Active Daily Sessions
async function loadSessions() {
    const data = await apiCall('/admin/sessions');
    if (!data.error) {
        document.getElementById('sessionsTable').innerHTML = data.map(s => `
            <tr>
                <td>${s.session_date}</td>
                <td>${s.branch_name} - ${s.division_name}</td>
                <td>${s.subject}</td>
                <td>${s.start_time} - ${s.end_time}</td>
                <td><span class="badge ${s.status === 'ACTIVE' ? 'present' : 'absent'}">${s.status}</span></td>
            </tr>
        `).join('');
    }
}

// Load Reports
async function loadReports() {
    const data = await apiCall('/admin/reports');
    if (!data.error) {
        document.getElementById('reportsTable').innerHTML = data.map(r => `
            <tr>
                <td>${r.attendance_date}</td>
                <td>${r.name} (${r.student_id})</td>
                <td>${r.branch_name} - ${r.division_name}</td>
                <td>${r.subject}</td>
                <td><span class="badge ${r.status === 'Present' ? 'present' : 'absent'}">${r.status}</span></td>
            </tr>
        `).join('');
    }
}

// Load Audit Logs
async function loadAudit() {
    const data = await apiCall('/admin/audit_logs');
    if (!data.error) {
        document.getElementById('auditTable').innerHTML = data.map(l => `
            <tr>
                <td>${l.created_at}</td>
                <td>${l.admin_username}</td>
                <td>${l.action}</td>
                <td>${l.entity} (${l.entity_id})</td>
                <td>${l.description}</td>
            </tr>
        `).join('');
    }
}

// Initial load
if(!window.location.href.includes('login.html')) {
    loadDashboard();
    loadBranches(); // Preload for dropdowns
}
