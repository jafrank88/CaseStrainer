<template>
  <div class="home">
    <!-- Page Header -->
    <div class="bg-primary text-white py-3 mb-4">
      <div class="container">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center">
          <div class="mb-3 mb-md-0">
            <h1 class="h3 mb-0">CaseStrainer</h1>
            <p class="mb-0 small">Legal Citation Validation & Analysis</p>
          </div>
          <router-link to="/enhanced-validator" class="btn btn-light btn-sm">
            <i class="bi bi-shield-check me-1"></i> Enhanced Validator
          </router-link>
        </div>
      </div>
    </div>

    <!-- Quick Validator Section -->
    <div class="container mb-4">
      <div class="card shadow-sm">
        <div class="card-body p-3 p-md-4">
          <h2 class="h5 mb-3">Quick Citation Validator</h2>
          <div class="input-group">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Enter a legal citation (e.g., 347 U.S. 483)"
              v-model="quickCitation"
              @keyup.enter="validateCitation"
            >
            <button 
              class="btn btn-primary"
              @click="validateCitation"
              :disabled="!quickCitation.trim()"
              title="Validate Citation"
            >
              <i class="bi bi-search"></i>
              <span class="d-none d-sm-inline ms-1">Validate</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Cards Section -->
    <div class="container mb-5">
      <div class="row g-3 g-md-4">
        <div class="col-12 col-md-4">
          <div class="card h-100 border-0 shadow-sm hover-shadow transition-all action-card" @click="navigateTo('upload')" style="cursor: pointer;">
            <div class="card-body text-center p-3 p-md-4">
              <div class="bg-primary bg-opacity-10 text-primary rounded-circle p-3 d-inline-flex mb-3">
                <i class="bi bi-upload fs-2"></i>
              </div>
              <h3 class="h5 mb-2">Upload Document</h3>
              <p class="text-muted small mb-0">Upload a file to extract and validate citations</p>
              <span class="btn btn-link text-primary p-0 mt-2">Get Started <i class="bi bi-arrow-right ms-1"></i></span>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4">
          <div class="card h-100 border-0 shadow-sm hover-shadow transition-all action-card" @click="navigateTo('paste')" style="cursor: pointer;">
            <div class="card-body text-center p-3 p-md-4">
              <div class="bg-success bg-opacity-10 text-success rounded-circle p-3 d-inline-flex mb-3">
                <i class="bi bi-clipboard-text fs-2"></i>
              </div>
              <h3 class="h5 mb-2">Paste Text</h3>
              <p class="text-muted small mb-0">Paste your text to find and validate citations</p>
              <span class="btn btn-link text-success p-0 mt-2">Try Now <i class="bi bi-arrow-right ms-1"></i></span>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4">
          <div class="card h-100 border-0 shadow-sm hover-shadow transition-all action-card" @click="navigateTo('url')" style="cursor: pointer;">
            <div class="card-body text-center p-3 p-md-4">
              <div class="bg-info bg-opacity-10 text-info rounded-circle p-3 d-inline-flex mb-3">
                <i class="bi bi-link-45deg fs-2"></i>
              </div>
              <h3 class="h5 mb-2">Check URL</h3>
              <p class="text-muted small mb-0">Enter a URL to analyze web content for citations</p>
              <span class="btn btn-link text-info p-0 mt-2">Analyze <i class="bi bi-arrow-right ms-1"></i></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <section id="features" class="features py-5 bg-light">
      <div class="container">
        <div class="text-center mb-5">
          <span class="badge bg-primary-soft text-primary mb-3">Features</span>
          <h2 class="fw-bold mb-3">Powerful Tools for Legal Research</h2>
          <p class="text-muted lead">Streamline your legal research with our comprehensive suite of citation tools</p>
        </div>
        
        <div class="row g-4">
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-primary bg-opacity-10 text-primary mb-3">
                  <i class="bi bi-shield-check fs-1"></i>
                </div>
                <h3 class="h5">Citation Validation</h3>
                <p class="text-muted mb-0">Validate legal citations against standard formats and court databases with our advanced validation engine.</p>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-success bg-opacity-10 text-success mb-3">
                  <i class="bi bi-diagram-3 fs-1"></i>
                </div>
                <h3 class="h5">Citation Network</h3>
                <p class="text-muted mb-0">Visualize and analyze citation networks to understand case relationships and legal precedents.</p>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-info bg-opacity-10 text-info mb-3">
                  <i class="bi bi-file-earmark-text fs-1"></i>
                </div>
                <h3 class="h5">Document Analysis</h3>
                <p class="text-muted mb-0">Upload documents to automatically extract and validate all citations within your legal documents.</p>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-warning bg-opacity-10 text-warning mb-3">
                  <i class="bi bi-search fs-1"></i>
                </div>
                <h3 class="h5">Advanced Search</h3>
                <p class="text-muted mb-0">Powerful search capabilities to find relevant cases and legal documents quickly.</p>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-danger bg-opacity-10 text-danger mb-3">
                  <i class="bi bi-graph-up fs-1"></i>
                </div>
                <h3 class="h5">Analytics</h3>
                <p class="text-muted mb-0">Gain insights from your citation data with comprehensive analytics and reporting tools.</p>
              </div>
            </div>
          </div>
          
          <div class="col-md-6 col-lg-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body p-4">
                <div class="feature-icon bg-purple bg-opacity-10 text-purple mb-3">
                  <i class="bi bi-share fs-1"></i>
                </div>
                <h3 class="h5">Collaboration</h3>
                <p class="text-muted mb-0">Share and collaborate on legal research with your team members seamlessly.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- How It Works -->
    <section class="how-it-works py-5">
      <div class="container">
        <div class="text-center mb-5">
          <span class="badge bg-primary-soft text-primary mb-3">How It Works</span>
          <h2 class="fw-bold mb-3">Validate Citations in 3 Simple Steps</h2>
          <p class="text-muted lead">Get started with CaseStrainer in minutes</p>
        </div>
        
        <div class="row g-4">
          <div class="col-md-4">
            <div class="step-card text-center p-4">
              <div class="step-number bg-primary text-white rounded-circle mx-auto mb-3">1</div>
              <h3 class="h5">Enter Citation</h3>
              <p class="text-muted mb-0">Type or paste your legal citation into the validator.</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="step-card text-center p-4">
              <div class="step-number bg-primary text-white rounded-circle mx-auto mb-3">2</div>
              <h3 class="h5">Analyze</h3>
              <p class="text-muted mb-0">Our system validates the citation against legal databases.</p>
            </div>
          </div>
          <div class="col-md-4">
            <div class="step-card text-center p-4">
              <div class="step-number bg-primary text-white rounded-circle mx-auto mb-3">3</div>
              <h3 class="h5">Get Results</h3>
              <p class="text-muted mb-0">Receive detailed information and validation results instantly.</p>
            </div>
          </div>
        </div>
        
        <div class="text-center mt-5">
          <router-link to="/enhanced-validator" class="btn btn-primary btn-lg">
            <i class="bi bi-shield-check me-2"></i> Try Enhanced Validator Now
          </router-link>
        </div>
      </div>
    </section>
    
    <!-- CTA Section -->
    <section class="cta py-5 bg-primary text-white">
      <div class="container text-center">
        <h2 class="fw-bold mb-4">Ready to Streamline Your Legal Research?</h2>
        <p class="lead mb-4">Join thousands of legal professionals who trust CaseStrainer for accurate citation validation and analysis.</p>
        <div class="d-flex justify-content-center gap-3">
          <router-link to="/enhanced-validator" class="btn btn-light btn-lg">
            <i class="bi bi-shield-check me-2"></i> Get Started Free
          </router-link>
          <a href="#" class="btn btn-outline-light btn-lg">
            <i class="bi bi-book me-2"></i> View Documentation
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'HomeView',
  setup() {
    const router = useRouter();
    const quickCitation = ref('');

    const validateCitation = () => {
      if (quickCitation.value.trim()) {
        navigateTo('validate', { citation: quickCitation.value.trim() });
      }
    };

    const navigateTo = (action, params = {}) => {
      switch (action) {
        case 'upload':
          router.push({ path: '/enhanced-validator', query: { tab: 'document' } });
          break;
        case 'paste':
          router.push({ path: '/enhanced-validator', query: { tab: 'text' } });
          break;
        case 'url':
          router.push({ path: '/enhanced-validator', query: { tab: 'url' } });
          break;
        case 'validate':
          router.push({ 
            path: '/enhanced-validator', 
            query: { 
              citation: params.citation,
              tab: 'single'
            } 
          });
          break;
        default:
          router.push('/enhanced-validator');
      }
    };

    return {
      quickCitation,
      validateCitation,
      navigateTo
    };
  }
}
</script>

