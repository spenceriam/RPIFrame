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
        this.uptimeEl = document.getElementById('uptime');
        this.cpuTempEl = document.getElementById('cpu-temp');
        this.photoCountEl = document.getElementById('photo-count');
        this.lastUpdateEl = document.getElementById('last-update');
        this.systemLogsEl = document.getElementById('system-logs');
        this.refreshStatusBtn = document.getElementById('refresh-status');
        this.nextPhotoBtn = document.getElementById('next-photo');
        
        // Current photo preview elements
        this.currentPhotoInfo = document.getElementById('current-photo-info');
        this.currentPhotoImage = document.getElementById('current-photo-image');
        
        // Notifications
        this.notifications = document.getElementById('notifications');
    }
    
    init() {
        // Initialize tab navigation
        this.initTabs();
        
        // Initialize photo management
        this.initPhotoManagement();
        
        // Initialize current photo preview
        this.initCurrentPhotoPreview();
        
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
                this.loadCurrentPhoto();
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
        
        // Next photo button
        this.nextPhotoBtn.addEventListener('click', () => {
            this.nextPhoto();
        });
    }
    
    initCurrentPhotoPreview() {
        // Load current photo info when photos tab is loaded
        this.loadCurrentPhoto();
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
                
                // Update CPU usage
                if (status.cpu_usage) {
                    const cpuFill = document.querySelector('.cpu-fill');
                    const cpuText = document.querySelector('.cpu-text');
                    if (cpuFill && cpuText) {
                        cpuFill.style.width = status.cpu_usage.percent + '%';
                        cpuText.textContent = `${status.cpu_usage.percent.toFixed(1)}%`;
                        
                        // Color coding for CPU usage
                        cpuFill.className = 'cpu-fill';
                        if (status.cpu_usage.percent > 80) {
                            cpuFill.classList.add('high-usage');
                        } else if (status.cpu_usage.percent > 60) {
                            cpuFill.classList.add('medium-usage');
                        } else {
                            cpuFill.classList.add('low-usage');
                        }
                    }
                }
                
                // Update Memory usage
                if (status.memory_usage) {
                    const memoryFill = document.querySelector('.memory-fill');
                    const memoryText = document.querySelector('.memory-text');
                    if (memoryFill && memoryText) {
                        memoryFill.style.width = status.memory_usage.percent_used + '%';
                        memoryText.textContent = `${status.memory_usage.used} / ${status.memory_usage.total} (${status.memory_usage.percent_used}%)`;
                        
                        // Color coding for Memory usage
                        memoryFill.className = 'memory-fill';
                        if (status.memory_usage.percent_used > 80) {
                            memoryFill.classList.add('high-usage');
                        } else if (status.memory_usage.percent_used > 60) {
                            memoryFill.classList.add('medium-usage');
                        } else {
                            memoryFill.classList.add('low-usage');
                        }
                    }
                }
                
                // Display service status removed - if main service isn't running, web interface wouldn't be accessible
                
                // Update system information
                this.uptimeEl.textContent = this.formatUptime(status.uptime);
                this.cpuTempEl.textContent = status.cpu_temp;
                this.photoCountEl.textContent = status.photo_count;
                
                // Update overall health
                if (status.tech_stack && status.tech_stack.overall_health) {
                    const health = status.tech_stack.overall_health;
                    const overallHealthEl = document.getElementById('overall-health');
                    if (overallHealthEl) {
                        overallHealthEl.textContent = `${health.status} (${health.score}/${health.total_checks})`;
                        overallHealthEl.className = `info-value health-${health.status}`;
                    }
                }
                
                // Update tech stack information
                this.updateTechStack(status.tech_stack);
                
                // Update health checks
                this.updateHealthChecks(status.tech_stack);
                
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
    
    
    updateTechStack(techStack) {
        const container = document.getElementById('tech-stack');
        if (!container || !techStack) return;
        
        let html = '';
        
        // Core System
        if (techStack.core && techStack.core.rpiframe) {
            const rpi = techStack.core.rpiframe;
            html += `
                <div class="tech-section">
                    <h4>RPIFrame Core</h4>
                    <div class="tech-item">
                        <span class="tech-name">Version:</span>
                        <span class="tech-value">${rpi.version}</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-name">Status:</span>
                        <span class="tech-value status-${rpi.status}">${rpi.status}</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-name">Architecture:</span>
                        <span class="tech-value">${rpi.architecture}</span>
                    </div>
                </div>
            `;
        }
        
        // System Information
        if (techStack.system) {
            const sys = techStack.system;
            html += `
                <div class="tech-section">
                    <h4>System</h4>
                    <div class="tech-item">
                        <span class="tech-name">OS:</span>
                        <span class="tech-value">${sys.os}</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-name">Python:</span>
                        <span class="tech-value">${sys.python_version}</span>
                    </div>
                    <div class="tech-item">
                        <span class="tech-name">Architecture:</span>
                        <span class="tech-value">${sys.arch}</span>
                    </div>
                </div>
            `;
        }
        
        // Hardware
        if (techStack.hardware) {
            const hw = techStack.hardware;
            html += `
                <div class="tech-section">
                    <h4>Hardware</h4>
                    ${hw.model ? `
                        <div class="tech-item">
                            <span class="tech-name">Model:</span>
                            <span class="tech-value">${hw.model}</span>
                        </div>
                    ` : ''}
                    ${hw.dsi_display ? `
                        <div class="tech-item">
                            <span class="tech-name">DSI Display:</span>
                            <span class="tech-value status-${hw.dsi_display.status}">${hw.dsi_display.resolution || 'Unknown'}</span>
                        </div>
                    ` : ''}
                    ${hw.gpu_memory ? `
                        <div class="tech-item">
                            <span class="tech-name">GPU Memory:</span>
                            <span class="tech-value">${hw.gpu_memory}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        // Dependencies
        if (techStack.dependencies) {
            html += `
                <div class="tech-section">
                    <h4>Key Dependencies</h4>
            `;
            
            Object.entries(techStack.dependencies).forEach(([name, info]) => {
                html += `
                    <div class="tech-item">
                        <span class="tech-name">${name}:</span>
                        <span class="tech-value status-${info.status}">${info.version} - ${info.description}</span>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        container.innerHTML = html;
    }
    
    updateHealthChecks(techStack) {
        const container = document.getElementById('health-checks');
        if (!container || !techStack) return;
        
        let html = '';
        
        // Health Checks
        if (techStack.health_checks) {
            html += `
                <div class="health-section">
                    <h4>System Health</h4>
            `;
            
            Object.entries(techStack.health_checks).forEach(([name, check]) => {
                const statusIcon = check.status === 'ok' ? '✅' : 
                                 check.status === 'warning' ? '⚠️' : '❌';
                html += `
                    <div class="health-item">
                        <span class="health-indicator">${statusIcon}</span>
                        <span class="health-name">${name.replace('_', ' ')}:</span>
                        <span class="health-description">${check.description}</span>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // Recommendations
        if (techStack.recommendations && techStack.recommendations.length > 0) {
            html += `
                <div class="recommendations-section">
                    <h4>Recommendations</h4>
            `;
            
            techStack.recommendations.forEach(rec => {
                const priorityIcon = rec.priority === 'high' ? '🔴' :
                                   rec.priority === 'medium' ? '🟡' : '🔵';
                html += `
                    <div class="recommendation-item priority-${rec.priority}">
                        <span class="priority-indicator">${priorityIcon}</span>
                        <span class="recommendation-text">${rec.message}</span>
                    </div>
                `;
            });
            
            html += '</div>';
        } else {
            html += `
                <div class="recommendations-section">
                    <div class="no-recommendations">✅ No recommendations - system running optimally!</div>
                </div>
            `;
        }
        
        container.innerHTML = html;
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
    
    async loadCurrentPhoto() {
        try {
            const response = await fetch('/api/slideshow/current');
            if (response.ok) {
                const data = await response.json();
                console.log('Current photo API response:', data); // Debug log
                if (data.current_photo) {
                    this.currentPhotoInfo.textContent = `Currently showing: ${data.current_photo}`;
                    this.currentPhotoImage.src = `/photos/${data.current_photo}`;
                    this.currentPhotoImage.style.display = 'block';
                    console.log('Updated preview to:', data.current_photo); // Debug log
                } else {
                    this.currentPhotoInfo.textContent = 'No photo currently displayed';
                    this.currentPhotoImage.style.display = 'none';
                }
            } else {
                console.error('API response not ok:', response.status);
                this.currentPhotoInfo.textContent = 'Error loading current photo';
            }
        } catch (error) {
            console.error('Error loading current photo:', error);
            this.currentPhotoInfo.textContent = 'Unable to load current photo info';
            this.currentPhotoImage.style.display = 'none';
        }
    }
    
    async nextPhoto() {
        try {
            // Show loading state
            this.currentPhotoInfo.textContent = 'Changing photo...';
            this.nextPhotoBtn.disabled = true;
            this.nextPhotoBtn.textContent = 'Changing...';
            
            const response = await fetch('/api/slideshow/next', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Displaying next photo', 'success');
                
                // Try multiple times to get the updated photo info
                let attempts = 0;
                const maxAttempts = 5;
                const checkPhoto = async () => {
                    attempts++;
                    await this.loadCurrentPhoto();
                    
                    // If still loading or no change after multiple attempts, try again
                    if (attempts < maxAttempts && this.currentPhotoInfo.textContent.includes('Loading')) {
                        setTimeout(checkPhoto, 500);
                    }
                };
                
                // Start checking after a brief delay
                setTimeout(checkPhoto, 800);
            } else {
                this.showNotification('Failed to advance to next photo', 'error');
                this.currentPhotoInfo.textContent = 'Error changing photo';
            }
        } catch (error) {
            console.error('Error advancing to next photo:', error);
            this.showNotification('Error advancing to next photo', 'error');
            this.currentPhotoInfo.textContent = 'Error changing photo';
        } finally {
            // Re-enable button
            setTimeout(() => {
                this.nextPhotoBtn.disabled = false;
                this.nextPhotoBtn.textContent = 'Next Photo';
            }, 2000);
        }
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