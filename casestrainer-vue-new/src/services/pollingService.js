/**
 * Polling service for checking async task status
 * Handles polling the task_status endpoint until tasks complete
 */

import { API_BASE_URL } from '@/config/api';

class PollingService {
  constructor() {
    this.activePolls = new Map(); // Map of task_id -> poll interval
    this.maxPollTime = 20 * 60 * 1000; // 20 minutes max (increased from 10 to handle rate-limited verification)
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
        
        // Handle 404 - job may still be processing, results not ready yet
        if (response.status === 404) {
          console.log(`Task ${taskId} not found yet (404) - job may still be processing`);
          onProgress({
            taskId,
            status: 'processing',
            message: 'Processing...',
            pollCount
          });
          
          // Check if we've exceeded max poll time
          if (Date.now() - startTime > this.maxPollTime) {
            console.error(`Task ${taskId} exceeded max poll time (404 persists)`);
            this.stopPolling(taskId);
            onError('Task exceeded maximum processing time - results not found');
            return;
          }
          
          // Continue polling - don't treat 404 as fatal error during processing
          return;
        }
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log(`Task ${taskId} status:`, result);

        // Check if task is complete
        // Backend may return status at top level OR nested in progress object
        // Also check for citations/clusters presence as completion indicator
        const status = result.status || result.progress?.status;
        const hasResults = (result.citations && result.citations.length > 0) ||
                          (result.clusters && result.clusters.length > 0);
        const isCompleted = status === 'completed' || 
                           hasResults ||
                           (result.progress?.status === 'completed');
        
        if (isCompleted) {
          console.log(`Task ${taskId} completion detected`, {
            status: status,
            progressStatus: result.progress?.status,
            citationsCount: result.citations?.length || 0,
            clustersCount: result.clusters?.length || 0,
            hasProgress: !!result.progress,
            hasResults: hasResults
          });
          
          // CRITICAL: If we detected completion via progress.status but don't have citations/clusters yet,
          // we MUST fetch the full result from task_status endpoint
          // The progress endpoint only returns progress data, not actual results
          if ((result.progress?.status === 'completed' || status === 'completed') && !hasResults) {
            console.log(`Task marked as completed but no results in response - fetching full result from task_status endpoint...`);
            try {
              const resultResponse = await fetch(`${API_BASE_URL}/task_status/${taskId}?t=${Date.now()}`);
              if (resultResponse.ok) {
                const fullResult = await resultResponse.json();
                console.log(`Fetched full result from task_status:`, {
                  status: fullResult.status,
                  citationsCount: fullResult.citations?.length || 0,
                  clustersCount: fullResult.clusters?.length || 0,
                  hasResults: !!(fullResult.citations?.length || fullResult.clusters?.length)
                });
                
                // Only complete if we actually have results (even if empty arrays - that's a valid result)
                // Backend should always return citations/clusters arrays when status is 'completed'
                const hasCitationsArray = Array.isArray(fullResult.citations);
                const hasClustersArray = Array.isArray(fullResult.clusters);
                const hasResults = hasCitationsArray || hasClustersArray;
                
                if (hasResults && fullResult.status === 'completed') {
                  // Results are ready (even if empty) - complete the task
                  console.log(`Task completed with results: ${fullResult.citations?.length || 0} citations, ${fullResult.clusters?.length || 0} clusters`);
                  this.stopPolling(taskId);
                  onComplete(fullResult);
                  return;
                } else {
                  console.log(`Task_status returned status '${fullResult.status}' but results not ready yet (citations: ${hasCitationsArray}, clusters: ${hasClustersArray}) - continuing to poll...`);
                  // Continue polling - results not ready yet
                  return;
                }
              } else if (resultResponse.status === 404) {
                console.log(`Task_status returned 404 - task may still be processing, continuing to poll...`);
                // Continue polling - task not found in RQ yet
                return;
              }
            } catch (error) {
              console.warn(`Failed to fetch full result from task_status, continuing to poll:`, error);
              // Continue polling on error
              return;
            }
          }
          
          // If we have results, complete immediately
          if (hasResults) {
            this.stopPolling(taskId);
            onComplete(result);
            return;
          }
        }

        // Check if task failed
        // Only treat as failed if explicitly marked as failed, not just missing success field
        const failureStatus = result.status || result.progress?.status;
        if (failureStatus === 'failed' || (result.success === false && result.error)) {
          console.error(`Task ${taskId} failed:`, result.error || 'Unknown error');
          this.stopPolling(taskId);
          onError(result.error || 'Task failed');
          return;
        }

        // Task is still processing
        // Check status at top level or in progress object
        const currentStatus = result.status || result.progress?.status || 'processing';
        if (currentStatus === 'processing' || currentStatus === 'queued') {
          // Extract progress information from various possible locations
          const progressData = result.progress_data || result.progress || {};
          const progressPercent = result.progress_percent || progressData.progress || 0;
          const message = result.message || 
                         result.progress?.current_message || 
                         progressData.message || 
                         result.current_step || 
                         'Processing...';
          
          // Call progress callback with comprehensive progress data
          onProgress({
            taskId,
            status: currentStatus,
            message: message,
            progress: progressPercent,
            current_step: result.current_step || progressData.phase,
            position: result.position,
            pollCount,
            // Include full progress data for frontend use
            progress_data: progressData,
            elapsed_time: result.elapsed_time || result.elapsedTime || progressData.elapsed_time
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