<style scoped>
/* Hover effects for action cards */
.hover-shadow {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover-shadow:hover {
  transform: translateY(-5px);
  box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.1) !important;
}

.transition-all {
  transition: all 0.2s ease;
}

/* Custom colors */
.bg-primary-soft {
  background-color: rgba(13, 110, 253, 0.1) !important;
}

.bg-purple {
  color: #6f42c1;
}

/* Hero section */
.hero {
  background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
  border-radius: 0.5rem;
  margin: -1.5rem 0 2rem;
  overflow: hidden;
  position: relative;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.hero .container {
  position: relative;
  z-index: 1;
}

.hero-image {
  position: relative;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
  100% { transform: translateY(0px); }
}

/* Feature icons */
.feature-icon {
  width: 70px;
  height: 70px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  margin-bottom: 1.5rem;
}

/* Step cards */
.step-card {
  height: 100%;
  border-radius: 1rem;
  background: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.step-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.05) !important;
}

.step-number {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

/* CTA Section */
.cta {
  background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
  border-radius: 0.5rem;
  margin: 2rem 0 0;
  position: relative;
  overflow: hidden;
}

.cta::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.cta .container {
  position: relative;
  z-index: 1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .hero {
    text-align: center;
    padding: 3rem 1rem;
  }
  
  .hero .btn {
    width: 100%;
    margin-bottom: 1rem;
  }
  
  .quick-validator {
    margin-bottom: 2rem;
  }
  
  .cta .btn {
    width: 100%;
    margin-bottom: 1rem;
  }
  
  /* Mobile-specific improvements */
  .action-card {
    min-height: 200px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  
  .action-card:active {
    transform: scale(0.98);
  }
  
  .action-card:hover {
    transform: none;
  }
  
  /* Typography */
  h1 { font-size: 1.75rem; }
  h2 { font-size: 1.5rem; }
  h3 { font-size: 1.25rem; }
  
  /* Spacing */
  .card-body {
    padding: 1rem;
  }
  
  /* Buttons */
  .btn {
    min-height: 44px;
    font-size: 1rem;
    padding: 0.75rem 1rem;
  }
  
  /* Input groups */
  .input-group {
    flex-direction: column;
  }
  
  .input-group .form-control {
    border-radius: 0.375rem 0.375rem 0 0;
    margin-bottom: 0;
  }
  
  .input-group .btn {
    border-radius: 0 0 0.375rem 0.375rem;
    width: 100%;
  }
  
  /* Feature icons */
  .feature-icon {
    width: 60px;
    height: 60px;
    font-size: 1.5rem;
  }
  
  /* Step cards */
  .step-card {
    padding: 1.5rem 1rem;
  }
  
  .step-number {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }
}

/* Tablet improvements */
@media (min-width: 769px) and (max-width: 1024px) {
  .action-card {
    min-height: 180px;
  }
  
  .btn {
    min-height: 40px;
  }
  
  .feature-icon {
    width: 65px;
    height: 65px;
  }
}

/* Touch improvements */
@media (hover: none) and (pointer: coarse) {
  .action-card {
    min-height: 200px;
  }
  
  .action-card:hover {
    transform: none;
  }
  
  .step-card:hover {
    transform: none;
  }
  
  .btn {
    min-height: 48px;
  }
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  .action-card,
  .step-card,
  .hero-image {
    transition: none;
    animation: none;
  }
  
  .action-card:active {
    transform: none;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .step-card {
    background-color: #2d2d2d;
    border-color: #3a3a3a;
  }
  
  .bg-light {
    background-color: #1a1a1a !important;
  }
}
</style>
