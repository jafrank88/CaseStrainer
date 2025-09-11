/**
 * Polling service for checking async task status
 * Handles polling the task_status endpoint until tasks complete
 */

// Get base URL from environment variables (same as api.js)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/casestrainer/api';

class PollingService {
  constructor() {
    this.activePolls = new Map(); // Map of task_id -> poll interval
    this.maxPollTime = 10 * 60 * 1000; // 10 minutes max
    this.pollInterval = 2000; // 2 seconds between polls
  }

  /**
   * Start polling for a task
   * @param {string} taskId - The task ID to poll
   * @param {Function} onProgress - Callback for progress updates
   * @param {Function} onComplete - Callback when task completes
   * @param {Function} onError - Callback for errors
   */
  startPolling(taskId, onProgress, onComplete, onError) {
    if (this.activePolls.has(taskId)) {
      console.warn(`Already polling for task ${taskId}`);
      return;
    }

    console.log(`Starting polling for task ${taskId}`);
    
    const startTime = Date.now();
    let pollCount = 0;

    const poll = async () => {
      try {
        pollCount++;
        console.log(`Polling task ${taskId} (attempt ${pollCount})`);

        const response = await fetch(`${API_BASE_URL}/task_status/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log(`Task ${taskId} status:`, result);

        // Check if task is complete
        if (result.status === 'completed' && result.success) {
          console.log(`Task ${taskId} completed successfully`);
          this.stopPolling(taskId);
          onComplete(result);
          return;
        }

        // Check if task failed
        if (result.status === 'failed' || !result.success) {
          console.error(`Task ${taskId} failed:`, result.error || 'Unknown error');
          this.stopPolling(taskId);
          onError(result.error || 'Task failed');
          return;
        }

        // Task is still processing
        if (result.status === 'processing' || result.status === 'queued') {
          // Call progress callback
          onProgress({
            taskId,
            status: result.status,
            message: result.message || 'Processing...',
            position: result.position,
            pollCount
          });

          // Check if we've exceeded max poll time
          if (Date.now() - startTime > this.maxPollTime) {
            console.error(`Task ${taskId} exceeded max poll time`);
            this.stopPolling(taskId);
            onError('Task exceeded maximum processing time');
            return;
          }

          // Continue polling
          return;
        }

        // Unknown status
        console.warn(`Unknown task status for ${taskId}:`, result.status);
        onProgress({
          taskId,
          status: 'unknown',
          message: 'Unknown status',
          pollCount
        });

      } catch (error) {
        console.error(`Error polling task ${taskId}:`, error);
        
        // Check if we've exceeded max poll time
        if (Date.now() - startTime > this.maxPollTime) {
          console.error(`Task ${taskId} exceeded max poll time due to errors`);
          this.stopPolling(taskId);
          onError('Task exceeded maximum processing time due to errors');
          return;
        }

        // Continue polling on error (network issues, etc.)
        onProgress({
          taskId,
          status: 'error',
          message: `Polling error: ${error.message}`,
          pollCount
        });
      }
    };

    // Start immediate poll
    poll();

    // Set up interval for subsequent polls
    const intervalId = setInterval(poll, this.pollInterval);
    this.activePolls.set(taskId, intervalId);
  }

  /**
   * Stop polling for a specific task
   * @param {string} taskId - The task ID to stop polling
   */
  stopPolling(taskId) {
    const intervalId = this.activePolls.get(taskId);
    if (intervalId) {
      clearInterval(intervalId);
      this.activePolls.delete(taskId);
      console.log(`Stopped polling for task ${taskId}`);
    }
  }

  /**
   * Stop all active polling
   */
  stopAllPolling() {
    for (const [taskId, intervalId] of this.activePolls) {
      clearInterval(intervalId);
      console.log(`Stopped polling for task ${taskId}`);
    }
    this.activePolls.clear();
  }

  /**
   * Check if a task is being polled
   * @param {string} taskId - The task ID to check
   * @returns {boolean} - True if task is being polled
   */
  isPolling(taskId) {
    return this.activePolls.has(taskId);
  }

  /**
   * Get count of active polls
   * @returns {number} - Number of active polls
   */
  getActivePollCount() {
    return this.activePolls.size;
  }
}

// Export singleton instance
export default new PollingService();
