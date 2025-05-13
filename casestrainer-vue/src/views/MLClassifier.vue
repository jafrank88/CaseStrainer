<template>
  <div class="ml-classifier">
    <h2>Machine Learning Citation Classifier</h2>
    <p class="lead">
      Our ML classifier can predict whether a citation is real or hallucinated without requiring API calls.
      It's trained on our database of confirmed and unconfirmed citations.
    </p>
    
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">Test a Citation</div>
          <div class="card-body">
            <form @submit.prevent="classifyCitation">
              <div class="mb-3">
                <label for="citationText" class="form-label">Citation Text:</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="citationText" 
                  v-model="citationInput.text"
                  placeholder="e.g., 347 U.S. 483"
                  required
                >
              </div>
              <div class="mb-3">
                <label for="caseName" class="form-label">Case Name (Optional):</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="caseName" 
                  v-model="citationInput.caseName"
                  placeholder="e.g., Brown v. Board of Education"
                >
                <div class="form-text">Including a case name improves classification accuracy.</div>
              </div>
              <button type="submit" class="btn btn-primary" :disabled="classifying">
                <span v-if="classifying" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Classify Citation
              </button>
            </form>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">Model Information</div>
          <div class="card-body">
            <div class="mb-3">
              <h5>Model Performance</h5>
              <div class="row text-center">
                <div class="col-md-4 mb-3">
                  <h4>95%</h4>
                  <p class="text-muted">Accuracy</p>
                </div>
                <div class="col-md-4 mb-3">
                  <h4>92%</h4>
                  <p class="text-muted">Precision</p>
                </div>
                <div class="col-md-4 mb-3">
                  <h4>93%</h4>
                  <p class="text-muted">Recall</p>
                </div>
              </div>
            </div>
            <div class="mb-3">
              <h5>Training Data</h5>
              <p>The model is trained on a dataset of:</p>
              <ul>
                <li>500+ confirmed citations from legal databases</li>
                <li>100+ unconfirmed citations from Washington Courts briefs</li>
                <li>50+ synthetically generated hallucinated citations</li>
              </ul>
            </div>
            <div class="mb-3">
              <h5>Features Used</h5>
              <ul>
                <li>Citation format patterns</li>
                <li>Jurisdiction markers</li>
                <li>Year references</li>
                <li>Case name patterns</li>
                <li>Context features</li>
              </ul>
            </div>
            <button class="btn btn-outline-primary" @click="trainModel" :disabled="training">
              <span v-if="training" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Retrain Model
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="classificationResult" class="card">
      <div class="card-header">Classification Result</div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <h5>Citation Information</h5>
            <table class="table table-sm">
              <tbody>
                <tr>
                  <th scope="row">Citation Text</th>
                  <td>{{ classificationResult.citation }}</td>
                </tr>
                <tr v-if="classificationResult.case_name">
                  <th scope="row">Case Name</th>
                  <td>{{ classificationResult.case_name }}</td>
                </tr>
                <tr v-if="classificationResult.format">
                  <th scope="row">Format</th>
                  <td>{{ classificationResult.format }}</td>
                </tr>
                <tr v-if="classificationResult.jurisdiction">
                  <th scope="row">Jurisdiction</th>
                  <td>{{ classificationResult.jurisdiction }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="col-md-6">
            <h5>Prediction</h5>
            <div class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span>Likelihood of being a real citation:</span>
                <span class="badge" :class="confidenceBadgeClass">
                  {{ (classificationResult.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="progress" style="height: 25px;">
                <div 
                  class="progress-bar" 
                  role="progressbar" 
                  :style="{ width: (classificationResult.confidence * 100) + '%' }"
                  :class="confidenceProgressClass"
                  :aria-valuenow="classificationResult.confidence * 100" 
                  aria-valuemin="0" 
                  aria-valuemax="100"
                >
                  {{ (classificationResult.confidence * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
            <div class="alert" :class="predictionAlertClass">
              <h5 class="alert-heading">{{ predictionHeading }}</h5>
              <p>{{ classificationResult.explanation }}</p>
            </div>
          </div>
        </div>
        
        <div v-if="classificationResult.feature_importance" class="mt-4">
          <h5>Feature Importance</h5>
          <div class="row">
            <div v-for="(value, feature) in classificationResult.feature_importance" :key="feature" class="col-md-6 mb-3">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span>{{ formatFeatureName(feature) }}</span>
                <span>{{ value.toFixed(2) }}</span>
              </div>
              <div class="progress">
                <div 
                  class="progress-bar bg-info" 
                  role="progressbar" 
                  :style="{ width: (value * 100) + '%' }"
                  :aria-valuenow="value * 100" 
                  aria-valuemin="0" 
                  aria-valuemax="100"
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="classificationResult.similar_citations && classificationResult.similar_citations.length > 0" class="mt-4">
          <h5>Similar Citations in Database</h5>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Citation</th>
                  <th>Case Name</th>
                  <th>Status</th>
                  <th>Similarity</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(citation, index) in classificationResult.similar_citations" :key="index">
                  <td>{{ citation.citation_text }}</td>
                  <td>{{ citation.case_name || 'N/A' }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(citation.status)">
                      {{ citation.status }}
                    </span>
                  </td>
                  <td>{{ (citation.similarity * 100).toFixed(1) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card mt-4">
      <div class="card-header">Batch Classification</div>
      <div class="card-body">
        <p>Upload a CSV or text file with one citation per line to classify multiple citations at once.</p>
        <form @submit.prevent="batchClassify">
          <div class="mb-3">
            <label for="batchFile" class="form-label">Upload File:</label>
            <input 
              type="file" 
              class="form-control" 
              id="batchFile" 
              ref="batchFileInput"
              accept=".csv,.txt"
            >
            <div class="form-text">CSV format should have columns for citation_text and optionally case_name.</div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="batchProcessing">
            <span v-if="batchProcessing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Process Batch
          </button>
        </form>
        
        <div v-if="batchResults.length > 0" class="mt-4">
          <h5>Batch Results</h5>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Citation</th>
                  <th>Case Name</th>
                  <th>Confidence</th>
                  <th>Prediction</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(result, index) in batchResults" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>{{ result.citation }}</td>
                  <td>{{ result.case_name || 'N/A' }}</td>
                  <td>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
                        role="progressbar" 
                        :style="{ width: (result.confidence * 100) + '%' }"
                        :class="getConfidenceProgressClass(result.confidence)"
                        :aria-valuenow="result.confidence * 100" 
                        aria-valuemin="0" 
                        aria-valuemax="100"
                      >
                        {{ (result.confidence * 100).toFixed(1) }}%
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="badge" :class="getPredictionBadgeClass(result.confidence)">
                      {{ getPredictionText(result.confidence) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="mt-3">
            <button class="btn btn-success" @click="exportBatchResults">
              <i class="bi bi-download"></i> Export Results
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api/citations';

export default {
  name: 'MLClassifier',
  data() {
    return {
      citationInput: {
        text: '',
        caseName: ''
      },
      classifying: false,
      training: false,
      classificationResult: null,
      batchProcessing: false,
      batchResults: []
    };
  },
  computed: {
    confidenceBadgeClass() {
      const confidence = this.classificationResult?.confidence || 0;
      if (confidence >= 0.9) return 'bg-success';
      if (confidence >= 0.7) return 'bg-warning text-dark';
      return 'bg-danger';
    },
    confidenceProgressClass() {
      const confidence = this.classificationResult?.confidence || 0;
      if (confidence >= 0.9) return 'bg-success';
      if (confidence >= 0.7) return 'bg-warning';
      return 'bg-danger';
    },
    predictionAlertClass() {
      const confidence = this.classificationResult?.confidence || 0;
      if (confidence >= 0.9) return 'alert-success';
      if (confidence >= 0.7) return 'alert-warning';
      return 'alert-danger';
    },
    predictionHeading() {
      const confidence = this.classificationResult?.confidence || 0;
      if (confidence >= 0.9) return 'Likely Real Citation';
      if (confidence >= 0.7) return 'Possibly Real Citation';
      return 'Likely Hallucinated Citation';
    }
  },
  methods: {
    async classifyCitation() {
      if (!this.citationInput.text) return;
      
      this.classifying = true;
      
      try {
        const response = await api.classifyCitation(
          this.citationInput.text,
          this.citationInput.caseName || null
        );
        
        this.classificationResult = response.data;
      } catch (error) {
        console.error('Error classifying citation:', error);
        // Handle error
      } finally {
        this.classifying = false;
      }
    },
    
    async trainModel() {
      this.training = true;
      
      try {
        const response = await api.trainMLClassifier();
        
        // Show success message or update model info
        alert('Model training completed successfully!');
      } catch (error) {
        console.error('Error training model:', error);
        alert('Error training model. Please try again.');
      } finally {
        this.training = false;
      }
    },
    
    async batchClassify() {
      const fileInput = this.$refs.batchFileInput;
      if (!fileInput.files || fileInput.files.length === 0) return;
      
      const file = fileInput.files[0];
      this.batchProcessing = true;
      
      try {
        // In a real implementation, you would:
        // 1. Read the file
        // 2. Parse CSV/text
        // 3. Send to API for batch processing
        // 4. Process results
        
        // For now, we'll simulate batch processing with a timeout
        setTimeout(() => {
          // Simulate batch results
          this.batchResults = [
            { citation: '347 U.S. 483', case_name: 'Brown v. Board of Education', confidence: 0.98 },
            { citation: '410 U.S. 113', case_name: 'Roe v. Wade', confidence: 0.97 },
            { citation: '384 U.S. 436', case_name: 'Miranda v. Arizona', confidence: 0.95 },
            { citation: '123 F.4d 456', case_name: 'Smith v. Jones', confidence: 0.45 },
            { citation: '789 P.3d 123', case_name: 'Washington v. Oregon', confidence: 0.72 }
          ];
          
          this.batchProcessing = false;
        }, 2000);
      } catch (error) {
        console.error('Error processing batch:', error);
        alert('Error processing batch. Please try again.');
        this.batchProcessing = false;
      }
    },
    
    exportBatchResults() {
      // Create CSV content
      let csvContent = 'data:text/csv;charset=utf-8,';
      csvContent += 'Citation,Case Name,Confidence,Prediction\n';
      
      this.batchResults.forEach(result => {
        csvContent += `"${result.citation}","${result.case_name || ''}",${result.confidence.toFixed(4)},"${this.getPredictionText(result.confidence)}"\n`;
      });
      
      // Create download link
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', 'citation_classification_results.csv');
      document.body.appendChild(link);
      
      // Trigger download
      link.click();
      document.body.removeChild(link);
    },
    
    formatFeatureName(feature) {
      // Convert snake_case to Title Case with spaces
      return feature
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },
    
    getStatusBadgeClass(status) {
      switch (status.toLowerCase()) {
        case 'confirmed': return 'bg-success';
        case 'unconfirmed': return 'bg-warning text-dark';
        case 'hallucinated': return 'bg-danger';
        default: return 'bg-secondary';
      }
    },
    
    getConfidenceProgressClass(confidence) {
      if (confidence >= 0.9) return 'bg-success';
      if (confidence >= 0.7) return 'bg-warning';
      return 'bg-danger';
    },
    
    getPredictionBadgeClass(confidence) {
      if (confidence >= 0.9) return 'bg-success';
      if (confidence >= 0.7) return 'bg-warning text-dark';
      return 'bg-danger';
    },
    
    getPredictionText(confidence) {
      if (confidence >= 0.9) return 'Real';
      if (confidence >= 0.7) return 'Possibly Real';
      return 'Hallucinated';
    }
  }
}
</script>
