import { ref, computed } from 'vue'

// Global state for recent inputs
const recentInputs = ref([])
const isInitialized = ref(false)

// Storage key with user-specific prefix
const getStorageKey = () => {
  // For now, use a generic key. In a real app, you'd use the user's ID
  return 'casestrainer_recent_inputs'
}

// Initialize recent inputs from localStorage
const initializeRecentInputs = () => {
  if (isInitialized.value) return
  
  try {
    const saved = localStorage.getItem(getStorageKey())
    if (saved) {
      const parsed = JSON.parse(saved)
      // Validate the structure and filter out invalid entries
      recentInputs.value = parsed
        .filter(input => input && input.tab && input.timestamp)
        .slice(0, 10) // Keep last 10 instead of 5
    }
  } catch (error) {
    console.error('Error loading recent inputs:', error)
    // Clear corrupted data
    localStorage.removeItem(getStorageKey())
  }
  
  isInitialized.value = true
}

// Save recent inputs to localStorage
const saveRecentInputs = () => {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(recentInputs.value))
  } catch (error) {
    console.error('Error saving recent inputs:', error)
  }
}

// Add a new input to recent inputs
const addRecentInput = (inputData) => {
  // Ensure we have the required fields
  if (!inputData || !inputData.tab || !inputData.timestamp) {
    console.warn('Invalid input data:', inputData)
    return
  }
  
  // Remove duplicates based on content
  recentInputs.value = recentInputs.value.filter(input => {
    if (input.tab !== inputData.tab) return true
    
    switch (inputData.tab) {
      case 'paste':
        return input.text !== inputData.text
      case 'url':
        return input.url !== inputData.url
      case 'file':
        return input.fileName !== inputData.fileName
      default:
        return true
    }
  })
  
  // Add to beginning
  recentInputs.value.unshift(inputData)
  
  // Keep only last 10
  recentInputs.value = recentInputs.value.slice(0, 10)
  
  saveRecentInputs()
}

// Remove a recent input by index
const removeRecentInput = (index) => {
  if (index >= 0 && index < recentInputs.value.length) {
    recentInputs.value.splice(index, 1)
    saveRecentInputs()
  }
}

// Clear all recent inputs
const clearRecentInputs = () => {
  recentInputs.value = []
  saveRecentInputs()
}

// Get recent inputs for a specific tab
const getRecentInputsByTab = (tab) => {
  return recentInputs.value.filter(input => input.tab === tab)
}

// Get input icon class
const getInputIcon = (tab) => {
  switch (tab) {
    case 'paste': return 'bi bi-clipboard-text'
    case 'file': return 'bi bi-file-earmark-text'
    case 'url': return 'bi bi-link-45deg'
    default: return 'bi bi-question-circle'
  }
}

// Get input title
const getInputTitle = (input) => {
  switch (input.tab) {
    case 'paste': return 'Text Input'
    case 'file': return `File: ${input.fileName || 'Unknown'}`
    case 'url': return 'URL Input'
    default: return 'Unknown Input'
  }
}

// Get input preview text
const getInputPreview = (input) => {
  switch (input.tab) {
    case 'paste': 
      return input.text ? input.text.substring(0, 60) + (input.text.length > 60 ? '...' : '') : 'No text'
    case 'file': 
      return input.fileName || 'Unknown file'
    case 'url': 
      return input.url || 'No URL'
    default: 
      return 'Unknown input type'
  }
}

// Format timestamp
const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString()
  } catch {
    return 'Unknown time'
  }
}

// Computed properties
const hasRecentInputs = computed(() => recentInputs.value.length > 0)
const recentInputsCount = computed(() => recentInputs.value.length)

export function useRecentInputs() {
  // Initialize on first use
  if (!isInitialized.value) {
    initializeRecentInputs()
  }
  
  return {
    // State
    recentInputs: computed(() => recentInputs.value),
    hasRecentInputs,
    recentInputsCount,
    
    // Methods
    addRecentInput,
    removeRecentInput,
    clearRecentInputs,
    getRecentInputsByTab,
    getInputIcon,
    getInputTitle,
    getInputPreview,
    formatTimestamp,
    
    // Utility
    initializeRecentInputs
  }
} 