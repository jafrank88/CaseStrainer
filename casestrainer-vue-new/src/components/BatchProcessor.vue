<template>
  <div class="batch-processor">
    <div class="batch-header">
      <h4>Batch Processing</h4>
      <p class="text-muted">Process multiple documents with progress tracking and notifications</p>
    </div>
    
    <!-- File Upload Area -->
    <div class="upload-section" v-if="!isProcessing">
      <div class="upload-area" @drop="handleDrop" @dragover.prevent @dragenter.prevent>
        <div class="upload-content">
          <div class="upload-icon">📁</div>
          <h5>Drop files here or click to browse</h5>
          <p>Support for PDF, DOCX, TXT, and RTF files</p>
          <input 
            ref="fileInput" 
            type="file" 
            multiple 
            accept=".pdf,.docx,.txt,.rtf"
            @change="handleFileSelect"
            style="display: none;"
          />
          <button @click="$refs.fileInput.click()" class="btn btn-primary">
            Select Files
          </button>
        </div>
      </div>
      
      <!-- Selected Files List -->
      <div v-if="selectedFiles.length > 0" class="selected-files">
        <h5>Selected Files ({{ selectedFiles.length }})</h5>
        <div class="file-list">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <button @click="removeFile(index)" class="remove-btn">✕</button>
          </div>
        </div>
        
        <!-- Processing Options -->
        <div class="processing-options">
          <h5>Processing Options</h5>
          <div class="options-grid">
            <div class="option-group">
              <label>Processing Mode:</label>
              <select v-model="processingMode" class="option-select">
                <option value="sequential">Sequential (One by one)</option>
                <option value="parallel">Parallel (Up to 3 files)</option>
                <option value="background">Background (Email notification)</option>
              </select>
            </div>
            
            <div class="option-group">
              <label>Priority Level:</label>
              <select v-model="priorityLevel" class="option-select">
                <option value="low">Low Priority</option>
                <option value="normal">Normal Priority</option>
                <option value="high">High Priority</option>
              </select>
            </div>
            
            <div class="option-group">
              <label>Email Notification:</label>
              <div class="checkbox-group">
                <label class="checkbox-item">
                  <input type="checkbox" v-model="emailNotification" />
                  <span class="checkmark"></span>
                  Send email when complete
                </label>
              </div>
            </div>
            
            <div class="option-group" v-if="emailNotification">
              <label>Email Address:</label>
              <input 
                v-model="emailAddress" 
                type="email" 
                placeholder="your@email.com"
                class="email-input"
              />
            </div>
          </div>
        </div>
        
        <!-- Start Processing -->
        <div class="start-processing">
          <button @click="startProcessing" class="btn btn-success" :disabled="!canStart">
            Start Processing ({{ selectedFiles.length }} files)
          </button>
          <div class="estimated-time" v-if="estimatedTime">
            Estimated time: {{ estimatedTime }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Processing Progress -->
    <div v-if="isProcessing" class="processing-section">
      <div class="processing-header">
        <h5>Processing Files</h5>
        <button @click="pauseProcessing" class="btn btn-warning" v-if="!isPaused">
          Pause
        </button>
        <button @click="resumeProcessing" class="btn btn-success" v-if="isPaused">
          Resume
        </button>
        <button @click="cancelProcessing" class="btn btn-danger">
          Cancel
        </button>
      </div>
      
      <!-- Overall Progress -->
      <div class="overall-progress">
        <div class="progress-info">
          <span class="progress-text">
            Overall Progress: {{ processedCount }} of {{ totalFiles }} files
          </span>
          <span class="progress-percentage">{{ overallProgress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: overallProgress + '%' }"></div>
        </div>
        <div class="time-info">
          <span class="elapsed-time">Elapsed: {{ elapsedTime }}</span>
          <span class="remaining-time" v-if="remainingTime">Remaining: {{ remainingTime }}</span>
        </div>
      </div>
      
      <!-- Current File Progress -->
      <div v-if="currentFile" class="current-file">
        <div class="current-file-info">
          <span class="file-name">{{ currentFile.name }}</span>
          <span class="file-status">{{ currentFileStatus }}</span>
        </div>
        <div class="file-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: currentFileProgress + '%' }"></div>
          </div>
          <span class="progress-percentage">{{ currentFileProgress }}%</span>
        </div>
        <div class="file-details">
          <span class="citations-found" v-if="currentFileCitations">
            Citations found: {{ currentFileCitations }}
          </span>
          <span class="processing-step">{{ currentProcessingStep }}</span>
        </div>
      </div>
      
      <!-- Processing Queue -->
      <div class="processing-queue">
        <h6>Processing Queue</h6>
        <div class="queue-list">
          <div 
            v-for="(file, index) in processingQueue" 
            :key="file.id" 
            class="queue-item"
            :class="{ 
              'completed': file.status === 'completed',
              'processing': file.status === 'processing',
              'pending': file.status === 'pending',
              'error': file.status === 'error'
            }"
          >
            <div class="queue-item-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-status">{{ getStatusText(file.status) }}</span>
            </div>
            <div class="queue-item-progress" v-if="file.status === 'processing'">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: file.progress + '%' }"></div>
              </div>
            </div>
            <div class="queue-item-result" v-if="file.status === 'completed'">
              <span class="citations-count">{{ file.citationsCount }} citations</span>
              <button @click="viewResults(file)" class="btn btn-sm btn-primary">
                View Results
              </button>
            </div>
            <div class="queue-item-error" v-if="file.status === 'error'">
              <span class="error-message">{{ file.errorMessage }}</span>
              <button @click="retryFile(file)" class="btn btn-sm btn-secondary">
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Processing Complete -->
    <div v-if="isComplete" class="completion-section">
      <div class="completion-header">
        <div class="completion-icon">✅</div>
        <h5>Processing Complete!</h5>
        <p>All files have been processed successfully.</p>
      </div>
      
      <div class="completion-stats">
        <div class="stat-item">
          <span class="stat-label">Total Files:</span>
          <span class="stat-value">{{ totalFiles }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Successfully Processed:</span>
          <span class="stat-value">{{ successfulCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Total Citations Found:</span>
          <span class="stat-value">{{ totalCitations }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Total Processing Time:</span>
          <span class="stat-value">{{ totalProcessingTime }}</span>
        </div>
      </div>
      
      <div class="completion-actions">
        <button @click="downloadBatchResults" class="btn btn-primary">
          Download All Results
        </button>
        <button @click="startNewBatch" class="btn btn-secondary">
          Process More Files
        </button>
        <button @click="viewBatchSummary" class="btn btn-success">
          View Summary
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BatchProcessor',
  data() {
    return {
      selectedFiles: [],
      isProcessing: false,
      isPaused: false,
      isComplete: false,
      processingMode: 'sequential',
      priorityLevel: 'normal',
      emailNotification: false,
      emailAddress: '',
      
      // Progress tracking
      processedCount: 0,
      totalFiles: 0,
      currentFile: null,
      currentFileProgress: 0,
      currentFileStatus: '',
      currentFileCitations: 0,
      currentProcessingStep: '',
      
      // Time tracking
      startTime: null,
      elapsedTime: '00:00:00',
      remainingTime: '',
      estimatedTime: '',
      
      // Processing queue
      processingQueue: [],
      
      // Results
      batchResults: [],
      totalCitations: 0,
      successfulCount: 0,
      totalProcessingTime: ''
    };
  },
  computed: {
    overallProgress() {
      if (this.totalFiles === 0) return 0;
      return Math.round((this.processedCount / this.totalFiles) * 100);
    },
    
    canStart() {
      return this.selectedFiles.length > 0 && 
             (!this.emailNotification || this.emailAddress);
    }
  },
  methods: {
    handleDrop(event) {
      event.preventDefault();
      const files = Array.from(event.dataTransfer.files);
      this.addFiles(files);
    },
    
    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.addFiles(files);
    },
    
    addFiles(files) {
      const validFiles = files.filter(file => {
        const validTypes = ['.pdf', '.docx', '.txt', '.rtf'];
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return validTypes.includes(extension);
      });
      
      this.selectedFiles.push(...validFiles);
      this.updateEstimatedTime();
    },
    
    removeFile(index) {
      this.selectedFiles.splice(index, 1);
      this.updateEstimatedTime();
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    updateEstimatedTime() {
      const avgTimePerFile = 30; // seconds
      const totalSeconds = this.selectedFiles.length * avgTimePerFile;
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      
      if (hours > 0) {
        this.estimatedTime = `${hours}h ${minutes}m`;
      } else {
        this.estimatedTime = `${minutes}m`;
      }
    },
    
    async startProcessing() {
      this.isProcessing = true;
      this.isComplete = false;
      this.startTime = Date.now();
      this.totalFiles = this.selectedFiles.length;
      this.processedCount = 0;
      
      // Initialize processing queue
      this.processingQueue = this.selectedFiles.map((file, index) => ({
        id: Date.now() + index,
        name: file.name,
        file: file,
        status: 'pending',
        progress: 0,
        citationsCount: 0,
        errorMessage: ''
      }));
      
      // Start processing based on mode
      if (this.processingMode === 'background') {
        this.startBackgroundProcessing();
      } else {
        this.startForegroundProcessing();
      }
      
      // Start time tracking
      this.startTimeTracking();
    },
    
    async startForegroundProcessing() {
      const maxConcurrent = this.processingMode === 'parallel' ? 3 : 1;
      const pendingFiles = [...this.processingQueue];
      
      while (pendingFiles.length > 0 && !this.isPaused) {
        const batch = pendingFiles.splice(0, maxConcurrent);
        const promises = batch.map(file => this.processFile(file));
        
        await Promise.all(promises);
      }
      
      if (!this.isPaused) {
        this.completeProcessing();
      }
    },
    
    startBackgroundProcessing() {
      // Simulate background processing
      this.currentFileStatus = 'Queued for background processing';
      this.currentProcessingStep = 'Files will be processed in the background';
      
      // In a real implementation, this would send the files to a backend queue
      setTimeout(() => {
        this.completeProcessing();
      }, 5000);
    },
    
    async processFile(file) {
      file.status = 'processing';
      this.currentFile = file;
      this.currentFileProgress = 0;
      this.currentFileStatus = 'Processing...';
      
      try {
        // Simulate file processing steps
        await this.simulateProcessingSteps(file);
        
        file.status = 'completed';
        file.progress = 100;
        this.processedCount++;
        this.successfulCount++;
        
        // Simulate citation extraction
        const citationsCount = Math.floor(Math.random() * 20) + 5;
        file.citationsCount = citationsCount;
        this.totalCitations += citationsCount;
        
        this.batchResults.push({
          fileName: file.name,
          citationsCount,
          processingTime: this.getProcessingTime(),
          status: 'success'
        });
        
      } catch (error) {
        file.status = 'error';
        file.errorMessage = error.message;
        this.batchResults.push({
          fileName: file.name,
          error: error.message,
          status: 'error'
        });
      }
    },
    
    async simulateProcessingSteps(file) {
      const steps = [
        'Uploading file...',
        'Extracting text...',
        'Detecting citations...',
        'Verifying citations...',
        'Generating results...'
      ];
      
      for (let i = 0; i < steps.length; i++) {
        if (this.isPaused) {
          throw new Error('Processing paused');
        }
        
        this.currentProcessingStep = steps[i];
        this.currentFileProgress = ((i + 1) / steps.length) * 100;
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
      }
    },
    
    pauseProcessing() {
      this.isPaused = true;
      this.currentFileStatus = 'Paused';
    },
    
    resumeProcessing() {
      this.isPaused = false;
      this.startForegroundProcessing();
    },
    
    cancelProcessing() {
      this.isProcessing = false;
      this.isPaused = false;
      this.resetState();
    },
    
    completeProcessing() {
      this.isProcessing = false;
      this.isComplete = true;
      this.totalProcessingTime = this.getProcessingTime();
      
      if (this.emailNotification && this.emailAddress) {
        this.sendCompletionEmail();
      }
      
      this.$emit('batch-complete', {
        results: this.batchResults,
        stats: {
          totalFiles: this.totalFiles,
          successfulCount: this.successfulCount,
          totalCitations: this.totalCitations,
          processingTime: this.totalProcessingTime
        }
      });
    },
    
    startTimeTracking() {
      const timer = setInterval(() => {
        if (!this.isProcessing || this.isComplete) {
          clearInterval(timer);
          return;
        }
        
        const elapsed = Date.now() - this.startTime;
        this.elapsedTime = this.formatTime(elapsed);
        
        // Calculate remaining time
        if (this.processedCount > 0) {
          const avgTimePerFile = elapsed / this.processedCount;
          const remainingFiles = this.totalFiles - this.processedCount;
          const remaining = avgTimePerFile * remainingFiles;
          this.remainingTime = this.formatTime(remaining);
        }
      }, 1000);
    },
    
    formatTime(milliseconds) {
      const seconds = Math.floor(milliseconds / 1000);
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;
      
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    
    getProcessingTime() {
      if (!this.startTime) return '00:00:00';
      return this.formatTime(Date.now() - this.startTime);
    },
    
    getStatusText(status) {
      const statusMap = {
        pending: 'Pending',
        processing: 'Processing',
        completed: 'Completed',
        error: 'Error'
      };
      return statusMap[status] || status;
    },
    
    viewResults(file) {
      this.$emit('view-results', file);
    },
    
    retryFile(file) {
      file.status = 'pending';
      file.progress = 0;
      file.errorMessage = '';
      this.processFile(file);
    },
    
    downloadBatchResults() {
      const exportData = {
        timestamp: new Date().toISOString(),
        batchResults: this.batchResults,
        stats: {
          totalFiles: this.totalFiles,
          successfulCount: this.successfulCount,
          totalCitations: this.totalCitations,
          processingTime: this.totalProcessingTime
        }
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_results_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    
    startNewBatch() {
      this.resetState();
    },
    
    viewBatchSummary() {
      this.$emit('view-summary', {
        results: this.batchResults,
        stats: {
          totalFiles: this.totalFiles,
          successfulCount: this.successfulCount,
          totalCitations: this.totalCitations,
          processingTime: this.totalProcessingTime
        }
      });
    },
    
    sendCompletionEmail() {
      // In a real implementation, this would call your backend API
      console.log('Sending completion email to:', this.emailAddress);
    },
    
    resetState() {
      this.selectedFiles = [];
      this.isProcessing = false;
      this.isPaused = false;
      this.isComplete = false;
      this.processedCount = 0;
      this.totalFiles = 0;
      this.currentFile = null;
      this.currentFileProgress = 0;
      this.currentFileStatus = '';
      this.currentFileCitations = 0;
      this.currentProcessingStep = '';
      this.processingQueue = [];
      this.batchResults = [];
      this.totalCitations = 0;
      this.successfulCount = 0;
      this.totalProcessingTime = '';
      this.startTime = null;
      this.elapsedTime = '00:00:00';
      this.remainingTime = '';
    }
  }
};
</script>

<style scoped>
.batch-processor {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.batch-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 1rem;
}

.batch-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.upload-section {
  margin-bottom: 2rem;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
}

.upload-area:hover {
  border-color: #1976d2;
  background: #f8f9fa;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  font-size: 3rem;
}

.upload-content h5 {
  margin: 0;
  color: #333;
}

.upload-content p {
  margin: 0;
  color: #666;
}

.selected-files {
  margin-top: 1.5rem;
}

.selected-files h5 {
  margin: 0 0 1rem 0;
  color: #333;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-weight: 500;
  color: #333;
}

.file-size {
  font-size: 0.8rem;
  color: #666;
}

.remove-btn {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.25rem;
}

.remove-btn:hover {
  color: #c82333;
}

.processing-options {
  border-top: 1px solid #e0e0e0;
  padding-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.processing-options h5 {
  margin: 0 0 1rem 0;
  color: #333;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-group label {
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.option-select,
.email-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.option-select:focus,
.email-input:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-item input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 16px;
  height: 16px;
  border: 2px solid #ddd;
  border-radius: 3px;
  position: relative;
  transition: all 0.2s;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark {
  background: #1976d2;
  border-color: #1976d2;
}

.checkbox-item input[type="checkbox"]:checked + .checkmark::after {
  content: '✓';
  position: absolute;
  top: -2px;
  left: 1px;
  color: white;
  font-size: 12px;
}

.start-processing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.estimated-time {
  font-size: 0.9rem;
  color: #666;
}

.processing-section {
  margin-bottom: 2rem;
}

.processing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.processing-header h5 {
  margin: 0;
  color: #333;
}

.overall-progress {
  margin-bottom: 1.5rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-text {
  font-weight: 500;
  color: #333;
}

.progress-percentage {
  font-weight: bold;
  color: #1976d2;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #1976d2;
  transition: width 0.3s ease;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
}

.current-file {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.current-file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.current-file-info .file-name {
  font-weight: 500;
  color: #333;
}

.current-file-info .file-status {
  font-size: 0.9rem;
  color: #666;
}

.file-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.file-progress .progress-bar {
  flex: 1;
  margin-bottom: 0;
}

.file-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
}

.processing-queue {
  border-top: 1px solid #e0e0e0;
  padding-top: 1.5rem;
}

.processing-queue h6 {
  margin: 0 0 1rem 0;
  color: #333;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 4px;
  border-left: 4px solid #ddd;
}

.queue-item.pending {
  background: #f8f9fa;
  border-left-color: #6c757d;
}

.queue-item.processing {
  background: #e3f2fd;
  border-left-color: #1976d2;
}

.queue-item.completed {
  background: #e8f5e8;
  border-left-color: #28a745;
}

.queue-item.error {
  background: #fde8e8;
  border-left-color: #dc3545;
}

.queue-item-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.queue-item-info .file-name {
  font-weight: 500;
  color: #333;
}

.queue-item-info .file-status {
  font-size: 0.8rem;
  color: #666;
}

.queue-item-progress {
  flex: 1;
  margin: 0 1rem;
}

.queue-item-result,
.queue-item-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.citations-count {
  color: #28a745;
  font-weight: 500;
}

.error-message {
  color: #dc3545;
}

.completion-section {
  text-align: center;
  padding: 2rem;
}

.completion-header {
  margin-bottom: 2rem;
}

.completion-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.completion-header h5 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.completion-header p {
  margin: 0;
  color: #666;
}

.completion-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.stat-value {
  font-weight: bold;
  color: #333;
}

.completion-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-warning:hover {
  background: #e0a800;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .batch-processor {
    padding: 0 1rem;
  }
  
  .batch-header {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  
  .batch-header h4 {
    font-size: 1.5rem;
  }
  
  .batch-header p {
    font-size: 0.9rem;
  }
  
  /* Upload section */
  .upload-area {
    padding: 2rem 1rem;
  }
  
  .upload-content h5 {
    font-size: 1.1rem;
  }
  
  .upload-content p {
    font-size: 0.9rem;
  }
  
  .btn {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    min-height: 44px;
  }
  
  /* Selected files */
  .selected-files {
    padding: 1rem;
  }
  
  .file-list {
    gap: 0.75rem;
  }
  
  .file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
  }
  
  .file-info {
    width: 100%;
  }
  
  .remove-btn {
    align-self: flex-end;
    padding: 0.5rem 0.75rem;
    min-height: 36px;
  }
  
  /* Processing options */
  .processing-options {
    padding: 1rem;
  }
  
  .options-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .option-group {
    gap: 0.5rem;
  }
  
  .option-select,
  .email-input {
    font-size: 16px; /* Prevent zoom on mobile */
    padding: 0.75rem;
  }
  
  .checkbox-item {
    padding: 0.5rem 0;
    font-size: 0.9rem;
  }
  
  /* Processing section */
  .processing-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .processing-header .btn {
    width: 100%;
  }
  
  .overall-progress {
    padding: 1rem;
  }
  
  .progress-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .time-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .current-file {
    padding: 1rem;
  }
  
  .current-file-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .file-details {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  /* Processing queue */
  .processing-queue {
    padding: 1rem;
  }
  
  .queue-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
  }
  
  .queue-item-info {
    width: 100%;
  }
  
  .queue-item-progress {
    width: 100%;
    margin: 0;
  }
  
  .queue-item-result,
  .queue-item-error {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .queue-item-result .btn,
  .queue-item-error .btn {
    width: 100%;
  }
  
  /* Completion section */
  .completion-section {
    padding: 1.5rem;
  }
  
  .completion-stats {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .stat-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    text-align: left;
  }
  
  .completion-actions {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .completion-actions .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .batch-processor {
    padding: 0 0.5rem;
  }
  
  .upload-area {
    padding: 1.5rem 0.75rem;
  }
  
  .upload-content h5 {
    font-size: 1rem;
  }
  
  .upload-content p {
    font-size: 0.85rem;
  }
  
  .selected-files,
  .processing-options,
  .overall-progress,
  .current-file,
  .processing-queue {
    padding: 0.75rem;
  }
  
  .file-item {
    padding: 0.5rem;
  }
  
  .option-select,
  .email-input {
    padding: 0.5rem;
    font-size: 16px;
  }
  
  .queue-item {
    padding: 0.75rem;
  }
  
  .completion-section {
    padding: 1rem;
  }
  
  .completion-icon {
    font-size: 2.5rem;
  }
  
  .completion-header h5 {
    font-size: 1.2rem;
  }
  
  .completion-header p {
    font-size: 0.9rem;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .btn,
  .remove-btn,
  .checkbox-item {
    min-height: 44px;
  }
  
  .option-select,
  .email-input {
    min-height: 44px;
  }
  
  /* Remove hover effects on touch devices */
  .btn:hover,
  .remove-btn:hover {
    transform: none;
  }
}
</style> 