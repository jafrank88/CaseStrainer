<template>
  <div class="feedback-form">
    <div class="feedback-toggle" @click="toggleForm">
      {{ isOpen ? 'Hide Feedback Form' : 'Send Feedback' }}
    </div>
    <div v-if="isOpen" class="feedback-content">
      <h3>Send Feedback</h3>
      <div v-if="message" :class="['alert', messageType]">
        {{ message }}
      </div>
      <form @submit.prevent="submitFeedback">
        <div class="form-group">
          <label for="feedback-message">Your Feedback:</label>
          <textarea
            id="feedback-message"
            v-model="feedback"
            class="form-control"
            rows="3"
            required
            placeholder="Please share your feedback, questions, or report any issues..."
          ></textarea>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            {{ isSubmitting ? 'Sending...' : 'Send Feedback' }}
          </button>
          <button type="button" class="btn btn-outline-secondary ml-2" @click="resetForm">
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FeedbackForm',
  data() {
    return {
      isOpen: false,
      feedback: '',
      isSubmitting: false,
      message: '',
      messageType: ''
    }
  },
  methods: {
    toggleForm() {
      this.isOpen = !this.isOpen
      if (!this.isOpen) {
        this.resetForm()
      }
    },
    async submitFeedback() {
      if (!this.feedback.trim()) return
      
      this.isSubmitting = true
      this.message = ''
      
      try {
        const response = await this.$http.post('/api/send_feedback', {
          message: this.feedback,
          page: window.location.href,
          userAgent: navigator.userAgent
        })
        
        this.message = 'Thank you for your feedback! We\'ll get back to you soon.'
        this.messageType = 'alert-success'
        this.feedback = ''
        
        // Close the form after 3 seconds
        setTimeout(() => {
          this.isOpen = false
          this.resetForm()
        }, 3000)
      } catch (error) {
        console.error('Error sending feedback:', error)
        this.message = 'Failed to send feedback. Please try again later.'
        this.messageType = 'alert-danger'
      } finally {
        this.isSubmitting = false
      }
    },
    resetForm() {
      this.feedback = ''
      this.message = ''
      this.messageType = ''
    }
  }
}
</script>

<style scoped>
.feedback-form {
  margin: 2rem 0;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  overflow: hidden;
}

.feedback-toggle {
  background-color: #f8f9fa;
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  font-weight: 500;
  color: #0056b3;
  transition: background-color 0.2s;
}

.feedback-toggle:hover {
  background-color: #e9ecef;
}

.feedback-content {
  padding: 1.25rem;
  background-color: #fff;
}

.feedback-content h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.25rem;
}

.form-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}

.alert {
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}

.alert-success {
  color: #155724;
  background-color: #d4edda;
  border-color: #c3e6cb;
}

.alert-danger {
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
}

.spinner-border {
  margin-right: 0.5rem;
}
</style>
