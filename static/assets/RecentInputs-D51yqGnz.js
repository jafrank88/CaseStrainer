import { a as axios, _ as _export_sfc } from "./index-Dl5kF7e3.js";
import { r as ref, p as computed, c as createElementBlock, l as createCommentVNode, I as unref, o as openBlock, b as createBaseVNode, g as createTextVNode, t as toDisplayString, F as Fragment, n as renderList, x as normalizeClass, A as withModifiers } from "./vendor-0f3ixpnm.js";
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
    if (requestData instanceof FormData) {
      console.log("FormData contents:");
      for (let [key, value] of requestData.entries()) {
        if (value instanceof File) {
          console.log(`- ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
        } else {
          console.log(`- ${key}: ${value}`);
        }
      }
    }
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
    console.log("Response data details:", {
      hasCitations: !!response.data.citations,
      citationsLength: response.data.citations ? response.data.citations.length : 0,
      hasValidationResults: !!response.data.validation_results,
      validationResultsLength: response.data.validation_results ? response.data.validation_results.length : 0,
      hasError: !!response.data.error,
      error: response.data.error,
      status: response.data.status,
      message: response.data.message
    });
    if (response.data.status === "processing" && response.data.task_id) {
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
const recentInputs = ref([]);
const isInitialized = ref(false);
const getStorageKey = () => {
  return "casestrainer_recent_inputs";
};
const initializeRecentInputs = () => {
  if (isInitialized.value) return;
  try {
    const saved = localStorage.getItem(getStorageKey());
    if (saved) {
      const parsed = JSON.parse(saved);
      recentInputs.value = parsed.filter((input) => input && input.tab && input.timestamp).slice(0, 10);
    }
  } catch (error) {
    console.error("Error loading recent inputs:", error);
    localStorage.removeItem(getStorageKey());
  }
  isInitialized.value = true;
};
const saveRecentInputs = () => {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(recentInputs.value));
  } catch (error) {
    console.error("Error saving recent inputs:", error);
  }
};
const addRecentInput = (inputData) => {
  if (!inputData || !inputData.tab || !inputData.timestamp) {
    console.warn("Invalid input data:", inputData);
    return;
  }
  recentInputs.value = recentInputs.value.filter((input) => {
    if (input.tab !== inputData.tab) return true;
    switch (inputData.tab) {
      case "paste":
        return input.text !== inputData.text;
      case "url":
        return input.url !== inputData.url;
      case "file":
        return input.fileName !== inputData.fileName;
      default:
        return true;
    }
  });
  recentInputs.value.unshift(inputData);
  recentInputs.value = recentInputs.value.slice(0, 10);
  saveRecentInputs();
};
const removeRecentInput = (index) => {
  if (index >= 0 && index < recentInputs.value.length) {
    recentInputs.value.splice(index, 1);
    saveRecentInputs();
  }
};
const clearRecentInputs = () => {
  recentInputs.value = [];
  saveRecentInputs();
};
const getRecentInputsByTab = (tab) => {
  return recentInputs.value.filter((input) => input.tab === tab);
};
const getInputIcon = (tab) => {
  switch (tab) {
    case "paste":
      return "bi bi-clipboard-text";
    case "file":
      return "bi bi-file-earmark-text";
    case "url":
      return "bi bi-link-45deg";
    default:
      return "bi bi-question-circle";
  }
};
const getInputTitle = (input) => {
  switch (input.tab) {
    case "paste":
      return "Text Input";
    case "file":
      return `File: ${input.fileName || "Unknown"}`;
    case "url":
      return "URL Input";
    default:
      return "Unknown Input";
  }
};
const getInputPreview = (input) => {
  switch (input.tab) {
    case "paste":
      return input.text ? input.text.substring(0, 60) + (input.text.length > 60 ? "..." : "") : "No text";
    case "file":
      return input.fileName || "Unknown file";
    case "url":
      return input.url || "No URL";
    default:
      return "Unknown input type";
  }
};
const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp);
    const now = /* @__PURE__ */ new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 6e4);
    const diffHours = Math.floor(diffMs / 36e5);
    const diffDays = Math.floor(diffMs / 864e5);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return "Unknown time";
  }
};
const hasRecentInputs = computed(() => recentInputs.value.length > 0);
const recentInputsCount = computed(() => recentInputs.value.length);
function useRecentInputs() {
  if (!isInitialized.value) {
    initializeRecentInputs();
  }
  return {
    // State
    recentInputs: computed(() => recentInputs.value),
    hasRecentInputs,
    recentInputsCount,
    // Methods
    addRecentInput,
    removeRecentInput,
    clearRecentInputs,
    getRecentInputsByTab,
    getInputIcon,
    getInputTitle,
    getInputPreview,
    formatTimestamp,
    // Utility
    initializeRecentInputs
  };
}
const _hoisted_1 = {
  key: 0,
  class: "recent-inputs-sidebar"
};
const _hoisted_2 = { class: "sidebar-header" };
const _hoisted_3 = { class: "sidebar-title" };
const _hoisted_4 = { class: "badge bg-secondary ms-2" };
const _hoisted_5 = { class: "sidebar-content" };
const _hoisted_6 = { class: "recent-inputs-list" };
const _hoisted_7 = ["onClick"];
const _hoisted_8 = { class: "input-card-header" };
const _hoisted_9 = { class: "input-type-badge" };
const _hoisted_10 = { class: "input-time" };
const _hoisted_11 = { class: "input-card-content" };
const _hoisted_12 = { class: "input-title" };
const _hoisted_13 = { class: "input-preview" };
const _hoisted_14 = {
  key: 0,
  class: "file-warning"
};
const _hoisted_15 = { class: "input-card-actions" };
const _hoisted_16 = ["onClick"];
const _hoisted_17 = {
  key: 0,
  class: "empty-state"
};
const _sfc_main = {
  __name: "RecentInputs",
  props: {
    // Optional: filter by specific tab
    filterTab: {
      type: String,
      default: null
    },
    // Optional: maximum number to show
    maxItems: {
      type: Number,
      default: 10
    }
  },
  emits: ["load-input"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const {
      recentInputs: recentInputs2,
      hasRecentInputs: hasRecentInputs2,
      recentInputsCount: recentInputsCount2,
      removeRecentInput: removeRecentInput2,
      clearRecentInputs: clearRecentInputs2,
      getInputIcon: getInputIcon2,
      getInputTitle: getInputTitle2,
      getInputPreview: getInputPreview2,
      formatTimestamp: formatTimestamp2
    } = useRecentInputs();
    const filteredInputs = computed(() => {
      let inputs = recentInputs2.value;
      if (props.filterTab) {
        inputs = inputs.filter((input) => input.tab === props.filterTab);
      }
      return inputs.slice(0, props.maxItems);
    });
    const getInputTypeLabel = (tab) => {
      switch (tab) {
        case "text":
          return "Text";
        case "file":
          return "File";
        case "url":
          return "URL";
        case "quick":
          return "Citation";
        default:
          return "Input";
      }
    };
    const loadInput = (input) => {
      if (input.tab === "file") {
        if (!confirm("This will restore the file name, but you'll need to re-upload the file. Continue?")) {
          return;
        }
      }
      emit("load-input", input);
    };
    const removeInput = (index) => {
      const actualIndex = recentInputs2.value.findIndex(
        (item) => item.tab === filteredInputs.value[index].tab && item.timestamp === filteredInputs.value[index].timestamp
      );
      if (actualIndex !== -1) {
        removeRecentInput2(actualIndex);
      }
    };
    const clearAll = () => {
      if (confirm("Are you sure you want to clear all recent inputs?")) {
        clearRecentInputs2();
      }
    };
    return (_ctx, _cache) => {
      return unref(hasRecentInputs2) ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            _cache[0] || (_cache[0] = createBaseVNode("i", { class: "bi bi-clock-history me-2" }, null, -1)),
            _cache[1] || (_cache[1] = createTextVNode(" Recent Inputs ")),
            createBaseVNode("span", _hoisted_4, toDisplayString(unref(recentInputsCount2)), 1)
          ]),
          createBaseVNode("button", {
            onClick: clearAll,
            class: "btn btn-sm btn-outline-secondary",
            title: "Clear all recent inputs"
          }, _cache[2] || (_cache[2] = [
            createBaseVNode("i", { class: "bi bi-trash" }, null, -1)
          ]))
        ]),
        createBaseVNode("div", _hoisted_5, [
          createBaseVNode("div", _hoisted_6, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(unref(recentInputs2), (input, index) => {
              return openBlock(), createElementBlock("div", {
                key: `${input.tab}-${input.timestamp}-${index}`,
                class: "recent-input-card",
                onClick: ($event) => loadInput(input)
              }, [
                createBaseVNode("div", _hoisted_8, [
                  createBaseVNode("div", _hoisted_9, [
                    createBaseVNode("i", {
                      class: normalizeClass(unref(getInputIcon2)(input.tab))
                    }, null, 2),
                    createTextVNode(" " + toDisplayString(getInputTypeLabel(input.tab)), 1)
                  ]),
                  createBaseVNode("div", _hoisted_10, toDisplayString(unref(formatTimestamp2)(input.timestamp)), 1)
                ]),
                createBaseVNode("div", _hoisted_11, [
                  createBaseVNode("div", _hoisted_12, toDisplayString(unref(getInputTitle2)(input)), 1),
                  createBaseVNode("div", _hoisted_13, toDisplayString(unref(getInputPreview2)(input)), 1),
                  input.tab === "file" ? (openBlock(), createElementBlock("div", _hoisted_14, _cache[3] || (_cache[3] = [
                    createBaseVNode("i", { class: "bi bi-exclamation-triangle text-warning me-1" }, null, -1),
                    createBaseVNode("small", null, "File will need to be re-uploaded", -1)
                  ]))) : createCommentVNode("", true)
                ]),
                createBaseVNode("div", _hoisted_15, [
                  createBaseVNode("button", {
                    onClick: withModifiers(($event) => removeInput(index), ["stop"]),
                    class: "btn btn-sm btn-outline-danger",
                    title: "Remove from history"
                  }, _cache[4] || (_cache[4] = [
                    createBaseVNode("i", { class: "bi bi-x" }, null, -1)
                  ]), 8, _hoisted_16)
                ])
              ], 8, _hoisted_7);
            }), 128))
          ]),
          !unref(hasRecentInputs2) ? (openBlock(), createElementBlock("div", _hoisted_17, _cache[5] || (_cache[5] = [
            createBaseVNode("i", { class: "bi bi-clock-history text-muted" }, null, -1),
            createBaseVNode("p", { class: "text-muted" }, "No recent inputs", -1),
            createBaseVNode("small", { class: "text-muted" }, "Your recent uploads and inputs will appear here", -1)
          ]))) : createCommentVNode("", true)
        ])
      ])) : createCommentVNode("", true);
    };
  }
};
const RecentInputs = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-95cbee23"]]);
export {
  RecentInputs as R,
  analyze as a,
  api as b,
  useRecentInputs as u
};
//# sourceMappingURL=RecentInputs-D51yqGnz.js.map
