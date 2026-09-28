document.addEventListener('DOMContentLoaded', async () => {
    try {
        const stats = await fetchAPI('/dashboard/stats');
        
        document.getElementById('totalStudents').innerText = stats.total_students;
        document.getElementById('presentToday').innerText = stats.present_today;
        document.getElementById('absentToday').innerText = stats.absent_today;
        document.getElementById('attendancePercentage').innerText = stats.attendance_percentage + '%';

        const tableBody = document.getElementById('recentAttendanceTable');
        
        if (stats.recent_attendance && stats.recent_attendance.length > 0) {
            tableBody.innerHTML = '';
            stats.recent_attendance.forEach(record => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${record.student_id}</td>
                    <td>${record.name}</td>
                    <td>${record.attendance_date}</td>
                    <td>${record.attendance_time}</td>
                    <td><span class="badge ${record.status.toLowerCase()}">${record.status}</span></td>
                `;
                tableBody.appendChild(tr);
            });
        } else {
            tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-secondary);">No recent attendance records found.</td></tr>';
        }
        
    } catch (error) {
        console.error("Dashboard error:", error);
        showAlert('Failed to load dashboard data. Is the backend running?', 'error');
    }
});
