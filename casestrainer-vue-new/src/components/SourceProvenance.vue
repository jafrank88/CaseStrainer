<template>
  <div class="source-provenance">
    <div class="provenance-header">
      <h4>Source Provenance</h4>
      <p class="text-muted">Verification sources and data reliability information</p>
    </div>
    
    <div v-for="(citation, index) in citations" :key="citation.citation" class="provenance-item">
      <div class="citation-header">
        <strong>{{ citation.citation }}</strong>
        <span :class="['verification-status', getVerificationStatus(citation)]">
          {{ getVerificationStatusText(citation) }}
        </span>
      </div>
      
      <div class="sources-grid">
        <!-- CourtListener -->
        <div class="source-card" :class="{ active: citation.courtlistener_verified }">
          <div class="source-header">
            <div class="source-icon">🏛️</div>
            <div class="source-info">
              <h5>CourtListener</h5>
              <span class="reliability-score" :class="getReliabilityClass(0.95)">
                Reliability: 95%
              </span>
            </div>
          </div>
          <div class="source-details">
            <div v-if="citation.courtlistener_verified" class="detail-row">
              <span class="label">Status:</span>
              <span class="value verified">Verified</span>
            </div>
            <div v-if="citation.courtlistener_url" class="detail-row">
              <span class="label">URL:</span>
              <a :href="citation.courtlistener_url" target="_blank" class="value link">
                View Case
              </a>
            </div>
            <div v-if="citation.courtlistener_last_checked" class="detail-row">
              <span class="label">Last Updated:</span>
              <span class="value">{{ formatDate(citation.courtlistener_last_checked) }}</span>
            </div>
            <div v-else class="detail-row">
              <span class="label">Status:</span>
              <span class="value not-verified">Not Verified</span>
            </div>
          </div>
        </div>
        
        <!-- Web Search Sources -->
        <div class="source-card" :class="{ active: citation.web_verified }">
          <div class="source-header">
            <div class="source-icon">🌐</div>
            <div class="source-info">
              <h5>Web Search</h5>
              <span class="reliability-score" :class="getReliabilityClass(0.85)">
                Reliability: 85%
              </span>
            </div>
          </div>
          <div class="source-details">
            <div v-if="citation.web_verified" class="detail-row">
              <span class="label">Status:</span>
              <span class="value verified">Verified</span>
            </div>
            <div v-if="citation.web_sources && citation.web_sources.length > 0" class="detail-row">
              <span class="label">Sources:</span>
              <div class="web-sources">
                <div v-for="(source, idx) in citation.web_sources.slice(0, 3)" :key="idx" class="web-source">
                  <a :href="source.url" target="_blank" class="value link">
                    {{ source.domain || 'Unknown' }}
                  </a>
                  <span class="source-type">{{ source.type || 'Legal' }}</span>
                </div>
              </div>
            </div>
            <div v-if="citation.web_last_checked" class="detail-row">
              <span class="label">Last Updated:</span>
              <span class="value">{{ formatDate(citation.web_last_checked) }}</span>
            </div>
            <div v-else class="detail-row">
              <span class="label">Status:</span>
              <span class="value not-verified">Not Verified</span>
            </div>
          </div>
        </div>
        
        <!-- Local Database -->
        <div class="source-card" :class="{ active: citation.local_verified }">
          <div class="source-header">
            <div class="source-icon">💾</div>
            <div class="source-info">
              <h5>Local Database</h5>
              <span class="reliability-score" :class="getReliabilityClass(0.90)">
                Reliability: 90%
              </span>
            </div>
          </div>
          <div class="source-details">
            <div v-if="citation.local_verified" class="detail-row">
              <span class="label">Status:</span>
              <span class="value verified">Verified</span>
            </div>
            <div v-if="citation.local_source" class="detail-row">
              <span class="label">Source:</span>
              <span class="value">{{ citation.local_source }}</span>
            </div>
            <div v-if="citation.local_last_checked" class="detail-row">
              <span class="label">Last Updated:</span>
              <span class="value">{{ formatDate(citation.local_last_checked) }}</span>
            </div>
            <div v-else class="detail-row">
              <span class="label">Status:</span>
              <span class="value not-verified">Not Verified</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Overall Reliability Score -->
      <div class="overall-reliability">
        <div class="reliability-header">
          <h5>Overall Reliability Score</h5>
          <span class="score" :class="getReliabilityClass(getOverallReliability(citation))">
            {{ Math.round(getOverallReliability(citation)) }}%
          </span>
        </div>
        <div class="reliability-breakdown">
          <div class="breakdown-item">
            <span class="label">CourtListener:</span>
            <span class="value">{{ citation.courtlistener_verified ? '95%' : '0%' }}</span>
          </div>
          <div class="breakdown-item">
            <span class="label">Web Search:</span>
            <span class="value">{{ citation.web_verified ? '85%' : '0%' }}</span>
          </div>
          <div class="breakdown-item">
            <span class="label">Local DB:</span>
            <span class="value">{{ citation.local_verified ? '90%' : '0%' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SourceProvenance',
  props: {
    citations: {
      type: Array,
      required: true
    }
  },
  methods: {
    getVerificationStatus(citation) {
      if (citation.courtlistener_verified) return 'verified';
      if (citation.web_verified || citation.local_verified) return 'partial';
      return 'unverified';
    },
    
    getVerificationStatusText(citation) {
      if (citation.courtlistener_verified) return 'Verified';
      if (citation.web_verified || citation.local_verified) return 'Partially Verified';
      return 'Not Verified';
    },
    
    getReliabilityClass(score) {
      if (score >= 90) return 'high';
      if (score >= 70) return 'medium';
      return 'low';
    },
    
    getOverallReliability(citation) {
      let total = 0;
      let count = 0;
      
      if (citation.courtlistener_verified) {
        total += 95;
        count++;
      }
      if (citation.web_verified) {
        total += 85;
        count++;
      }
      if (citation.local_verified) {
        total += 90;
        count++;
      }
      
      return count > 0 ? total / count : 0;
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      } catch {
        return 'Invalid Date';
      }
    }
  }
};
</script>

