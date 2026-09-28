document.addEventListener('DOMContentLoaded', () => {
    const startCamBtn = document.getElementById('startCamBtn');
    const stopCamBtn = document.getElementById('stopCamBtn');
    const scanBtn = document.getElementById('scanBtn');
    const video = document.getElementById('videoFeed');
    const canvas = document.getElementById('scanCanvas');
    const cameraContainer = document.getElementById('cameraContainer');
    
    // Result sections
    const idleState = document.getElementById('idleState');
    const loadingResult = document.getElementById('loadingResult');
    const resultCard = document.getElementById('resultCard');
    
    let stream = null;
    let isScanning = false;

    startCamBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
            video.srcObject = stream;
            
            startCamBtn.style.display = 'none';
            stopCamBtn.style.display = 'inline-flex';
            scanBtn.style.display = 'inline-flex';
            
        } catch (err) {
            console.error("Camera access denied", err);
            showAlert('Camera access denied. Please allow camera permissions.', 'error');
        }
    });

    stopCamBtn.addEventListener('click', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
        }
        startCamBtn.style.display = 'inline-flex';
        stopCamBtn.style.display = 'none';
        scanBtn.style.display = 'none';
        cameraContainer.classList.remove('scanning');
    });

    scanBtn.addEventListener('click', async () => {
        if (!stream || isScanning) return;
        
        isScanning = true;
        cameraContainer.classList.add('scanning');
        
        // Show loading state
        idleState.style.display = 'none';
        resultCard.style.display = 'none';
        loadingResult.style.display = 'block';
        scanBtn.disabled = true;

        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        const base64Image = canvas.toDataURL('image/jpeg');

        try {
            const res = await fetchAPI('/attendance/mark', {
                method: 'POST',
                body: JSON.stringify({ image: base64Image })
            });
            
            // Show result
            loadingResult.style.display = 'none';
            resultCard.style.display = 'block';
            
            document.getElementById('resultName').innerText = res.student_name;
            document.getElementById('resultId').innerText = `ID: ${res.student_id}`;
            
            const iconDiv = document.getElementById('resultIcon');
            const statusSpan = document.getElementById('resultStatus');
            
            if (res.status === 'Already Present') {
                iconDiv.innerHTML = '<i class="fas fa-info-circle" style="color: var(--warning);"></i>';
                statusSpan.className = 'badge';
                statusSpan.style.background = 'rgba(245, 158, 11, 0.2)';
                statusSpan.style.color = '#fbbf24';
                statusSpan.innerText = 'Already Marked';
                
                // Keep date/time from response or current if not provided
                document.getElementById('resultDate').innerText = res.date || new Date().toISOString().split('T')[0];
                document.getElementById('resultTime').innerText = res.time || '--:--';
                showAlert(res.message, 'warning');
            } else {
                iconDiv.innerHTML = '<i class="fas fa-check-circle" style="color: var(--success);"></i>';
                statusSpan.className = 'badge present';
                statusSpan.innerText = 'Present';
                
                document.getElementById('resultDate').innerText = res.date;
                document.getElementById('resultTime').innerText = res.time;
                showAlert('Attendance marked successfully!', 'success');
            }
            
        } catch (err) {
            loadingResult.style.display = 'none';
            idleState.style.display = 'block';
            showAlert(err.message, 'error');
        } finally {
            isScanning = false;
            cameraContainer.classList.remove('scanning');
            scanBtn.disabled = false;
        }
    });
});
