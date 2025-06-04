<template>
  <div class="not-found">
    <div class="container py-5">
      <div class="row justify-content-center">
        <div class="col-lg-8 text-center">
          <div class="error-404">
            <h1 class="display-1 fw-bold text-primary">404</h1>
            <h2 class="h3 mb-4">Page Not Found</h2>
            <p class="lead text-muted mb-5">
              Oops! The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
            </p>
            <div class="d-flex justify-content-center gap-3">
              <router-link to="/" class="btn btn-primary btn-lg">
                <i class="bi bi-house-door me-2"></i> Back to Home
              </router-link>
              <a href="#" class="btn btn-outline-secondary btn-lg" @click="goBack">
                <i class="bi bi-arrow-left me-2"></i> Go Back
              </a>
            </div>
          </div>
          
          <div class="mt-5 pt-5">
            <h3 class="h5 mb-3">Or try these helpful links:</h3>
            <div class="d-flex flex-wrap justify-content-center gap-3">
              <router-link to="/enhanced-validator" class="btn btn-outline-primary">
                <i class="bi bi-shield-check me-2"></i> Enhanced Validator
              </router-link>
              <a href="#" class="btn btn-outline-secondary">
                <i class="bi bi-question-circle me-2"></i> Help Center
              </a>
              <a href="#" class="btn btn-outline-secondary">
                <i class="bi bi-envelope me-2"></i> Contact Support
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';

export default {
  name: 'NotFound',
  setup() {
    const router = useRouter();
    
    const goBack = () => {
      router.go(-1);
    };
    
    return {
      goBack
    };
  }
};
</script>

<style scoped>
.not-found {
  min-height: 70vh;
  display: flex;
  align-items: center;
}

.error-404 {
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 1rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.05);
}

h1 {
  font-size: 8rem;
  line-height: 1;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #0d6efd, #0a58ca);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}

h2 {
  font-weight: 600;
  color: #2c3e50;
}

.btn {
  min-width: 180px;
  margin: 0.5rem 0;
}

@media (max-width: 768px) {
  h1 {
    font-size: 5rem;
  }
  
  .btn {
    width: 100%;
  }
  
  .d-flex {
    flex-direction: column;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .error-404 {
    background-color: #2d2d2d;
  }
  
  h2 {
    color: #f8f9fa;
  }
  
  .text-muted {
    color: #adb5bd !important;
  }
  
  .btn-outline-secondary {
    border-color: #6c757d;
    color: #f8f9fa;
  }
  
  .btn-outline-secondary:hover {
    background-color: #6c757d;
    color: #fff;
  }
}
</style>
