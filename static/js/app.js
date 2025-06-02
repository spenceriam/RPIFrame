/**
 * RPIFrame Web Application
 * Main JavaScript file
 */

// Wait for DOM to be loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize application
    const app = new RPIFrameApp();
    app.init();
});

class RPIFrameApp {
    constructor() {
        // Tab navigation
        this.tabs = document.querySelectorAll('.tab');
        this.tabContents = document.querySelectorAll('.tab-content');
        
        // Photo management
        this.photosContainer = document.getElementById('photos-container');
        this.photoTemplate = document.getElementById('photo-template');
        this.dropzone = document.getElementById('dropzone');
        this.fileInput = document.getElementById('file-input');
        this.uploadProgress = document.getElementById('upload-progress');
        this.progressFill = document.querySelector('.progress-fill');
        this.progressText = document.querySelector('.progress-text');
        this.refreshDisplayBtn = document.getElementById('refresh-display');
        
        // Settings management
        this.rotationInterval = document.getElementById('rotation-interval');
        this.displayBrightness = document.getElementById('display-brightness');
        this.enableTransitions = document.getElementById('enable-transitions');
        this.enableTouch = document.getElementById('enable-touch');
        this.imageRotation = document.getElementById('image-rotation');
        this.fitMode = document.getElementById('fit-mode');
        this.timezone = document.getElementById('timezone');
        this.saveSettingsBtn = document.getElementById('save-settings');
        
        // System information
        this.diskFill = document.querySelector('.disk-fill');
        this.diskText = document.querySelector('.disk-text');
        this.statusIndicator = document.querySelector('.indicator');
        this.statusText = document.querySelector('.status-text');
        this.uptimeEl = document.getElementById('uptime');
        this.cpuTempEl = document.getElementById('cpu-temp');
        this.photoCountEl = document.getElementById('photo-count');
        this.lastUpdateEl = document.getElementById('last-update');
        this.systemLogsEl = document.getElementById('system-logs');
        this.refreshStatusBtn = document.getElementById('refresh-status');
        this.startServiceBtn = document.getElementById('start-service');
        
        // Notifications
        this.notifications = document.getElementById('notifications');
    }
    
    init() {
        // Initialize tab navigation
        this.initTabs();
        
        // Initialize photo management
        this.initPhotoManagement();
        
        // Initialize settings
        this.initSettings();
        
        // Initialize system information
        this.initSystemInfo();
        
        // Load the active tab data
        this.loadTabData(this.getActiveTab());
    }
    
