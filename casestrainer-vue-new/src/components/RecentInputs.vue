<template>
  <div v-if="hasRecentInputs" class="recent-inputs-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">
        <i class="bi bi-clock-history me-2"></i>
        Recent Inputs
        <span class="badge bg-secondary ms-2">{{ recentInputsCount }}</span>
      </div>
      <button 
        @click="clearAll"
        class="btn btn-sm btn-outline-secondary"
        title="Clear all recent inputs"
      >
        <i class="bi bi-trash"></i>
      </button>
    </div>
    
    <div class="sidebar-content">
      <div class="recent-inputs-list">
        <div 
          v-for="(input, index) in recentInputs" 
          :key="`${input.tab}-${input.timestamp}-${index}`"
          class="recent-input-card"
          @click="loadInput(input)"
        >
          <div class="input-card-header">
            <div class="input-type-badge">
              <i :class="getInputIcon(input.tab)"></i>
              {{ getInputTypeLabel(input.tab) }}
            </div>
            <div class="input-time">
              {{ formatTimestamp(input.timestamp) }}
            </div>
          </div>
          
          <div class="input-card-content">
            <div class="input-title">{{ getInputTitle(input) }}</div>
            <div class="input-preview">{{ getInputPreview(input) }}</div>
            
            <!-- File-specific warning -->
            <div v-if="input.tab === 'file'" class="file-warning">
              <i class="bi bi-exclamation-triangle text-warning me-1"></i>
              <small>File will need to be re-uploaded</small>
            </div>
          </div>
          
          <div class="input-card-actions">
            <button 
              @click.stop="removeInput(index)"
              class="btn btn-sm btn-remove-purple"
              title="Remove from history"
            >
              <i class="bi bi-x"></i> Remove
            </button>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-if="!hasRecentInputs" class="empty-state">
        <i class="bi bi-clock-history text-muted"></i>
        <p class="text-muted">No recent inputs</p>
        <small class="text-muted">Your recent uploads and inputs will appear here</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRecentInputs } from '@/composables/useRecentInputs'

const props = defineProps({
  // Optional: filter by specific tab
  filterTab: {
    type: String,
    default: null
  },
  // Optional: maximum number to show
  maxItems: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['load-input'])

const {
  recentInputs,
  hasRecentInputs,
  recentInputsCount,
  removeRecentInput,
  clearRecentInputs,
  getInputIcon,
  getInputTitle,
  getInputPreview,
  formatTimestamp
} = useRecentInputs()

// Filter inputs if needed
const filteredInputs = computed(() => {
  let inputs = recentInputs.value
  
  if (props.filterTab) {
    inputs = inputs.filter(input => input.tab === props.filterTab)
  }
  
  return inputs.slice(0, props.maxItems)
})

const getInputTypeLabel = (tab) => {
  switch (tab) {
    case 'text': return 'Text'
    case 'file': return 'File'
    case 'url': return 'URL'
    case 'quick': return 'Citation'
    default: return 'Input'
  }
}

const loadInput = (input) => {
  // Show warning for files
  if (input.tab === 'file') {
    if (!confirm('This will restore the file name, but you\'ll need to re-upload the file. Continue?')) {
      return
    }
  }
  
  emit('load-input', input)
}

const removeInput = (index) => {
  // Find the actual index in the full array
  const actualIndex = recentInputs.value.findIndex(item => 
    item.tab === filteredInputs.value[index].tab &&
    item.timestamp === filteredInputs.value[index].timestamp
  )
  
  if (actualIndex !== -1) {
    removeRecentInput(actualIndex)
  }
}

const clearAll = () => {
  if (confirm('Are you sure you want to clear all recent inputs?')) {
    clearRecentInputs()
  }
}
</script>

<style scoped>
.recent-inputs-sidebar {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #ffffff;
  border-bottom: 1px solid #e9ecef;
}

.sidebar-title {
  font-weight: 600;
  color: #495057;
  font-size: 1rem;
  display: flex;
  align-items: center;
}

.sidebar-content {
  max-height: 400px;
  overflow-y: auto;
}

.recent-inputs-list {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.recent-input-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.recent-input-card:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.input-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.input-type-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.input-time {
  font-size: 0.7rem;
  color: #6c757d;
}

.input-card-content {
  flex: 1;
  min-width: 0;
}

.input-title {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.input-preview {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0.5rem;
}

.file-warning {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.7rem;
  color: #856404;
  display: flex;
  align-items: center;
}

.input-card-actions {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.recent-input-card:hover .input-card-actions {
  opacity: 1;
}

.input-card-actions .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: #6c757d;
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  display: block;
}

.empty-state p {
  margin: 0.5rem 0;
  font-weight: 500;
}

/* Scrollbar styling */
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Responsive design */
@media (max-width: 768px) {
  .recent-inputs-sidebar {
    margin-top: 1rem;
  }
  
  .sidebar-content {
    max-height: 300px;
  }
  
  .input-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .input-time {
    font-size: 0.65rem;
  }
}

/* Purple remove button style */
.btn-remove-purple {
  background: #a259e6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4em;
  transition: background 0.2s;
}
.btn-remove-purple:hover, .btn-remove-purple:focus {
  background: #7c3aed;
  color: #fff;
}
</style> 