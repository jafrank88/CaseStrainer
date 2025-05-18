<template>
  <div class="citation-tester">
    <h2>Citation Verification Tester</h2>
    <p class="lead">Test the citation verification system with random assortments of citations</p>
    
    <div class="card mb-4">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Test Configuration</h5>
      </div>
      <div class="card-body">
        <form @submit.prevent="runTest">
          <div class="row mb-3">
            <div class="col-md-4">
              <label for="citationCount" class="form-label">Number of Citations:</label>
              <input 
                type="number" 
                class="form-control" 
                id="citationCount" 
                v-model.number="testConfig.count"
                min="1" 
                max="20"
                required
              >
            </div>
            <div class="col-md-8">
              <label class="form-label">Citation Types:</label>
              <div class="d-flex">
                <div class="form-check me-4">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="confirmedCheckbox" 
                    v-model="testConfig.includeConfirmed"
                    @change="updateCheckboxes"
                  >
                  <label class="form-check-label" for="confirmedCheckbox">
                    Include Confirmed Citations
                  </label>
                </div>
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="unconfirmedCheckbox" 
                    v-model="testConfig.includeUnconfirmed"
                    @change="updateCheckboxes"
                  >
                  <label class="form-check-label" for="unconfirmedCheckbox">
                    Include Unconfirmed Citations
                  </label>
                </div>
              </div>
            </div>
          </div>
          <div class="mb-3">
            <label for="apiKey" class="form-label">CourtListener API Key (Optional):</label>
            <input 
              type="text" 
              class="form-control" 
              id="apiKey" 
              v-model="testConfig.apiKey"
              placeholder="Enter your CourtListener API key"
            >
            <div class="form-text">If you have a CourtListener API key, enter it here for better citation verification.</div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="testing">
            <span v-if="testing" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Run Test
          </button>
        </form>
      </div>
    </div>
    
    <div v-if="testResults.length > 0" class="card mb-4">
      <ul class="nav nav-tabs" id="tester-tabs">
        <li class="nav-item">
          <a class="nav-link active" id="results-tab" data-bs-toggle="tab" href="#results-content" role="tab">Results</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" id="debug-tab" data-bs-toggle="tab" href="#debug-content" role="tab">Debug Information</a>
        </li>
      </ul>
      <div class="tab-content">
        <div class="tab-pane fade show active" id="results-content" role="tabpanel">

      <div class="card-header bg-info text-white">
        <h5 class="mb-0">Test Results</h5>
      </div>
      <div class="card-body">
        <div class="mb-4">
          <h5>Summary</h5>
          <div class="row text-center">
            <div class="col-md-3 mb-3">
              <div class="card bg-light">
                <div class="card-body">
                  <h3>{{ testResults.length }}</h3>
                  <p class="mb-0">Total Citations</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card bg-success text-white">
                <div class="card-body">
                  <h3>{{ correctlyVerified }}</h3>
                  <p class="mb-0">Correctly Verified</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card bg-danger text-white">
                <div class="card-body">
                  <h3>{{ incorrectlyVerified }}</h3>
                  <p class="mb-0">Incorrectly Verified</p>
                </div>
              </div>
            </div>
            <div class="col-md-3 mb-3">
              <div class="card bg-warning">
                <div class="card-body">
                  <h3>{{ (accuracy * 100).toFixed(1) }}%</h3>
                  <p class="mb-0">Accuracy</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>#</th>
                <th>Citation</th>
                <th>Actual Status</th>
                <th>Verified Status</th>
                <th>Verification Source</th>
                <th>Time (ms)</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in testResults" :key="index">
                <td>{{ index + 1 }}</td>
                <td>
                  <strong>{{ result.citation_text }}</strong>
                  <div v-if="result.case_name" class="small text-muted">{{ result.case_name }}</div>
                </td>
                <td>
                  <span 
                    class="badge" 
                    :class="result.actual_status === 'confirmed' ? 'bg-success' : 'bg-danger'"
                  >
                    {{ result.actual_status === 'confirmed' ? 'Real' : 'Hallucinated' }}
                  </span>
                </td>
                <td>
                  <span 
                    class="badge" 
                    :class="result.verified_status === 'confirmed' ? 'bg-success' : 'bg-danger'"
                  >
                    {{ result.verified_status === 'confirmed' ? 'Confirmed' : 'Unconfirmed' }}
                  </span>
                </td>
                <td>{{ result.verification_source || 'None' }}</td>
                <td>{{ result.verification_time_ms }}</td>
                <td>
                  <span 
                    class="badge" 
                    :class="result.actual_status === result.verified_status ? 'bg-success' : 'bg-danger'"
                  >
                    {{ result.actual_status === result.verified_status ? 'Correct' : 'Incorrect' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="mt-4">
          <h5>Performance by Verification Source</h5>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Verification Source</th>
                  <th>Citations</th>
                  <th>Correct</th>
                  <th>Incorrect</th>
                  <th>Accuracy</th>
                  <th>Avg. Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stats, source) in sourceStats" :key="source">
                  <td>{{ source }}</td>
                  <td>{{ stats.count }}</td>
                  <td>{{ stats.correct }}</td>
                  <td>{{ stats.incorrect }}</td>
                  <td>{{ (stats.accuracy * 100).toFixed(1) }}%</td>
                  <td>{{ stats.avgTime.toFixed(0) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <div class="tab-pane fade" id="debug-content" role="tabpanel" aria-labelledby="debug-tab">
      <div class="card bg-light">
        <div class="card-header bg-secondary text-white">
          <h6 class="mb-0">Debug Information</h6>
        </div>
        <div class="card-body">
          <pre class="bg-dark text-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">{{ debugInfo }}</pre>
        </div>
      </div>
    </div>
    </div>
    
    <div class="card">
      <div class="card-header bg-light">
        <h5 class="mb-0">About the Citation Tester</h5>
      </div>
      <div class="card-body">
        <p>The Citation Tester helps evaluate the performance of our citation verification system by:</p>
        <ul>
          <li>Testing with a mix of confirmed and unconfirmed citations</li>
          <li>Measuring verification accuracy and speed</li>
          <li>Comparing performance across different verification sources</li>
          <li>Identifying patterns in verification errors</li>
        </ul>
        <p>This tool is valuable for:</p>
        <ul>
          <li>Benchmarking system improvements</li>
          <li>Identifying verification sources that need enhancement</li>
          <li>Testing with different API keys to compare performance</li>
          <li>Validating the multi-source verification approach</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/api/citations';

export default {
  name: 'CitationTester',
  data() {
    return {
      testConfig: {
        count: 5,
        includeConfirmed: true,
        includeUnconfirmed: true,
        apiKey: ''
      },
      testing: false,
      testResults: [],
      debugInfo: ''
    };
  },
  computed: {
    correctlyVerified() {
      return this.testResults.filter(result => 
        result.actual_status === result.verified_status
      ).length;
    },
    incorrectlyVerified() {
      return this.testResults.filter(result => 
        result.actual_status !== result.verified_status
      ).length;
    },
    accuracy() {
      return this.testResults.length > 0 
        ? this.correctlyVerified / this.testResults.length 
        : 0;
    },
    sourceStats() {
      const stats = {};
      
      this.testResults.forEach(result => {
        const source = result.verification_source || 'None';
        
        if (!stats[source]) {
          stats[source] = {
            count: 0,
            correct: 0,
            incorrect: 0,
            totalTime: 0
          };
        }
        
        stats[source].count++;
        
        if (result.actual_status === result.verified_status) {
          stats[source].correct++;
        } else {
          stats[source].incorrect++;
        }
        
        stats[source].totalTime += result.verification_time_ms;
      });
      
      // Calculate accuracy and average time
      Object.keys(stats).forEach(source => {
        const sourceStats = stats[source];
        sourceStats.accuracy = sourceStats.count > 0 
          ? sourceStats.correct / sourceStats.count 
          : 0;
        sourceStats.avgTime = sourceStats.count > 0 
          ? sourceStats.totalTime / sourceStats.count 
          : 0;
      });
      
      return stats;
    }
  },
  methods: {
    updateCheckboxes() {
      // Ensure at least one checkbox is checked
      if (!this.testConfig.includeConfirmed && !this.testConfig.includeUnconfirmed) {
        // If both are unchecked, check the one that was just unchecked
        if (!this.testConfig.includeConfirmed) {
          this.testConfig.includeConfirmed = true;
        } else {
          this.testConfig.includeUnconfirmed = true;
        }
      }
    },
    
    async runTest() {
      this.testing = true;
      // Start debug info
      this.debugInfo = 'Debug: Starting citation test...\n';
      this.debugInfo += `Request: count=${this.testConfig.count}, includeConfirmed=${this.testConfig.includeConfirmed}, includeUnconfirmed=${this.testConfig.includeUnconfirmed}\n`;
      try {
        const response = await api.getTestCitations(
          this.testConfig.count,
          this.testConfig.includeConfirmed,
          this.testConfig.includeUnconfirmed
        );
        this.debugInfo += `Response received: Success\n`;
        this.debugInfo += `Response data: ${JSON.stringify(response.data, null, 2)}\n`;
        this.testResults = response.data.results || [];
      } catch (error) {
        console.error('Error running citation test:', error);
        this.debugInfo += `Error: ${error.message}\n`;
        if (error.response) {
          this.debugInfo += `Response status: ${error.response.status}\n`;
          this.debugInfo += `Response data: ${JSON.stringify(error.response.data, null, 2)}\n`;
        }
        alert('Error running citation test. Please try again.');
      } finally {
        this.testing = false;
      }
    }
  }
}
</script>
