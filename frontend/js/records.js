document.addEventListener('DOMContentLoaded', () => {
    let allRecords = [];

    const dateFilter = document.getElementById('dateFilter');
    const searchFilter = document.getElementById('searchFilter');
    const divFilter = document.getElementById('divFilter');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const exportBtn = document.getElementById('exportBtn');

    loadRecords();

    dateFilter.addEventListener('change', applyFilters);
    searchFilter.addEventListener('input', applyFilters);
    divFilter.addEventListener('change', applyFilters);

    resetFiltersBtn.addEventListener('click', () => {
        dateFilter.value = '';
        searchFilter.value = '';
        divFilter.value = '';
        applyFilters();
    });

    exportBtn.addEventListener('click', () => {
        if (allRecords.length === 0) {
            showAlert('No records to export.', 'warning');
            return;
        }

        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Date,Time,Student ID,Name,Division,Status\n";

        const rows = document.querySelectorAll('#recordsTableBody tr');
        rows.forEach(row => {
            const cols = row.querySelectorAll('td');
            if (cols.length === 6) {
                const rowData = [
                    cols[0].innerText,
                    cols[1].innerText,
                    cols[2].innerText,
                    cols[3].innerText,
                    cols[4].innerText,
                    cols[5].innerText
                ];
                csvContent += rowData.join(",") + "\n";
            }
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "attendance_records.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    async function loadRecords() {
        try {
            allRecords = await fetchAPI('/records');
            renderTable(allRecords);
        } catch (err) {
            console.error("Failed to load records", err);
            showAlert('Failed to load attendance records.', 'error');
        }
    }

    function applyFilters() {
        const dVal = dateFilter.value;
        const sVal = searchFilter.value.toLowerCase();
        const divVal = divFilter.value;

        const filtered = allRecords.filter(record => {
            const matchDate = !dVal || record.attendance_date === dVal;
            const matchSearch = !sVal || 
                                record.name.toLowerCase().includes(sVal) || 
                                record.student_id.toLowerCase().includes(sVal);
            const matchDiv = !divVal || record.division === divVal;

            return matchDate && matchSearch && matchDiv;
        });

        renderTable(filtered);
    }

    function renderTable(data) {
        const tbody = document.getElementById('recordsTableBody');
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color: var(--text-secondary);">No records found.</td></tr>';
            return;
        }

        data.forEach(record => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${record.attendance_date}</td>
                <td>${record.attendance_time}</td>
                <td style="font-family: 'Outfit'; font-weight: 500;">${record.student_id}</td>
                <td>${record.name}</td>
                <td>${record.division}</td>
                <td><span class="badge ${record.status.toLowerCase()}">${record.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
});
