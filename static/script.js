const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loadingState = document.getElementById('loading-state');
const successMessage = document.getElementById('success-message');
const errorContainer = document.getElementById('error-message');
const errorDetails = document.getElementById('error-details');

const dialog = document.getElementById('download-dialog');
const form = document.getElementById('download-form');
const filenameInput = document.getElementById('filename-input');
const cancelBtn = document.getElementById('cancel-btn');

let currentBlobUrl = null;

dropZone.addEventListener('click', () => {
    fileInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

['dragleave', 'dragend'].forEach(type => {
    dropZone.addEventListener(type, () => {
        dropZone.classList.remove('dragover');
    });
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');

    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFileSelect();
    }
});

async function handleFileSelect() {
    const file = fileInput.files[0];
    if (!file) return;
    if (!file.type.includes('video/mp4')) {
        showError('Please select a valid MP4 video file.');
        return;
    }

    uploadVideo(file);
}

function showLoading() {
    dropZone.classList.add('hidden');
    successMessage.classList.add('hidden');
    errorContainer.classList.add('hidden');
    loadingState.classList.remove('hidden');
}

function showSuccess() {
    loadingState.classList.add('hidden');
    successMessage.classList.remove('hidden');
    dropZone.classList.remove('hidden');
}

function showError(msg) {
    loadingState.classList.add('hidden');
    dropZone.classList.remove('hidden');
    errorContainer.classList.remove('hidden');
    errorDetails.textContent = msg;
}

async function uploadVideo(file) {
    showLoading();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/process-video', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }

        const blob = await response.blob();
        
        // Save blob URL for download
        if (currentBlobUrl) {
            window.URL.revokeObjectURL(currentBlobUrl);
        }
        currentBlobUrl = window.URL.createObjectURL(blob);
        
        // Show success state
        showSuccess();

        // Default filename
        let baseName = file.name.replace(/\.[^/.]+$/, ""); // strip extension
        filenameInput.value = `editado_${baseName}`;

        // Open dialog
        dialog.showModal();

    } catch (err) {
        console.error(err);
        showError(err.message || 'An unknown error occurred during processing.');
    }
}

// Dialog events
cancelBtn.addEventListener('click', () => {
    dialog.close();
});

form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!currentBlobUrl) return;

    const chosenName = filenameInput.value.trim() || 'video_editado';
    
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = currentBlobUrl;
    a.download = `${chosenName}.mp4`;
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    dialog.close();
});