    initTabs() {
        // Add click event listeners to tabs
        this.tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs
                this.tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Hide all tab contents
                this.tabContents.forEach(content => content.classList.remove('active'));
                
                // Show the selected tab content
                const tabId = tab.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
                
                // Load tab data
                this.loadTabData(tabId);
            });
        });
    }
    
    getActiveTab() {
        // Get the active tab
        const activeTab = document.querySelector('.tab.active');
        return activeTab ? activeTab.getAttribute('data-tab') : 'photos';
    }
    
    loadTabData(tabId) {
        // Load data for the active tab
        switch (tabId) {
            case 'photos':
                this.loadPhotos();
                break;
            case 'settings':
                this.loadSettings();
                break;
            case 'system':
                this.loadSystemInfo();
                break;
        }
    }
    
    initPhotoManagement() {
        // Initialize dropzone for file uploads
        this.dropzone.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropzone.classList.add('drag-over');
        });
        
        this.dropzone.addEventListener('dragleave', () => {
            this.dropzone.classList.remove('drag-over');
        });
        
        this.dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropzone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                this.uploadFiles(e.dataTransfer.files);
            }
        });
        
        this.fileInput.addEventListener('change', () => {
            if (this.fileInput.files.length > 0) {
                this.uploadFiles(this.fileInput.files);
            }
        });
        
        // Refresh display button
        this.refreshDisplayBtn.addEventListener('click', () => {
            this.refreshDisplay();
        });
    }
    
    initSettings() {
        // Populate timezone dropdown
        this.populateTimezones();
        
        // Save settings button
        this.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });
    }
    
    initSystemInfo() {
        // Refresh status button
        this.refreshStatusBtn.addEventListener('click', () => {
            this.loadSystemInfo();
        });
        
        // Start service button
        this.startServiceBtn.addEventListener('click', () => {
            this.startService();
        });
    }
    
    async loadPhotos() {
        try {
            // Show loading indicator
            this.photosContainer.innerHTML = '<div class="loading">Loading photos...</div>';
            
            // Fetch photos from the API
            const response = await fetch('/api/photos');
            const data = await response.json();
            
            // Clear the container
            this.photosContainer.innerHTML = '';
            
            if (data.photos && data.photos.length > 0) {
                // Display each photo
                data.photos.forEach(photo => {
                    this.addPhotoToGallery(photo);
                });
            } else {
                // Show empty state
                this.photosContainer.innerHTML = '<div class="empty-state">No photos uploaded yet. Upload some photos to get started!</div>';
            }
        } catch (error) {
            console.error('Error loading photos:', error);
            this.showNotification('Failed to load photos', 'error');
            this.photosContainer.innerHTML = '<div class="error">Failed to load photos. Please refresh the page.</div>';
        }
    }
    
    addPhotoToGallery(photo) {
        // Clone the photo template
        const photoElement = this.photoTemplate.content.cloneNode(true);
        
        // Get the elements from the template
        const item = photoElement.querySelector('.photo-item');
        const img = photoElement.querySelector('img');
        const name = photoElement.querySelector('.photo-name');
        const date = photoElement.querySelector('.photo-date');
        const deleteBtn = photoElement.querySelector('.delete-photo');
        
        // Set the data
        item.dataset.photoId = photo.id;
        img.src = photo.thumbnail;
        img.alt = photo.name;
        name.textContent = photo.name;
        date.textContent = new Date(photo.date_added).toLocaleDateString();
        
        // Add delete functionality
        deleteBtn.addEventListener('click', () => {
            this.deletePhoto(photo.id, item);
        });
        
        // Add the photo to the container
        this.photosContainer.appendChild(photoElement);
    }
    
    async uploadFiles(files) {
        // Show upload progress
        this.uploadProgress.classList.remove('hidden');
        
        let totalFiles = files.length;
        let uploaded = 0;
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Update progress
            const percent = Math.round((i / totalFiles) * 100);
            this.progressFill.style.width = percent + '%';
            this.progressText.textContent = `Uploading ${file.name}... ${percent}%`;
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                // Upload the file
                const response = await fetch('/api/photos', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    uploaded++;
                    this.showNotification(`${file.name} uploaded successfully`, 'success');
                } else {
                    this.showNotification(`Failed to upload ${file.name}: ${data.error}`, 'error');
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.showNotification(`Failed to upload ${file.name}`, 'error');
            }
        }
        
        // Hide upload progress
        this.uploadProgress.classList.add('hidden');
        this.progressFill.style.width = '0%';
        
        // Reload photos
        if (uploaded > 0) {
            this.loadPhotos();
        }
        
        // Clear file input
        this.fileInput.value = '';
    }
    
    async deletePhoto(photoId, photoElement) {
        if (!confirm('Are you sure you want to delete this photo?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/photos/${photoId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Remove the photo from the DOM
                photoElement.remove();
                this.showNotification('Photo deleted successfully', 'success');
                
                // Check if gallery is empty
                if (this.photosContainer.children.length === 0) {
                    this.photosContainer.innerHTML = '<div class="empty-state">No photos uploaded yet. Upload some photos to get started!</div>';
                }
            } else {
                this.showNotification(`Failed to delete photo: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Failed to delete photo', 'error');
        }
    }
    
    async refreshDisplay() {
        try {
            const response = await fetch('/api/refresh', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification(`Failed to refresh display: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Refresh error:', error);
            this.showNotification('Failed to refresh display', 'error');
        }
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (response.ok && data.config) {
                const config = data.config;
                
                // Display settings
                if (config.display) {
                    this.rotationInterval.value = config.display.rotation_interval_minutes || 60;
                    this.displayBrightness.value = config.display.brightness || 100;
                    this.enableTransitions.checked = config.display.enable_transitions || false;
                    this.enableTouch.checked = config.display.enable_touch || false;
                    this.imageRotation.value = config.display.image_rotation || 0;
                    this.fitMode.value = config.display.fit_mode || 'contain';
                }
                
                // System settings
                if (config.system) {
                    this.timezone.value = config.system.timezone || 'UTC';
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showNotification('Failed to load settings', 'error');
        }
    }
    
    async saveSettings() {
        try {
            const config = {
                display: {
                    rotation_interval_minutes: parseInt(this.rotationInterval.value),
                    brightness: parseInt(this.displayBrightness.value),
                    enable_transitions: this.enableTransitions.checked,
                    enable_touch: this.enableTouch.checked,
                    image_rotation: parseInt(this.imageRotation.value),
                    fit_mode: this.fitMode.value
                },
                system: {
                    timezone: this.timezone.value
                }
            };
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Settings saved successfully', 'success');
            } else {
                this.showNotification(`Failed to save settings: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system/status');
            const data = await response.json();
            
            if (response.ok && data.status) {
                const status = data.status;
                
                // Update disk usage
                if (status.disk) {
                    this.diskFill.style.width = status.disk.percent_used + '%';
                    this.diskText.textContent = `${status.disk.used} / ${status.disk.total} (${status.disk.percent_used}%)`;
                }
                
                // Update service status
                if (status.display_running) {
                    this.statusIndicator.classList.add('active');
                    this.statusText.textContent = 'Running';
                    this.startServiceBtn.disabled = true;
                } else {
                    this.statusIndicator.classList.remove('active');
                    this.statusText.textContent = 'Stopped';
                    this.startServiceBtn.disabled = false;
                }
                
                // Update system information
                this.uptimeEl.textContent = this.formatUptime(status.uptime);
                this.cpuTempEl.textContent = status.cpu_temp;
                this.photoCountEl.textContent = status.photo_count;
                this.lastUpdateEl.textContent = new Date(status.timestamp).toLocaleString();
                
                // Load logs
                this.loadLogs();
            }
        } catch (error) {
            console.error('Error loading system info:', error);
            this.showNotification('Failed to load system information', 'error');
        }
    }
    
    async loadLogs() {
        try {
            const response = await fetch('/api/system/logs?lines=50');
            const data = await response.json();
            
            if (response.ok && data.logs) {
                this.systemLogsEl.textContent = data.logs.join('');
                // Scroll to bottom
                this.systemLogsEl.scrollTop = this.systemLogsEl.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading logs:', error);
            this.systemLogsEl.textContent = 'Failed to load logs';
        }
    }
    
    async startService() {
        try {
            const response = await fetch('/api/system/start', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showNotification('Display service started', 'success');
                // Reload system info after a short delay
                setTimeout(() => this.loadSystemInfo(), 2000);
            } else {
                this.showNotification(`Failed to start service: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error starting service:', error);
            this.showNotification('Failed to start display service', 'error');
        }
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        const parts = [];
        if (days > 0) parts.push(`${days}d`);
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        
        return parts.join(' ') || '< 1m';
    }
    
    populateTimezones() {
        // Common timezones
        const timezones = [
            'UTC',
            'America/New_York',
            'America/Chicago',
            'America/Denver',
            'America/Los_Angeles',
            'America/Toronto',
            'America/Vancouver',
            'America/Mexico_City',
            'America/Sao_Paulo',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Europe/Moscow',
            'Asia/Dubai',
            'Asia/Kolkata',
            'Asia/Shanghai',
            'Asia/Tokyo',
            'Asia/Seoul',
            'Australia/Sydney',
            'Australia/Melbourne',
            'Pacific/Auckland'
        ];
        
        // Clear existing options
        this.timezone.innerHTML = '';
        
        // Add timezone options
        timezones.forEach(tz => {
            const option = document.createElement('option');
            option.value = tz;
            option.textContent = tz.replace(/_/g, ' ');
            this.timezone.appendChild(option);
        });
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to notifications container
        this.notifications.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}