<style scoped>
.source-provenance {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.provenance-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 1rem;
}

.provenance-header h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.provenance-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background: #fafafa;
}

.citation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.verification-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.verification-status.verified {
  background: #d4edda;
  color: #155724;
}

.verification-status.partial {
  background: #fff3cd;
  color: #856404;
}

.verification-status.unverified {
  background: #f8d7da;
  color: #721c24;
}

.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.source-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
  background: #fff;
  transition: all 0.2s;
}

.source-card.active {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.source-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.source-icon {
  font-size: 1.5rem;
}

.source-info h5 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.reliability-score {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
}

.reliability-score.high {
  background: #d4edda;
  color: #155724;
}

.reliability-score.medium {
  background: #fff3cd;
  color: #856404;
}

.reliability-score.low {
  background: #f8d7da;
  color: #721c24;
}

.source-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.detail-row .label {
  font-weight: 500;
  color: #555;
}

.detail-row .value {
  color: #333;
}

.detail-row .value.verified {
  color: #155724;
  font-weight: 500;
}

.detail-row .value.not-verified {
  color: #721c24;
  font-weight: 500;
}

.detail-row .value.link {
  color: #1976d2;
  text-decoration: none;
}

.detail-row .value.link:hover {
  text-decoration: underline;
}

.web-sources {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.web-source {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}

.source-type {
  background: #f0f0f0;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.7rem;
  color: #666;
}

.overall-reliability {
  border-top: 1px solid #e0e0e0;
  padding-top: 1rem;
  margin-top: 1rem;
}

.reliability-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.reliability-header h5 {
  margin: 0;
  color: #333;
}

.reliability-header .score {
  font-size: 1.2rem;
  font-weight: bold;
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

.reliability-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.breakdown-item .label {
  color: #555;
}

.breakdown-item .value {
  font-weight: 500;
  color: #333;
}
</style> 