<template>
  <div v-if="hasRecentInputs" class="recent-inputs-section">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <label class="form-label mb-0">
        <i class="bi bi-clock-history me-2"></i>
        Recent Inputs
      </label>
      <button 
        @click="clearAll"
        class="btn btn-sm btn-outline-secondary"
        title="Clear all recent inputs"
      >
        <i class="bi bi-trash me-1"></i>
        Clear All
      </button>
    </div>
    
    <div class="recent-inputs">
      <div 
        v-for="(input, index) in recentInputs" 
        :key="`${input.tab}-${input.timestamp}-${index}`"
        class="recent-input-item"
        @click="loadInput(input)"
      >
        <div class="recent-input-content">
          <div class="recent-input-header">
            <div class="recent-input-title">
              <i :class="getInputIcon(input.tab)" class="me-2"></i>
              {{ getInputTitle(input) }}
            </div>
            <div class="recent-input-time">
              {{ formatTimestamp(input.timestamp) }}
            </div>
          </div>
          <div class="recent-input-preview">{{ getInputPreview(input) }}</div>
        </div>
        <div class="recent-input-actions">
          <button 
            @click.stop="removeInput(index)"
            class="btn btn-sm btn-outline-danger"
            title="Remove from history"
          >
            <i class="bi bi-x"></i>
          </button>
        </div>
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

const loadInput = (input) => {
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
.recent-inputs-section {
  margin-bottom: 1.5rem;
}

.recent-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.recent-input-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  text-align: center;
}

.recent-input-item:hover {
  background: #e9ecef;
  border-color: #dee2e6;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.recent-input-content {
  flex: 1;
  min-width: 0;
}

.recent-input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.recent-input-title {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
}

.recent-input-time {
  font-size: 0.75rem;
  color: #6c757d;
}

.recent-input-preview {
  font-size: 0.85rem;
  color: #6c757d;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-input-actions {
  margin-left: 0.5rem;
}

.recent-input-actions .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .recent-input-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .recent-input-time {
    font-size: 0.7rem;
  }
  .recent-input-item {
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem 0.5rem;
    text-align: center;
  }
  .recent-input-actions {
    margin-left: 0;
    margin-top: 0.5rem;
  }
}
</style> 