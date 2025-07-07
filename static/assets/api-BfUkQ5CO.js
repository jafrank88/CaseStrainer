import { a as axios } from "./index-enUF1-WP.js";
const baseURL = "/casestrainer/api";
const api = axios.create({
  baseURL,
  timeout: 12e4
  // 2 minutes default timeout
  // Remove default Content-Type header to let browser set it for FormData
});
api.interceptors.request.use((config) => {
  if (config.url === "/analyze" && config.data && config.data.type === "url") {
    config.timeout = 3e5;
    config.retryCount = 0;
    config.maxRetries = 3;
  } else {
    config.timeout = 12e4;
    config.retryCount = 0;
    config.maxRetries = 1;
  }
  return config;
});
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config || !config.retryCount || config.retryCount >= config.maxRetries || !(error.code === "ECONNABORTED" || error.message.includes("timeout") || error.message.includes("Network Error"))) {
      return Promise.reject(error);
    }
    config.retryCount += 1;
    const delay = Math.min(1e3 * Math.pow(2, config.retryCount), 3e4);
    console.log(`Retrying request to ${config.url} (attempt ${config.retryCount}/${config.maxRetries}) after ${delay}ms delay`);
    await new Promise((resolve) => setTimeout(resolve, delay));
    return api(config);
  }
);
api.interceptors.request.use(
  (config) => {
    config.headers["X-API-Key"] = "***REDACTED_COURTLISTENER_KEY***";
    if (!(config.data instanceof FormData)) {
      config.headers["Content-Type"] = "application/json";
    }
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    var _a, _b;
    if (error.response) {
      console.error("API Error Response:", {
        status: error.response.status,
        url: (_a = error.config) == null ? void 0 : _a.url,
        data: error.response.data,
        headers: error.response.headers
      });
    } else if (error.request) {
      console.error("API Request Error (No Response):", {
        url: (_b = error.config) == null ? void 0 : _b.url,
        message: error.message
      });
    } else {
      console.error("API Error:", error.message);
    }
    return Promise.reject(error);
  }
);
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.config && error.config.url === "/analyze" && error.config.data && error.config.data.type === "url") {
      if (error.response) {
        switch (error.response.status) {
          case 400:
            error.message = "Invalid URL or content type not supported";
            break;
          case 404:
            error.message = "URL not found or content not accessible";
            break;
          case 429:
            error.message = "Too many requests. Please try again in a few minutes";
            break;
          case 502:
            error.message = "Failed to fetch URL content. The server may be temporarily unavailable";
            break;
          case 504:
            error.message = "Request timed out while fetching URL content";
            break;
          default:
            error.message = `Error fetching URL: ${error.response.status} ${error.response.statusText}`;
        }
      } else if (error.code === "ECONNABORTED") {
        error.message = "Request timed out while fetching URL content";
      } else if (error.code === "ECONNREFUSED") {
        error.message = "Could not connect to the server";
      } else if (error.code === "ENOTFOUND") {
        error.message = "URL not found or domain does not exist";
      }
    }
    return Promise.reject(error);
  }
);
const POLLING_INTERVAL = 2e3;
const MAX_POLLING_TIME = 6e5;
async function pollForResults(requestId, startTime = Date.now()) {
  var _a, _b;
  if (Date.now() - startTime > MAX_POLLING_TIME) {
    throw new Error("Request timed out after 10 minutes");
  }
  try {
    console.log("Polling for results:", {
      taskId: requestId,
      endpoint: `/task_status/${requestId}`,
      elapsed: Date.now() - startTime,
      baseURL
    });
    const response = await api.get(`/task_status/${requestId}`, {
      timeout: 3e4,
      // 30 second timeout for status checks
      validateStatus: function(status) {
        return status < 500;
      }
    });
    console.log("Status check response:", {
      taskId: requestId,
      status: response.status,
      data: response.data,
      headers: response.headers
    });
    if (response.status === 404) {
      console.log("Task not ready yet, retrying...", {
        taskId: requestId,
        elapsed: Date.now() - startTime,
        endpoint: `/task_status/${requestId}`
      });
      await new Promise((resolve) => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    }
    if (response.data.status === "completed") {
      console.log("Task completed:", {
        taskId: requestId,
        elapsed: Date.now() - startTime,
        citations: ((_a = response.data.citations) == null ? void 0 : _a.length) || 0
      });
      return response.data;
    } else if (response.data.status === "failed") {
      console.error("Task failed:", {
        taskId: requestId,
        error: response.data.error,
        elapsed: Date.now() - startTime
      });
      throw new Error(response.data.error || "Request failed");
    } else if (response.data.status === "processing" || response.data.status === "queued" || response.data.status === "pending") {
      console.log("Processing status:", {
        taskId: requestId,
        status: response.data.status,
        progress: response.data.progress,
        message: response.data.message,
        queuePosition: response.data.queue_position,
        estimatedWaitTime: response.data.estimated_wait_time,
        citations: ((_b = response.data.citations) == null ? void 0 : _b.length) || 0
      });
      await new Promise((resolve) => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    } else {
      console.warn("Unknown status received:", {
        taskId: requestId,
        status: response.data.status,
        data: response.data
      });
      await new Promise((resolve) => setTimeout(resolve, POLLING_INTERVAL));
      return pollForResults(requestId, startTime);
    }
  } catch (error) {
    if (error.response) {
      if (error.response.status === 404) {
        console.log("Status endpoint not found, retrying...", {
          taskId: requestId,
          elapsed: Date.now() - startTime,
          endpoint: `/task_status/${requestId}`,
          baseURL,
          response: error.response.data
        });
        await new Promise((resolve) => setTimeout(resolve, POLLING_INTERVAL));
        return pollForResults(requestId, startTime);
      } else {
        console.error("Status check failed:", {
          taskId: requestId,
          status: error.response.status,
          data: error.response.data,
          headers: error.response.headers,
          endpoint: `/task_status/${requestId}`,
          baseURL
        });
        throw new Error(`Status check failed: ${error.response.status} ${error.response.statusText}`);
      }
    } else if (error.request) {
      console.error("No response received for status check:", {
        taskId: requestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw new Error("No response received from server");
    } else {
      console.error("Error checking status:", {
        taskId: requestId,
        message: error.message,
        endpoint: `/task_status/${requestId}`,
        baseURL
      });
      throw error;
    }
  }
}
const analyze = async (requestData) => {
  const timeout = requestData.type === "url" ? 3e5 : 12e4;
  try {
    console.log("Starting analysis:", {
      type: requestData.type,
      isFormData: requestData instanceof FormData,
      baseURL,
      endpoint: "/analyze"
    });
    const headers = requestData instanceof FormData ? {} : {
      "Content-Type": "application/json"
    };
    const response = await api.post("/analyze", requestData, {
      timeout,
      headers,
      validateStatus: function(status) {
        return status < 500;
      }
    });
    console.log("Analysis response:", {
      status: response.status,
      data: response.data,
      headers: response.headers
    });
    if (response.status === 202 && response.data.task_id) {
      console.log("Starting polling for task:", {
        taskId: response.data.task_id,
        status: response.data.status,
        message: response.data.message
      });
      return await pollForResults(response.data.task_id);
    }
    return response.data;
  } catch (error) {
    console.error("Error in analyze request:", {
      error,
      type: requestData.type,
      isFormData: requestData instanceof FormData,
      baseURL,
      endpoint: "/analyze"
    });
    throw error;
  }
};
export {
  analyze as a,
  api as b
};
//# sourceMappingURL=api-BfUkQ5CO.js.map
