<template>
  <div v-if="hasErrors" class="app-error-handler">
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      <h5 class="alert-heading">An error occurred</h5>
      <ul class="mb-0">
        <li v-for="(error, index) in errors" :key="index">
          {{ getErrorMessage(error) }}
          <button 
            type="button" 
            class="btn-close" 
            aria-label="Dismiss"
            @click="dismissError(index)"
          ></button>
        </li>
      </ul>
      <button 
        type="button" 
        class="btn-close" 
        aria-label="Close"
        @click="clearAllErrors"
      ></button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useLoadingState } from '@/utils/loading';

export default {
  name: 'AppErrorHandler',
  
  setup() {
    const { errors, clearErrors } = useLoadingState();
    
    const hasErrors = computed(() => errors.value.length > 0);
    
    function getErrorMessage(error) {
      if (!error) return 'An unknown error occurred';
      
      // Handle different error formats
      if (error.isAxiosError) {
        // Axios error
        const { response } = error;
        
        if (response) {
          // Server responded with error status
          const { status, data } = response;
          
          if (data && data.message) {
            return `[${status}] ${data.message}`;
          }
          
          switch (status) {
            case 400: return 'Bad request. Please check your input and try again.';
            case 401: return 'You need to be logged in to perform this action.';
            case 403: return 'You do not have permission to perform this action.';
            case 404: return 'The requested resource was not found.';
            case 429: return 'Too many requests. Please wait before trying again.';
            case 500: return 'An internal server error occurred. Please try again later.';
            default: return `An error occurred (${status}). Please try again.`;
          }
        } else if (error.request) {
          // No response received
          return 'Unable to connect to the server. Please check your internet connection.';
        }
      }
      
      // Generic error handling
      return error.message || 'An unexpected error occurred';
    }
    
    function dismissError(index) {
      if (errors.value[index]) {
        const newErrors = [...errors.value];
        newErrors.splice(index, 1);
        clearErrors();
        errors.value = newErrors;
      }
    }
    
    function clearAllErrors() {
      clearErrors();
    }
    
    return {
      errors,
      hasErrors,
      getErrorMessage,
      dismissError,
      clearAllErrors,
    };
  },
};
</script>

<style scoped>
.app-error-handler {
  position: fixed;
  top: 1rem;
  right: 1rem;
  max-width: 400px;
  z-index: 9999;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border-radius: 0.25rem;
}

.alert {
  margin-bottom: 0;
}

.alert ul {
  padding-left: 1.5rem;
  margin-bottom: 0;
}

.alert li {
  position: relative;
  padding-right: 2rem;
  margin-bottom: 0.5rem;
}

.alert li:last-child {
  margin-bottom: 0;
}

.btn-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.5rem;
  opacity: 0.5;
  transition: opacity 0.2s ease-in-out;
}

.btn-close:hover {
  opacity: 1;
}

.alert .btn-close {
  padding: 0.5rem 1rem;
}

/* Mobile Responsive Design */
@media (max-width: 768px) {
  .app-error-handler {
    position: fixed;
    top: 0.5rem;
    left: 0.5rem;
    right: 0.5rem;
    max-width: none;
    z-index: 9999;
  }
  
  .alert {
    padding: 0.75rem;
  }
  
  .alert-heading {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .alert ul {
    padding-left: 1rem;
  }
  
  .alert li {
    padding-right: 1.5rem;
    margin-bottom: 0.75rem;
    font-size: 0.9rem;
    line-height: 1.4;
  }
  
  .btn-close {
    top: 0.25rem;
    right: 0.25rem;
    padding: 0.375rem;
    min-height: 32px;
    min-width: 32px;
  }
  
  .alert .btn-close {
    padding: 0.375rem 0.75rem;
    min-height: 32px;
  }
}

@media (max-width: 480px) {
  .app-error-handler {
    top: 0.25rem;
    left: 0.25rem;
    right: 0.25rem;
  }
  
  .alert {
    padding: 0.5rem;
  }
  
  .alert-heading {
    font-size: 0.95rem;
  }
  
  .alert li {
    font-size: 0.85rem;
    padding-right: 1.25rem;
  }
  
  .btn-close {
    padding: 0.25rem;
    min-height: 28px;
    min-width: 28px;
  }
  
  .alert .btn-close {
    padding: 0.25rem 0.5rem;
    min-height: 28px;
  }
}

/* Touch-friendly improvements */
@media (hover: none) and (pointer: coarse) {
  .btn-close {
    min-height: 44px;
    min-width: 44px;
  }
  
  .alert .btn-close {
    min-height: 44px;
  }
  
  /* Remove hover effects on touch devices */
  .btn-close:hover {
    opacity: 0.5;
  }
}
</style>
