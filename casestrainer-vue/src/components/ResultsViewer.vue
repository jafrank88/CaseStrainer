<template>
  <div class="results-viewer">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div class="view-title">
        <h5 class="mb-0">
          <i class="fas" :class="viewIcon"></i>
          {{ viewTitle }}
          <span v-if="isNewView" class="badge bg-primary ms-2">New</span>
        </h5>
        <small class="text-muted">{{ viewDescription }}</small>
      </div>
      
      <div class="btn-group" role="group" aria-label="View mode">
        <button
          v-for="view in viewModes"
          :key="view.id"
          class="btn"
          :class="getButtonClass(view.id)"
          @click="setViewMode(view.id)"
          :title="view.description"
          data-bs-toggle="tooltip"
          data-bs-placement="bottom"
        >
          <i :class="view.icon"></i>
          {{ view.label }}
        </button>
      </div>
    </div>

    <div class="view-container">
      <CitationResults v-if="viewMode === 'citation'" :results="results" />
      <ReusableResults v-else :results="results" />
    </div>
    
    <!-- View Info Modal -->
    <div class="modal fade" id="viewInfoModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i :class="currentView.icon"></i>
              {{ currentView.label }} View
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>{{ currentView.description }}</p>
            <div v-if="currentView.id === 'citation'" class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              Try the new Citation View and provide feedback!
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { Modal, Tooltip } from 'bootstrap';
import CitationResults from './CitationResults.vue';
import ReusableResults from './ReusableResults.vue';

const STORAGE_KEY = 'caseStrainerResultsView';
const VIEW_MODES = {
  reusable: {
    id: 'reusable',
    label: 'Classic',
    icon: 'fas fa-table',
    description: 'Original view with detailed citation analysis',
    isNew: false
  },
  citation: {
    id: 'citation',
    label: 'Citation',
    icon: 'fas fa-list-check',
    description: 'New streamlined view focusing on citation verification',
    isNew: true
  }
};

export default {
  name: 'ResultsViewer',
  components: {
    CitationResults,
    ReusableResults
  },
  props: {
    results: {
      type: Object,
      required: true
    },
    defaultView: {
      type: String,
      default: 'citation',
      validator: value => Object.keys(VIEW_MODES).includes(value)
    }
  },
  setup(props) {
    const viewMode = ref(props.defaultView);
    let tooltips = [];

    // Initialize from localStorage or use default
    const loadViewPreference = () => {
      try {
        const savedView = localStorage.getItem(STORAGE_KEY);
        if (savedView && VIEW_MODES[savedView]) {
          viewMode.value = savedView;
        }
      } catch (e) {
        console.warn('Failed to load view preference:', e);
      }
    };

    // Save preference to localStorage
    const saveViewPreference = (mode) => {
      try {
        localStorage.setItem(STORAGE_KEY, mode);
      } catch (e) {
        console.warn('Failed to save view preference:', e);
      }
    };

    const setViewMode = (mode) => {
      if (viewMode.value !== mode) {
        viewMode.value = mode;
        saveViewPreference(mode);
        showViewInfo(mode);
      }
    };

    const showViewInfo = (mode) => {
      if (mode === 'citation') {
        const modalElement = document.getElementById('viewInfoModal');
        if (modalElement) {
          const modal = new Modal(modalElement);
          modal.show();
        }
      }
    };

    const currentView = computed(() => VIEW_MODES[viewMode.value] || VIEW_MODES.reusable);
    const viewModes = computed(() => Object.values(VIEW_MODES));
    const isNewView = computed(() => currentView.value.isNew);
    const viewTitle = computed(() => `${currentView.value.label} View`);
    const viewIcon = computed(() => currentView.value.icon);
    const viewDescription = computed(() => currentView.value.description);

    const getButtonClass = (mode) => ({
      'btn-outline-primary': viewMode.value === mode,
      'btn-outline-secondary': viewMode.value !== mode,
      'position-relative': VIEW_MODES[mode].isNew
    });

    // Initialize tooltips
    const initTooltips = () => {
      tooltips = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        .map(el => new Tooltip(el));
    };

    // Cleanup tooltips
    const destroyTooltips = () => {
      tooltips.forEach(tooltip => tooltip.dispose());
      tooltips = [];
    };

    onMounted(() => {
      loadViewPreference();
      initTooltips();
      
      // Show info for citation view on first load
      const hasSeenInfo = sessionStorage.getItem('hasSeenCitationInfo');
      if (viewMode.value === 'citation' && !hasSeenInfo) {
        showViewInfo('citation');
        sessionStorage.setItem('hasSeenCitationInfo', 'true');
      }
    });

    return {
      viewMode,
      viewModes,
      currentView,
      isNewView,
      viewTitle,
      viewIcon,
      viewDescription,
      setViewMode,
      getButtonClass,
      initTooltips,
      destroyTooltips
    };
  },
  beforeUnmount() {
    this.destroyTooltips();
  },
  updated() {
    this.initTooltips();
  }
};
</script>

<style scoped>
.results-viewer {
  margin-top: 1.5rem;
  background: #fff;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.view-title h5 {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #2c3e50;
}

.view-title small {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.85rem;
}

.btn-group {
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn {
  position: relative;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn i {
  font-size: 1rem;
}

.btn-outline-primary {
  color: #0d6efd;
  border-color: #dee2e6;
}

.btn-outline-primary:hover,
.btn-outline-primary.active {
  background-color: #0d6efd;
  color: white;
  border-color: #0d6efd;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #dee2e6;
}

.btn-outline-secondary:hover {
  background-color: #f8f9fa;
  color: #0d6efd;
}

.badge {
  font-size: 0.65rem;
  padding: 0.25rem 0.5rem;
  position: absolute;
  top: -8px;
  right: -8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.view-container {
  margin-top: 1.5rem;
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  overflow: hidden;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .results-viewer {
    padding: 1rem;
  }
  
  .view-title h5 {
    font-size: 1.1rem;
  }
  
  .btn {
    padding: 0.4rem 0.75rem;
    font-size: 0.85rem;
  }
  
  .btn i {
    font-size: 0.9rem;
  }
}
</style>
