import { r as ref, D as onUnmounted, p as computed, c as createElementBlock, o as openBlock, b as createBaseVNode, l as createCommentVNode, B as normalizeStyle, t as toDisplayString, x as normalizeClass, F as Fragment, n as renderList, g as createTextVNode, E as watch, h as createBlock, y as withDirectives, z as vModelText, d as createVNode, v as createStaticVNode, A as withModifiers, G as withKeys, w as withCtx, T as Transition, f as resolveComponent, s as onMounted, u as useRoute, C as useRouter, H as nextTick } from "./vendor-0f3ixpnm.js";
import { c as createLoader, _ as _export_sfc } from "./index-BAtGweOG.js";
import { R as RecentInputs, b as api, a as analyze } from "./RecentInputs-R_Im7MPW.js";
function useApi(options = {}) {
  const {
    loadingMessage: loadingMessage2 = "Loading...",
    showLoading = true,
    onSuccess,
    onError,
    onFinally
  } = options;
  const data = ref(null);
  const error = ref(null);
  const isLoading2 = ref(false);
  const status = ref(null);
  let loader = null;
  let controller = null;
  const callId = `api_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  onUnmounted(() => {
    if (controller) {
      controller.abort();
    }
    if (loader) {
      loader.remove();
    }
  });
  async function execute(apiCall, callOptions = {}) {
    var _a;
    const {
      message = loadingMessage2,
      showLoader = showLoading,
      signal,
      ...requestConfig
    } = { ...options, ...callOptions };
    error.value = null;
    status.value = null;
    data.value = null;
    if (showLoader) {
      loader = createLoader(callId, { message });
    }
    isLoading2.value = true;
    if (typeof AbortController !== "undefined") {
      controller = new AbortController();
      requestConfig.signal = signal || controller.signal;
    }
    try {
      const response = await apiCall({
        ...requestConfig,
        signal: requestConfig.signal
      });
      data.value = response.data || response;
      status.value = response.status || 200;
      if (onSuccess) {
        onSuccess(response);
      }
      return response;
    } catch (err) {
      error.value = err;
      status.value = ((_a = err.response) == null ? void 0 : _a.status) || 0;
      if (onError) {
        onError(err);
      }
      throw err;
    } finally {
      isLoading2.value = false;
      if (loader) {
        if (error.value) {
          loader.error(error.value);
        } else {
          loader.complete();
        }
        loader = null;
      }
      if (onFinally) {
        onFinally();
      }
      controller = null;
    }
  }
  function cancel() {
    if (controller) {
      controller.abort();
      controller = null;
    }
    if (loader) {
      loader.remove();
      loader = null;
    }
    isLoading2.value = false;
  }
  return {
    execute,
    cancel,
    data,
    error,
    isLoading: isLoading2,
    status
  };
}
const isLoading = ref(false);
const loadingMessage = ref("Loading...");
function useLoadingState() {
  const setLoading = (value, message = "Loading...") => {
    isLoading.value = value;
    if (message) {
      loadingMessage.value = message;
    }
  };
  const showLoading = (message) => {
    setLoading(true, message);
  };
  const hideLoading = () => {
    setLoading(false);
  };
  const toggleLoading = (message) => {
    setLoading(!isLoading.value, message);
  };
  return {
    // State
    isLoading: computed(() => isLoading.value),
    loadingMessage: computed(() => loadingMessage.value),
    // Actions
    setLoading,
    showLoading,
    hideLoading,
    toggleLoading
  };
}
function useProcessingTime() {
  const startTime = ref(null);
  const estimatedTotalTime = ref(0);
  const currentStep = ref("");
  const stepProgress = ref(0);
  const processingSteps = ref([]);
  const actualTimes = ref({});
  const citationInfo = ref(null);
  const rateLimitInfo = ref(null);
  const timeout = ref(null);
  const processingError = ref(null);
  const canRetry = ref(false);
  const elapsedTime = computed(() => {
    if (!startTime.value) return 0;
    return (Date.now() - startTime.value) / 1e3;
  });
  const remainingTime = computed(() => {
    if (!estimatedTotalTime.value) return 0;
    return Math.max(0, estimatedTotalTime.value - elapsedTime.value);
  });
  const totalProgress = computed(() => {
    if (!estimatedTotalTime.value) return 0;
    return Math.min(100, elapsedTime.value / estimatedTotalTime.value * 100);
  });
  const currentStepProgress = computed(() => {
    if (!processingSteps.value.length) return 0;
    const currentStepIndex = processingSteps.value.findIndex((step2) => step2.step === currentStep.value);
    if (currentStepIndex === -1) return 0;
    const step = processingSteps.value[currentStepIndex];
    const stepElapsed = elapsedTime.value - (step.startTime || 0);
    return Math.min(100, stepElapsed / step.estimated_time * 100);
  });
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };
  const startProcessing = (timeEstimate) => {
    var _a;
    startTime.value = Date.now();
    if (typeof timeEstimate === "object" && timeEstimate !== null && Array.isArray(timeEstimate.steps)) {
      estimatedTotalTime.value = timeEstimate.estimated_total_time;
      processingSteps.value = timeEstimate.steps.map((step) => ({
        step: step[0],
        estimated_time: step[1],
        startTime: null,
        progress: 0
      }));
      currentStep.value = ((_a = processingSteps.value[0]) == null ? void 0 : _a.step) || "";
    } else if (typeof timeEstimate === "number") {
      estimatedTotalTime.value = timeEstimate;
      processingSteps.value = [];
      currentStep.value = "";
    } else {
      estimatedTotalTime.value = 0;
      processingSteps.value = [];
      currentStep.value = "";
    }
    stepProgress.value = 0;
  };
  const stopProcessing = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = "";
    stepProgress.value = 0;
  };
  const updateProgress = (progress) => {
    if (typeof progress === "object" && progress.step) {
      updateStep(progress.step, progress.progress || 0);
    } else if (typeof progress === "number") {
      stepProgress.value = progress;
    }
  };
  const setSteps = (steps) => {
    if (Array.isArray(steps)) {
      processingSteps.value = steps.map((step) => ({
        step: typeof step === "string" ? step : step.step,
        estimated_time: typeof step === "object" ? step.estimated_time : 10,
        startTime: null,
        progress: 0
      }));
    }
  };
  const resetProcessing = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = "";
    stepProgress.value = 0;
    processingSteps.value = [];
    actualTimes.value = {};
    citationInfo.value = null;
    rateLimitInfo.value = null;
    timeout.value = null;
    processingError.value = null;
    canRetry.value = false;
  };
  const setProcessingError = (error) => {
    processingError.value = error;
    canRetry.value = true;
  };
  const updateStep = (stepName, progress) => {
    const stepIndex = processingSteps.value.findIndex((step) => step.step === stepName);
    if (stepIndex === -1) return;
    if (stepIndex === 0 || processingSteps.value[stepIndex - 1].progress === 100) {
      currentStep.value = stepName;
      if (!processingSteps.value[stepIndex].startTime) {
        processingSteps.value[stepIndex].startTime = Date.now();
      }
    }
    processingSteps.value[stepIndex].progress = progress;
    stepProgress.value = progress;
  };
  const completeStep = (stepName) => {
    updateStep(stepName, 100);
    const nextStepIndex = processingSteps.value.findIndex((step) => step.step === stepName) + 1;
    if (nextStepIndex < processingSteps.value.length) {
      currentStep.value = processingSteps.value[nextStepIndex].step;
      processingSteps.value[nextStepIndex].startTime = Date.now();
    }
  };
  const updateActualTimes = (times) => {
    actualTimes.value = times;
  };
  const reset = () => {
    startTime.value = null;
    estimatedTotalTime.value = 0;
    currentStep.value = "";
    stepProgress.value = 0;
    processingSteps.value = [];
    actualTimes.value = {};
    citationInfo.value = null;
    rateLimitInfo.value = null;
    timeout.value = null;
    processingError.value = null;
    canRetry.value = false;
  };
  return {
    // State
    startTime,
    estimatedTotalTime,
    currentStep,
    stepProgress,
    processingSteps,
    actualTimes,
    citationInfo,
    rateLimitInfo,
    timeout,
    processingError,
    canRetry,
    // Computed
    elapsedTime,
    remainingTime,
    totalProgress,
    currentStepProgress,
    // Methods
    startProcessing,
    stopProcessing,
    updateProgress,
    setSteps,
    resetProcessing,
    setProcessingError,
    updateStep,
    completeStep,
    updateActualTimes,
    reset,
    formatTime
  };
}
function useCitationNormalization() {
  const normalizeCitation = (citation) => {
    let score = 0;
    let scoreColor = "text-muted";
    if (citation.canonical_name && citation.canonical_name !== "N/A") {
      score += 2;
    }
    if (citation.extracted_case_name && citation.extracted_case_name !== "N/A" && citation.canonical_name && citation.canonical_name !== "N/A") {
      const canonicalWords = citation.canonical_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
      const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
      const commonWords = canonicalWords.filter((word) => extractedWords.includes(word));
      const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
      if (similarity >= 0.5) {
        score += 1;
      }
    }
    if (citation.canonical_date && citation.canonical_date !== "N/A") {
      score += 1;
    }
    if (citation.url && citation.url !== "") {
      score += 1;
    }
    if (score >= 4) {
      scoreColor = "text-success";
    } else if (score >= 2) {
      scoreColor = "text-warning";
    } else {
      scoreColor = "text-danger";
    }
    return {
      score,
      scoreColor,
      normalized: {
        canonical_name: citation.canonical_name || "N/A",
        extracted_case_name: citation.extracted_case_name || "N/A",
        canonical_date: citation.canonical_date || "N/A",
        extracted_date: citation.extracted_date || "N/A",
        url: citation.url || "",
        verified: citation.verified || false
      }
    };
  };
  const normalizeCitations = (citations) => {
    if (!Array.isArray(citations)) {
      return [];
    }
    return citations.map((citation) => {
      const normalized = normalizeCitation(citation);
      return {
        ...citation,
        ...normalized.normalized,
        score: normalized.score,
        scoreColor: normalized.scoreColor
      };
    });
  };
  const calculateCitationScore = (citation) => {
    return normalizeCitation(citation).score;
  };
  const calculateSimilarity = (citation) => {
    if (citation.canonical_name && citation.canonical_name !== "N/A") {
      return 1;
    }
    if (citation.extracted_case_name && citation.extracted_case_name !== "N/A" && citation.canonical_name && citation.canonical_name !== "N/A") {
      const canonicalWords = citation.canonical_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
      const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
      const commonWords = canonicalWords.filter((word) => extractedWords.includes(word));
      return commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
    }
    return 0;
  };
  return {
    normalizeCitation,
    normalizeCitations,
    calculateCitationScore,
    calculateSimilarity
  };
}
const _sfc_main$5 = {
  name: "ProcessingProgress",
  props: {
    elapsedTime: {
      type: Number,
      required: true
    },
    remainingTime: {
      type: Number,
      required: true
    },
    totalProgress: {
      type: Number,
      required: true
    },
    currentStep: {
      type: String,
      default: ""
    },
    currentStepProgress: {
      type: Number,
      default: 0
    },
    processingSteps: {
      type: Array,
      default: () => []
    },
    actualTimes: {
      type: Object,
      default: () => ({})
    },
    citationInfo: {
      type: Object,
      default: null
    },
    rateLimitInfo: {
      type: Object,
      default: null
    },
    error: {
      type: String,
      default: ""
    },
    canRetry: {
      type: Boolean,
      default: false
    },
    timeout: {
      type: Number,
      default: null
    }
  },
  mounted() {
  },
  watch: {
    totalProgress(newVal) {
    },
    remainingTime(newVal) {
    }
  },
  computed: {
    currentStepElapsed() {
      const step = this.processingSteps.find((s) => s.step === this.currentStep);
      return step ? Date.now() / 1e3 - step.start_time : 0;
    },
    currentStepRemaining() {
      const step = this.processingSteps.find((s) => s.step === this.currentStep);
      if (!step || !step.estimated_time) return 0;
      return Math.max(0, step.estimated_time - this.currentStepElapsed);
    },
    isTimeoutWarning() {
      if (!this.timeout) return false;
      const timeRemaining = this.timeout - this.elapsedTime;
      return timeRemaining < 60;
    }
  },
  methods: {
    formatTime(seconds) {
      if (seconds < 0) return "0s";
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      if (minutes > 0) {
        return `${minutes}m ${remainingSeconds}s`;
      }
      return `${remainingSeconds}s`;
    },
    getStepClass(step) {
      if (step.progress === 100) return "completed";
      if (step.step === this.currentStep) return "current";
      if (step.progress > 0) return "in-progress";
      return "pending";
    },
    getStepStatus(step) {
      if (step.progress === 100) return "Completed";
      if (step.step === this.currentStep) return "In Progress";
      if (step.progress > 0) return `${step.progress}%`;
      return "Pending";
    },
    formatProcessingRate(citationInfo) {
      if (!citationInfo.processed || !this.elapsedTime) return "0/min";
      const rate = citationInfo.processed / this.elapsedTime * 60;
      return `${Math.round(rate)}/min`;
    }
  }
};
const _hoisted_1$4 = { class: "processing-progress" };
const _hoisted_2$4 = { class: "progress-section" };
const _hoisted_3$3 = { class: "progress-bar" };
const _hoisted_4$3 = { class: "time-info" };
const _hoisted_5$3 = {
  key: 0,
  class: "citation-section"
};
const _hoisted_6$3 = { class: "citation-stats" };
const _hoisted_7$3 = { class: "stat" };
const _hoisted_8$3 = { class: "value" };
const _hoisted_9$3 = { class: "stat" };
const _hoisted_10$3 = { class: "value" };
const _hoisted_11$3 = { class: "stat" };
const _hoisted_12$3 = { class: "value" };
const _hoisted_13$3 = {
  key: 0,
  class: "stat"
};
const _hoisted_14$3 = { class: "value" };
const _hoisted_15$3 = {
  key: 0,
  class: "rate-limit-info"
};
const _hoisted_16$3 = { class: "stat" };
const _hoisted_17$3 = { class: "value" };
const _hoisted_18$3 = {
  key: 0,
  class: "stat"
};
const _hoisted_19$3 = { class: "value" };
const _hoisted_20$3 = {
  key: 1,
  class: "current-step"
};
const _hoisted_21$3 = { class: "step-info" };
const _hoisted_22$3 = { class: "step-name" };
const _hoisted_23$3 = { class: "progress-bar" };
const _hoisted_24$3 = { class: "time-info" };
const _hoisted_25$2 = { class: "steps-section" };
const _hoisted_26$2 = { class: "steps-list" };
const _hoisted_27$2 = { class: "step-header" };
const _hoisted_28$2 = { class: "step-name" };
const _hoisted_29$2 = { class: "step-status" };
const _hoisted_30$2 = {
  key: 0,
  class: "progress-bar"
};
const _hoisted_31$2 = {
  key: 1,
  class: "time-info"
};
const _hoisted_32$2 = { key: 0 };
const _hoisted_33$2 = {
  key: 2,
  class: "error-section"
};
const _hoisted_34$2 = { class: "error-message" };
function _sfc_render$1(_ctx, _cache, $props, $setup, $data, $options) {
  return openBlock(), createElementBlock("div", _hoisted_1$4, [
    createBaseVNode("div", _hoisted_2$4, [
      _cache[1] || (_cache[1] = createBaseVNode("h3", null, "Overall Progress", -1)),
      createBaseVNode("div", _hoisted_3$3, [
        createBaseVNode("div", {
          class: "progress-fill",
          style: normalizeStyle({ width: `${$props.totalProgress}%` })
        }, null, 4)
      ]),
      createBaseVNode("div", _hoisted_4$3, [
        createBaseVNode("span", null, "Elapsed: " + toDisplayString($options.formatTime($props.elapsedTime)), 1),
        createBaseVNode("span", null, "Remaining: " + toDisplayString($options.formatTime($props.remainingTime)), 1),
        $props.timeout ? (openBlock(), createElementBlock("span", {
          key: 0,
          class: normalizeClass(["timeout-info", { "warning": $options.isTimeoutWarning }])
        }, " Timeout: " + toDisplayString($options.formatTime($props.timeout - $props.elapsedTime)), 3)) : createCommentVNode("", true)
      ])
    ]),
    $props.citationInfo ? (openBlock(), createElementBlock("div", _hoisted_5$3, [
      _cache[8] || (_cache[8] = createBaseVNode("h3", null, "Citation Processing", -1)),
      createBaseVNode("div", _hoisted_6$3, [
        createBaseVNode("div", _hoisted_7$3, [
          _cache[2] || (_cache[2] = createBaseVNode("span", { class: "label" }, "Total Citations:", -1)),
          createBaseVNode("span", _hoisted_8$3, toDisplayString($props.citationInfo.total), 1)
        ]),
        createBaseVNode("div", _hoisted_9$3, [
          _cache[3] || (_cache[3] = createBaseVNode("span", { class: "label" }, "Unique Citations:", -1)),
          createBaseVNode("span", _hoisted_10$3, toDisplayString($props.citationInfo.unique), 1)
        ]),
        createBaseVNode("div", _hoisted_11$3, [
          _cache[4] || (_cache[4] = createBaseVNode("span", { class: "label" }, "Processed:", -1)),
          createBaseVNode("span", _hoisted_12$3, toDisplayString($props.citationInfo.processed), 1)
        ]),
        $props.citationInfo.unique ? (openBlock(), createElementBlock("div", _hoisted_13$3, [
          _cache[5] || (_cache[5] = createBaseVNode("span", { class: "label" }, "Processing Rate:", -1)),
          createBaseVNode("span", _hoisted_14$3, toDisplayString($options.formatProcessingRate($props.citationInfo)), 1)
        ])) : createCommentVNode("", true)
      ]),
      $props.rateLimitInfo ? (openBlock(), createElementBlock("div", _hoisted_15$3, [
        createBaseVNode("div", _hoisted_16$3, [
          _cache[6] || (_cache[6] = createBaseVNode("span", { class: "label" }, "API Rate Limit:", -1)),
          createBaseVNode("span", _hoisted_17$3, toDisplayString($props.rateLimitInfo.remaining) + "/" + toDisplayString($props.rateLimitInfo.limit), 1)
        ]),
        $props.rateLimitInfo.resetTime ? (openBlock(), createElementBlock("div", _hoisted_18$3, [
          _cache[7] || (_cache[7] = createBaseVNode("span", { class: "label" }, "Reset in:", -1)),
          createBaseVNode("span", _hoisted_19$3, toDisplayString($options.formatTime($props.rateLimitInfo.resetTime - Date.now() / 1e3)), 1)
        ])) : createCommentVNode("", true)
      ])) : createCommentVNode("", true)
    ])) : createCommentVNode("", true),
    $props.currentStep ? (openBlock(), createElementBlock("div", _hoisted_20$3, [
      _cache[9] || (_cache[9] = createBaseVNode("h3", null, "Current Step", -1)),
      createBaseVNode("div", _hoisted_21$3, [
        createBaseVNode("span", _hoisted_22$3, toDisplayString($props.currentStep), 1),
        createBaseVNode("div", _hoisted_23$3, [
          createBaseVNode("div", {
            class: "progress-fill",
            style: normalizeStyle({ width: `${$props.currentStepProgress}%` })
          }, null, 4)
        ]),
        createBaseVNode("div", _hoisted_24$3, [
          createBaseVNode("span", null, "Elapsed: " + toDisplayString($options.formatTime($options.currentStepElapsed)), 1),
          createBaseVNode("span", null, "Remaining: " + toDisplayString($options.formatTime($options.currentStepRemaining)), 1)
        ])
      ])
    ])) : createCommentVNode("", true),
    createBaseVNode("div", _hoisted_25$2, [
      _cache[10] || (_cache[10] = createBaseVNode("h3", null, "Processing Steps", -1)),
      createBaseVNode("div", _hoisted_26$2, [
        (openBlock(true), createElementBlock(Fragment, null, renderList($props.processingSteps, (step) => {
          return openBlock(), createElementBlock("div", {
            key: step.step,
            class: normalizeClass(["step", $options.getStepClass(step)])
          }, [
            createBaseVNode("div", _hoisted_27$2, [
              createBaseVNode("span", _hoisted_28$2, toDisplayString(step.step), 1),
              createBaseVNode("span", _hoisted_29$2, toDisplayString($options.getStepStatus(step)), 1)
            ]),
            step.progress !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_30$2, [
              createBaseVNode("div", {
                class: "progress-fill",
                style: normalizeStyle({ width: `${step.progress}%` })
              }, null, 4)
            ])) : createCommentVNode("", true),
            step.estimated_time ? (openBlock(), createElementBlock("div", _hoisted_31$2, [
              createBaseVNode("span", null, "Estimated: " + toDisplayString($options.formatTime(step.estimated_time)), 1),
              step.actual_time ? (openBlock(), createElementBlock("span", _hoisted_32$2, "Actual: " + toDisplayString($options.formatTime(step.actual_time)), 1)) : createCommentVNode("", true)
            ])) : createCommentVNode("", true)
          ], 2);
        }), 128))
      ])
    ]),
    $props.error ? (openBlock(), createElementBlock("div", _hoisted_33$2, [
      createBaseVNode("div", _hoisted_34$2, [
        _cache[11] || (_cache[11] = createBaseVNode("i", { class: "fas fa-exclamation-circle" }, null, -1)),
        createTextVNode(" " + toDisplayString($props.error), 1)
      ]),
      $props.canRetry ? (openBlock(), createElementBlock("button", {
        key: 0,
        onClick: _cache[0] || (_cache[0] = ($event) => _ctx.$emit("retry")),
        class: "retry-button"
      }, " Retry Processing ")) : createCommentVNode("", true)
    ])) : createCommentVNode("", true)
  ]);
}
const ProcessingProgress = /* @__PURE__ */ _export_sfc(_sfc_main$5, [["render", _sfc_render$1], ["__scopeId", "data-v-c1f312dc"]]);
const _hoisted_1$3 = { class: "citation-results" };
const _hoisted_2$3 = {
  key: 0,
  class: "loading-state"
};
const _hoisted_3$2 = {
  key: 1,
  class: "error-state"
};
const _hoisted_4$2 = {
  key: 2,
  class: "results-content"
};
const _hoisted_5$2 = { class: "results-header" };
const _hoisted_6$2 = { class: "header-content" };
const _hoisted_7$2 = { class: "summary-stats" };
const _hoisted_8$2 = { class: "stat-item verified" };
const _hoisted_9$2 = { class: "stat-number" };
const _hoisted_10$2 = { class: "stat-item invalid" };
const _hoisted_11$2 = { class: "stat-number" };
const _hoisted_12$2 = { class: "stat-item total" };
const _hoisted_13$2 = { class: "stat-number" };
const _hoisted_14$2 = { class: "action-buttons" };
const _hoisted_15$2 = { class: "filter-section" };
const _hoisted_16$2 = { class: "filter-controls" };
const _hoisted_17$2 = ["onClick"];
const _hoisted_18$2 = { class: "search-box" };
const _hoisted_19$2 = { class: "citations-list" };
const _hoisted_20$2 = { class: "cluster-header" };
const _hoisted_21$2 = { key: 0 };
const _hoisted_22$2 = { key: 1 };
const _hoisted_23$2 = {
  key: 2,
  class: "canonical-date"
};
const _hoisted_24$2 = {
  key: 0,
  class: "extracted-info"
};
const _hoisted_25$1 = { class: "extracted-name" };
const _hoisted_26$1 = {
  key: 0,
  class: "extracted-date"
};
const _hoisted_27$1 = { class: "cluster-meta" };
const _hoisted_28$1 = { class: "cluster-size" };
const _hoisted_29$1 = { key: 0 };
const _hoisted_30$1 = { key: 0 };
const _hoisted_31$1 = ["href"];
const _hoisted_32$1 = { class: "cluster-citations" };
const _hoisted_33$1 = { class: "citation-row" };
const _hoisted_34$1 = { class: "citation-text" };
const _hoisted_35$1 = {
  key: 3,
  class: "results-content"
};
const _hoisted_36$1 = { class: "results-header" };
const _hoisted_37$1 = { class: "header-content" };
const _hoisted_38$1 = { class: "summary-stats" };
const _hoisted_39$1 = { class: "stat-item verified" };
const _hoisted_40$1 = { class: "stat-number" };
const _hoisted_41$1 = { class: "stat-item invalid" };
const _hoisted_42$1 = { class: "stat-number" };
const _hoisted_43$1 = { class: "stat-item total" };
const _hoisted_44$1 = { class: "stat-number" };
const _hoisted_45$1 = { class: "action-buttons" };
const _hoisted_46$1 = { class: "filter-section" };
const _hoisted_47$1 = { class: "filter-controls" };
const _hoisted_48$1 = ["onClick"];
const _hoisted_49$1 = { class: "search-box" };
const _hoisted_50$1 = {
  key: 0,
  class: "citations-list"
};
const _hoisted_51$1 = { class: "citation-header" };
const _hoisted_52 = { class: "citation-main" };
const _hoisted_53 = { class: "citation-score" };
const _hoisted_54 = ["title"];
const _hoisted_55 = { class: "citation-content" };
const _hoisted_56 = { class: "citation-link" };
const _hoisted_57 = ["href"];
const _hoisted_58 = {
  key: 0,
  class: "canonical-info"
};
const _hoisted_59 = { class: "canonical-details" };
const _hoisted_60 = ["href"];
const _hoisted_61 = {
  key: 1,
  class: "extracted-info"
};
const _hoisted_62 = { class: "extracted-details" };
const _hoisted_63 = {
  key: 2,
  class: "no-extraction"
};
const _hoisted_64 = { class: "citation-meta" };
const _hoisted_65 = { class: "source" };
const _hoisted_66 = {
  key: 0,
  class: "method"
};
const _hoisted_67 = { class: "citation-actions" };
const _hoisted_68 = ["onClick"];
const _hoisted_69 = {
  key: 0,
  class: "citation-details"
};
const _hoisted_70 = { class: "detail-section" };
const _hoisted_71 = { class: "detail-row" };
const _hoisted_72 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_73 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_74 = {
  key: 2,
  class: "detail-row"
};
const _hoisted_75 = {
  key: 3,
  class: "detail-row"
};
const _hoisted_76 = { class: "text-danger" };
const _hoisted_77 = {
  key: 4,
  class: "detail-row"
};
const _hoisted_78 = { class: "parallel-citations" };
const _hoisted_79 = {
  key: 0,
  class: "pagination"
};
const _hoisted_80 = ["disabled"];
const _hoisted_81 = { class: "pagination-info" };
const _hoisted_82 = ["disabled"];
const _hoisted_83 = {
  key: 4,
  class: "no-results-state"
};
const itemsPerPage = 50;
const _sfc_main$4 = {
  __name: "CitationResults",
  props: {
    results: { type: Object, default: null },
    showLoading: { type: Boolean, default: false },
    error: { type: String, default: "" }
  },
  emits: ["copy-results", "download-results", "toast"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const activeFilter = ref("all");
    const searchQuery = ref("");
    const currentPage = ref(1);
    const expandedCitations = ref(/* @__PURE__ */ new Set());
    const progress = ref(0);
    const etaSeconds = ref(null);
    watch(() => props.results, (newVal) => {
      if (newVal && typeof newVal.progress === "number") {
        progress.value = newVal.progress;
        etaSeconds.value = newVal.eta_seconds;
      }
    });
    const shouldShowProgressBar = computed(() => {
      return props.showLoading && progress.value > 0 && progress.value < 100;
    });
    const validCount = computed(() => {
      var _a, _b;
      if (((_a = props.results) == null ? void 0 : _a.clusters) && props.results.clusters.length > 0) {
        return props.results.clusters.reduce((total, cluster) => {
          return total + cluster.citations.filter((c) => c.verified === "true" || c.verified === true).length;
        }, 0);
      }
      if (!((_b = props.results) == null ? void 0 : _b.citations)) return 0;
      return props.results.citations.filter((c) => c.verified === "true" || c.verified === true).length;
    });
    const invalidCount = computed(() => {
      var _a, _b;
      if (((_a = props.results) == null ? void 0 : _a.clusters) && props.results.clusters.length > 0) {
        return props.results.clusters.reduce((total, cluster) => {
          return total + cluster.citations.filter((c) => c.verified === "false" || c.verified === false).length;
        }, 0);
      }
      if (!((_b = props.results) == null ? void 0 : _b.citations)) return 0;
      return props.results.citations.filter((c) => c.verified === "false" || c.verified === false).length;
    });
    const filteredClusters = computed(() => {
      var _a;
      if (!((_a = props.results) == null ? void 0 : _a.clusters) || props.results.clusters.length === 0) {
        return [];
      }
      return props.results.clusters.map((cluster) => {
        let filteredCitations2 = cluster.citations.filter((c) => !isStatuteOrRegulation(c));
        if (activeFilter.value === "verified") {
          filteredCitations2 = filteredCitations2.filter((c) => c.verified === "true" || c.verified === true);
        } else if (activeFilter.value === "invalid") {
          filteredCitations2 = filteredCitations2.filter((c) => c.verified === "false" || c.verified === false);
        }
        if (searchQuery.value.trim()) {
          const query = searchQuery.value.toLowerCase();
          filteredCitations2 = filteredCitations2.filter(
            (c) => c.citation && c.citation.toLowerCase().includes(query) || c.canonical_citation && c.canonical_citation.toLowerCase().includes(query) || c.primary_citation && c.primary_citation.toLowerCase().includes(query) || getCaseName(c) && getCaseName(c).toLowerCase().includes(query)
          );
        }
        if (filteredCitations2.length > 0) {
          return {
            ...cluster,
            citations: filteredCitations2,
            size: filteredCitations2.length
          };
        }
        return null;
      }).filter((cluster) => cluster !== null);
    });
    const filteredCitations = computed(() => {
      var _a, _b;
      if (((_a = props.results) == null ? void 0 : _a.clusters) && props.results.clusters.length > 0) {
        return filteredClusters.value.flatMap((cluster) => cluster.citations);
      }
      if (!((_b = props.results) == null ? void 0 : _b.citations)) return [];
      let filtered = props.results.citations;
      filtered = filtered.filter((c) => !isStatuteOrRegulation(c));
      if (activeFilter.value === "verified") {
        filtered = filtered.filter((c) => c.verified === "true" || c.verified === true);
      } else if (activeFilter.value === "invalid") {
        filtered = filtered.filter((c) => c.verified === "false" || c.verified === false);
      }
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(
          (c) => c.citation && c.citation.toLowerCase().includes(query) || c.canonical_citation && c.canonical_citation.toLowerCase().includes(query) || c.primary_citation && c.primary_citation.toLowerCase().includes(query) || getCaseName(c) && getCaseName(c).toLowerCase().includes(query)
        );
      }
      return filtered;
    });
    const isStatuteOrRegulation = (citation) => {
      const citationText = citation.citation || citation.canonical_citation || citation.primary_citation || "";
      const text = citationText.toUpperCase();
      if (text.includes("U.S.C.") || text.includes("USC") || text.includes("C.F.R.") || text.includes("CFR") || text.includes("UNITED STATES CODE") || text.includes("CODE OF FEDERAL REGULATIONS")) {
        return true;
      }
      return /\d+\s+U\.?\s*S\.?\s*C\.?\s*[§]?\s*\d+/i.test(text) || /\d+\s+C\.?\s*F\.?\s*R\.?\s*[§]?\s*\d+/i.test(text);
    };
    const totalPages = computed(() => Math.ceil(filteredCitations.value.length / itemsPerPage));
    const paginatedCitations = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return filteredCitations.value.slice(start, end);
    });
    const filters = computed(() => [
      { value: "all", label: "All", count: filteredCitations.value.length },
      { value: "verified", label: "Verified", count: validCount.value },
      { value: "invalid", label: "Invalid", count: invalidCount.value }
    ]);
    const getCaseName = (citation) => {
      return citation.case_name || citation.canonical_name || citation.extracted_case_name || null;
    };
    const getCanonicalCaseName = (citation) => {
      return citation.case_name || citation.canonical_name || null;
    };
    const getExtractedCaseName = (citation) => {
      const value = citation.extracted_case_name;
      return value && value !== "N/A" ? value : null;
    };
    const getCanonicalDate = (citation) => {
      return citation.canonical_date || null;
    };
    const getExtractedDate = (citation) => {
      const value = citation.extracted_date;
      return value && value !== "N/A" ? value : null;
    };
    const getCitation = (citation) => {
      return citation.citation || citation.canonical_citation || citation.primary_citation || "N/A";
    };
    const getCitationUrl = (citation) => {
      return citation.url || null;
    };
    const getSource = (citation) => {
      return citation.source || "Unknown";
    };
    const getVerificationMethod = (citation) => {
      return citation.verification_method || "N/A";
    };
    const getConfidence = (citation) => {
      return citation.confidence || citation.likelihood_score || "N/A";
    };
    const getError = (citation) => {
      return citation.error || citation.explanation || null;
    };
    const getVerificationStatus = (citation) => {
      if (citation.verified === "true" || citation.verified === true) return "verified";
      if (citation.verified === "true_by_parallel") return "true_by_parallel";
      return "unverified";
    };
    const isVerified = (citation) => {
      const status = getVerificationStatus(citation);
      return status === "verified" || status === "true_by_parallel";
    };
    const areCaseNamesSimilar = (canonical, extracted) => {
      if (!canonical || !extracted) return false;
      if (canonical === "N/A" || extracted === "N/A") return false;
      const normalize = (name) => {
        return name.toLowerCase().replace(/[^\w\s]/g, " ").replace(/\s+/g, " ").trim();
      };
      const norm1 = normalize(canonical);
      const norm2 = normalize(extracted);
      if (norm1 === norm2) return true;
      const words1 = norm1.split(" ");
      const words2 = norm2.split(" ");
      const commonWords = words1.filter((word) => words2.includes(word) && word.length > 2);
      return commonWords.length >= Math.min(words1.length, words2.length) * 0.6;
    };
    const areDatesSimilar = (canonical, extracted) => {
      if (!canonical || !extracted) return false;
      const getYear = (dateStr) => {
        const match = dateStr.match(/\d{4}/);
        return match ? match[0] : null;
      };
      const year1 = getYear(canonical);
      const year2 = getYear(extracted);
      return year1 && year2 && year1 === year2;
    };
    const getCitationStatusClass = (citation) => {
      const status = getVerificationStatus(citation);
      if (status === "verified") return "citation-verified";
      if (status === "true_by_parallel") return "citation-parallel";
      return "citation-unverified";
    };
    const getCaseNameClass = (citation) => {
      const canonical = getCanonicalCaseName(citation);
      const extracted = getExtractedCaseName(citation);
      if (areCaseNamesSimilar(canonical, extracted)) return "name-similar";
      return "name-different";
    };
    const getDateClass = (citation) => {
      const canonical = getCanonicalDate(citation);
      const extracted = getExtractedDate(citation);
      if (areDatesSimilar(canonical, extracted)) return "date-similar";
      return "date-different";
    };
    const getScoreClass = (citation) => {
      const confidence = getConfidence(citation);
      if (typeof confidence === "number") {
        if (confidence >= 0.8) return "green";
        if (confidence >= 0.6) return "yellow";
        if (confidence >= 0.4) return "orange";
        return "red";
      }
      return isVerified(citation) ? "green" : "red";
    };
    const getScoreDisplay = (citation) => {
      const confidence = getConfidence(citation);
      if (typeof confidence === "number") {
        return Math.round(confidence * 100) + "%";
      }
      return isVerified(citation) ? "✓" : "✗";
    };
    const formatYear = (dateStr) => {
      if (!dateStr) return null;
      const match = dateStr.match(/\d{4}/);
      return match ? match[0] : dateStr;
    };
    const toggleExpanded = (citationKey) => {
      if (expandedCitations.value.has(citationKey)) {
        expandedCitations.value.delete(citationKey);
      } else {
        expandedCitations.value.add(citationKey);
      }
    };
    const resetPagination = () => {
      currentPage.value = 1;
    };
    watch(activeFilter, resetPagination);
    watch(searchQuery, resetPagination);
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$3, [
        __props.showLoading ? (openBlock(), createElementBlock("div", _hoisted_2$3, [
          _cache[8] || (_cache[8] = createBaseVNode("div", { class: "loading-spinner" }, null, -1)),
          _cache[9] || (_cache[9] = createBaseVNode("p", null, "Processing citations...", -1)),
          shouldShowProgressBar.value ? (openBlock(), createBlock(ProcessingProgress, {
            key: 0,
            "elapsed-time": 0,
            "remaining-time": etaSeconds.value || 0,
            "total-progress": progress.value,
            "current-step": "Processing Citations",
            "current-step-progress": progress.value,
            "processing-steps": [],
            "citation-info": null,
            "rate-limit-info": null,
            error: "",
            "can-retry": false,
            timeout: null
          }, null, 8, ["remaining-time", "total-progress", "current-step-progress"])) : createCommentVNode("", true)
        ])) : __props.error ? (openBlock(), createElementBlock("div", _hoisted_3$2, [
          _cache[10] || (_cache[10] = createBaseVNode("div", { class: "error-icon" }, "⚠️", -1)),
          _cache[11] || (_cache[11] = createBaseVNode("h3", null, "Error Processing Citations", -1)),
          createBaseVNode("p", null, toDisplayString(__props.error), 1)
        ])) : __props.results && filteredClusters.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_4$2, [
          createBaseVNode("div", _hoisted_5$2, [
            createBaseVNode("div", _hoisted_6$2, [
              _cache[15] || (_cache[15] = createBaseVNode("h2", null, "Citation Verification Results", -1)),
              createBaseVNode("div", _hoisted_7$2, [
                createBaseVNode("div", _hoisted_8$2, [
                  createBaseVNode("span", _hoisted_9$2, toDisplayString(validCount.value), 1),
                  _cache[12] || (_cache[12] = createBaseVNode("span", { class: "stat-label" }, "Verified", -1))
                ]),
                createBaseVNode("div", _hoisted_10$2, [
                  createBaseVNode("span", _hoisted_11$2, toDisplayString(invalidCount.value), 1),
                  _cache[13] || (_cache[13] = createBaseVNode("span", { class: "stat-label" }, "Invalid", -1))
                ]),
                createBaseVNode("div", _hoisted_12$2, [
                  createBaseVNode("span", _hoisted_13$2, toDisplayString(filteredCitations.value.length), 1),
                  _cache[14] || (_cache[14] = createBaseVNode("span", { class: "stat-label" }, "Total (excluding statutes)", -1))
                ])
              ])
            ]),
            createBaseVNode("div", _hoisted_14$2, [
              createBaseVNode("button", {
                class: "action-btn copy-btn",
                onClick: _cache[0] || (_cache[0] = ($event) => _ctx.$emit("copy-results"))
              }, " Copy Results "),
              createBaseVNode("button", {
                class: "action-btn download-btn",
                onClick: _cache[1] || (_cache[1] = ($event) => _ctx.$emit("download-results"))
              }, " Download ")
            ])
          ]),
          createBaseVNode("div", _hoisted_15$2, [
            createBaseVNode("div", _hoisted_16$2, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(filters.value, (filter) => {
                return openBlock(), createElementBlock("button", {
                  key: filter.value,
                  class: normalizeClass(["filter-btn", { active: activeFilter.value === filter.value }]),
                  onClick: ($event) => activeFilter.value = filter.value
                }, toDisplayString(filter.label) + " (" + toDisplayString(filter.count) + ") ", 11, _hoisted_17$2);
              }), 128))
            ]),
            createBaseVNode("div", _hoisted_18$2, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => searchQuery.value = $event),
                type: "text",
                placeholder: "Search citations...",
                class: "search-input"
              }, null, 512), [
                [vModelText, searchQuery.value]
              ])
            ])
          ]),
          createBaseVNode("div", _hoisted_19$2, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(filteredClusters.value, (cluster) => {
              return openBlock(), createElementBlock("div", {
                key: cluster.cluster_id,
                class: "cluster-item"
              }, [
                createBaseVNode("div", _hoisted_20$2, [
                  createBaseVNode("h3", null, [
                    cluster.canonical_name && cluster.canonical_name !== "N/A" ? (openBlock(), createElementBlock("span", _hoisted_21$2, toDisplayString(cluster.canonical_name), 1)) : (openBlock(), createElementBlock("span", _hoisted_22$2, "Unverified Cluster")),
                    cluster.canonical_date ? (openBlock(), createElementBlock("span", _hoisted_23$2, " (" + toDisplayString(formatYear(cluster.canonical_date)) + ") ", 1)) : createCommentVNode("", true)
                  ]),
                  cluster.extracted_case_name && cluster.extracted_case_name !== "N/A" ? (openBlock(), createElementBlock("div", _hoisted_24$2, [
                    _cache[16] || (_cache[16] = createBaseVNode("span", { class: "extracted-label" }, "Extracted from document:", -1)),
                    createBaseVNode("span", _hoisted_25$1, toDisplayString(cluster.extracted_case_name), 1),
                    cluster.extracted_date ? (openBlock(), createElementBlock("span", _hoisted_26$1, " (" + toDisplayString(formatYear(cluster.extracted_date)) + ") ", 1)) : createCommentVNode("", true)
                  ])) : createCommentVNode("", true),
                  createBaseVNode("div", _hoisted_27$1, [
                    createBaseVNode("span", _hoisted_28$1, [
                      createTextVNode(toDisplayString(cluster.size) + " citation", 1),
                      cluster.size > 1 ? (openBlock(), createElementBlock("span", _hoisted_29$1, "s")) : createCommentVNode("", true)
                    ]),
                    cluster.url ? (openBlock(), createElementBlock("span", _hoisted_30$1, [
                      createBaseVNode("a", {
                        href: cluster.url,
                        target: "_blank"
                      }, "View on CourtListener", 8, _hoisted_31$1)
                    ])) : createCommentVNode("", true)
                  ])
                ]),
                createBaseVNode("div", _hoisted_32$1, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(cluster.citations, (citation) => {
                    return openBlock(), createElementBlock("div", {
                      key: citation.citation,
                      class: "citation-item"
                    }, [
                      createBaseVNode("div", _hoisted_33$1, [
                        createBaseVNode("span", _hoisted_34$1, toDisplayString(getCitation(citation)), 1),
                        createBaseVNode("span", {
                          class: normalizeClass(["verification-status", getVerificationStatus(citation)])
                        }, toDisplayString(getVerificationStatus(citation).replace("_", " ")), 3)
                      ])
                    ]);
                  }), 128))
                ])
              ]);
            }), 128))
          ])
        ])) : __props.results && __props.results.citations && __props.results.citations.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_35$1, [
          createBaseVNode("div", _hoisted_36$1, [
            createBaseVNode("div", _hoisted_37$1, [
              _cache[20] || (_cache[20] = createBaseVNode("h2", null, "Citation Verification Results", -1)),
              createBaseVNode("div", _hoisted_38$1, [
                createBaseVNode("div", _hoisted_39$1, [
                  createBaseVNode("span", _hoisted_40$1, toDisplayString(validCount.value), 1),
                  _cache[17] || (_cache[17] = createBaseVNode("span", { class: "stat-label" }, "Verified", -1))
                ]),
                createBaseVNode("div", _hoisted_41$1, [
                  createBaseVNode("span", _hoisted_42$1, toDisplayString(invalidCount.value), 1),
                  _cache[18] || (_cache[18] = createBaseVNode("span", { class: "stat-label" }, "Invalid", -1))
                ]),
                createBaseVNode("div", _hoisted_43$1, [
                  createBaseVNode("span", _hoisted_44$1, toDisplayString(filteredCitations.value.length), 1),
                  _cache[19] || (_cache[19] = createBaseVNode("span", { class: "stat-label" }, "Total (excluding statutes)", -1))
                ])
              ])
            ]),
            createBaseVNode("div", _hoisted_45$1, [
              createBaseVNode("button", {
                class: "action-btn copy-btn",
                onClick: _cache[3] || (_cache[3] = ($event) => _ctx.$emit("copy-results"))
              }, " Copy Results "),
              createBaseVNode("button", {
                class: "action-btn download-btn",
                onClick: _cache[4] || (_cache[4] = ($event) => _ctx.$emit("download-results"))
              }, " Download ")
            ])
          ]),
          createBaseVNode("div", _hoisted_46$1, [
            createBaseVNode("div", _hoisted_47$1, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(filters.value, (filter) => {
                return openBlock(), createElementBlock("button", {
                  key: filter.value,
                  class: normalizeClass(["filter-btn", { active: activeFilter.value === filter.value }]),
                  onClick: ($event) => activeFilter.value = filter.value
                }, toDisplayString(filter.label) + " (" + toDisplayString(filter.count) + ") ", 11, _hoisted_48$1);
              }), 128))
            ]),
            createBaseVNode("div", _hoisted_49$1, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => searchQuery.value = $event),
                type: "text",
                placeholder: "Search citations...",
                class: "search-input"
              }, null, 512), [
                [vModelText, searchQuery.value]
              ])
            ])
          ]),
          filteredCitations.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_50$1, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(paginatedCitations.value, (citation) => {
              return openBlock(), createElementBlock("div", {
                key: getCitation(citation),
                class: normalizeClass(["citation-item", { verified: isVerified(citation), invalid: !isVerified(citation) }])
              }, [
                createBaseVNode("div", _hoisted_51$1, [
                  createBaseVNode("div", _hoisted_52, [
                    createBaseVNode("div", _hoisted_53, [
                      createBaseVNode("span", {
                        class: normalizeClass(["score-badge", getScoreClass(citation)]),
                        title: "Confidence: " + getConfidence(citation)
                      }, toDisplayString(getScoreDisplay(citation)), 11, _hoisted_54)
                    ]),
                    createBaseVNode("div", _hoisted_55, [
                      createBaseVNode("div", _hoisted_56, [
                        getCitationUrl(citation) ? (openBlock(), createElementBlock("a", {
                          key: 0,
                          href: getCitationUrl(citation),
                          target: "_blank",
                          class: normalizeClass(["citation-hyperlink", getCitationStatusClass(citation)])
                        }, toDisplayString(getCitation(citation)), 11, _hoisted_57)) : (openBlock(), createElementBlock("span", {
                          key: 1,
                          class: normalizeClass(["citation-text", getCitationStatusClass(citation)])
                        }, toDisplayString(getCitation(citation)), 3))
                      ]),
                      getCanonicalCaseName(citation) ? (openBlock(), createElementBlock("div", _hoisted_58, [
                        _cache[21] || (_cache[21] = createBaseVNode("div", { class: "canonical-label" }, "Canonical:", -1)),
                        createBaseVNode("div", _hoisted_59, [
                          getCitationUrl(citation) ? (openBlock(), createElementBlock("a", {
                            key: 0,
                            href: getCitationUrl(citation),
                            target: "_blank",
                            class: normalizeClass(["canonical-name", getCaseNameClass(citation)])
                          }, toDisplayString(getCanonicalCaseName(citation)), 11, _hoisted_60)) : (openBlock(), createElementBlock("span", {
                            key: 1,
                            class: normalizeClass(["canonical-name", getCaseNameClass(citation)])
                          }, toDisplayString(getCanonicalCaseName(citation)), 3)),
                          getCanonicalDate(citation) ? (openBlock(), createElementBlock("span", {
                            key: 2,
                            class: normalizeClass(["canonical-date", getDateClass(citation)])
                          }, " (" + toDisplayString(formatYear(getCanonicalDate(citation))) + ") ", 3)) : createCommentVNode("", true)
                        ])
                      ])) : createCommentVNode("", true),
                      getExtractedCaseName(citation) || getExtractedDate(citation) ? (openBlock(), createElementBlock("div", _hoisted_61, [
                        _cache[22] || (_cache[22] = createBaseVNode("div", { class: "extracted-label" }, "Extracted from document:", -1)),
                        createBaseVNode("div", _hoisted_62, [
                          getExtractedCaseName(citation) ? (openBlock(), createElementBlock("span", {
                            key: 0,
                            class: normalizeClass(["extracted-name", getCaseNameClass(citation)])
                          }, toDisplayString(getExtractedCaseName(citation)), 3)) : createCommentVNode("", true),
                          getExtractedDate(citation) ? (openBlock(), createElementBlock("span", {
                            key: 1,
                            class: normalizeClass(["extracted-date", getDateClass(citation)])
                          }, " (" + toDisplayString(formatYear(getExtractedDate(citation))) + ") ", 3)) : createCommentVNode("", true),
                          !getExtractedCaseName(citation) && !getExtractedDate(citation) ? (openBlock(), createElementBlock("span", _hoisted_63, " No case name or date extracted ")) : createCommentVNode("", true)
                        ])
                      ])) : createCommentVNode("", true),
                      createBaseVNode("div", _hoisted_64, [
                        createBaseVNode("span", _hoisted_65, toDisplayString(getSource(citation)), 1),
                        getVerificationMethod(citation) !== "N/A" ? (openBlock(), createElementBlock("span", _hoisted_66, " via " + toDisplayString(getVerificationMethod(citation)), 1)) : createCommentVNode("", true),
                        createBaseVNode("span", {
                          class: normalizeClass(["verification-status", getVerificationStatus(citation)])
                        }, toDisplayString(getVerificationStatus(citation).replace("_", " ")), 3)
                      ])
                    ])
                  ]),
                  createBaseVNode("div", _hoisted_67, [
                    createBaseVNode("button", {
                      class: normalizeClass(["expand-btn", { expanded: expandedCitations.value.has(getCitation(citation)) }]),
                      onClick: ($event) => toggleExpanded(getCitation(citation))
                    }, toDisplayString(expandedCitations.value.has(getCitation(citation)) ? "−" : "+"), 11, _hoisted_68)
                  ])
                ]),
                expandedCitations.value.has(getCitation(citation)) ? (openBlock(), createElementBlock("div", _hoisted_69, [
                  createBaseVNode("div", _hoisted_70, [
                    _cache[29] || (_cache[29] = createBaseVNode("h4", { class: "section-title" }, "Citation Information", -1)),
                    createBaseVNode("div", _hoisted_71, [
                      _cache[23] || (_cache[23] = createBaseVNode("span", { class: "detail-label" }, "Status:", -1)),
                      createBaseVNode("span", {
                        class: normalizeClass({ "text-success": isVerified(citation), "text-danger": !isVerified(citation) })
                      }, toDisplayString(isVerified(citation) ? "Verified" : "Invalid"), 3)
                    ]),
                    citation.canonical_date ? (openBlock(), createElementBlock("div", _hoisted_72, [
                      _cache[24] || (_cache[24] = createBaseVNode("span", { class: "detail-label" }, "Date:", -1)),
                      createBaseVNode("span", null, toDisplayString(citation.canonical_date), 1)
                    ])) : createCommentVNode("", true),
                    citation.court ? (openBlock(), createElementBlock("div", _hoisted_73, [
                      _cache[25] || (_cache[25] = createBaseVNode("span", { class: "detail-label" }, "Court:", -1)),
                      createBaseVNode("span", null, toDisplayString(citation.court), 1)
                    ])) : createCommentVNode("", true),
                    citation.docket_number ? (openBlock(), createElementBlock("div", _hoisted_74, [
                      _cache[26] || (_cache[26] = createBaseVNode("span", { class: "detail-label" }, "Docket:", -1)),
                      createBaseVNode("span", null, toDisplayString(citation.docket_number), 1)
                    ])) : createCommentVNode("", true),
                    getError(citation) ? (openBlock(), createElementBlock("div", _hoisted_75, [
                      _cache[27] || (_cache[27] = createBaseVNode("span", { class: "detail-label" }, "Error:", -1)),
                      createBaseVNode("span", _hoisted_76, toDisplayString(getError(citation)), 1)
                    ])) : createCommentVNode("", true),
                    citation.parallel_citations && citation.parallel_citations.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_77, [
                      _cache[28] || (_cache[28] = createBaseVNode("span", { class: "detail-label" }, "Parallel Citations:", -1)),
                      createBaseVNode("div", _hoisted_78, [
                        (openBlock(true), createElementBlock(Fragment, null, renderList(citation.parallel_citations, (parallel) => {
                          return openBlock(), createElementBlock("span", {
                            key: parallel.citation,
                            class: "parallel-citation"
                          }, toDisplayString(parallel.citation), 1);
                        }), 128))
                      ])
                    ])) : createCommentVNode("", true)
                  ])
                ])) : createCommentVNode("", true)
              ], 2);
            }), 128)),
            totalPages.value > 1 ? (openBlock(), createElementBlock("div", _hoisted_79, [
              createBaseVNode("button", {
                disabled: currentPage.value === 1,
                onClick: _cache[6] || (_cache[6] = ($event) => currentPage.value = currentPage.value - 1),
                class: "pagination-btn"
              }, " Previous ", 8, _hoisted_80),
              createBaseVNode("span", _hoisted_81, " Page " + toDisplayString(currentPage.value) + " of " + toDisplayString(totalPages.value), 1),
              createBaseVNode("button", {
                disabled: currentPage.value === totalPages.value,
                onClick: _cache[7] || (_cache[7] = ($event) => currentPage.value = currentPage.value + 1),
                class: "pagination-btn"
              }, " Next ", 8, _hoisted_82)
            ])) : createCommentVNode("", true)
          ])) : createCommentVNode("", true)
        ])) : (openBlock(), createElementBlock("div", _hoisted_83, _cache[30] || (_cache[30] = [
          createBaseVNode("p", null, "No citation results to display.", -1)
        ])))
      ]);
    };
  }
};
const CitationResults = /* @__PURE__ */ _export_sfc(_sfc_main$4, [["__scopeId", "data-v-92fdc13c"]]);
const _hoisted_1$2 = { class: "unified-input" };
const _hoisted_2$2 = { class: "input-methods-top" };
const _hoisted_3$1 = { class: "method-icon" };
const _hoisted_4$1 = { class: "method-content" };
const _hoisted_5$1 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_6$1 = { class: "method-icon" };
const _hoisted_7$1 = { class: "method-content" };
const _hoisted_8$1 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_9$1 = {
  key: 0,
  class: "input-area-top"
};
const _hoisted_10$1 = {
  key: 0,
  class: "file-input"
};
const _hoisted_11$1 = ["disabled"];
const _hoisted_12$1 = {
  key: 0,
  class: "drop-zone-content"
};
const _hoisted_13$1 = {
  key: 1,
  class: "file-info"
};
const _hoisted_14$1 = { class: "file-details" };
const _hoisted_15$1 = {
  key: 0,
  class: "validation-errors"
};
const _hoisted_16$1 = {
  key: 1,
  class: "url-input"
};
const _hoisted_17$1 = { class: "url-input-container" };
const _hoisted_18$1 = { class: "input-wrapper" };
const _hoisted_19$1 = ["disabled"];
const _hoisted_20$1 = {
  key: 0,
  class: "input-status valid"
};
const _hoisted_21$1 = {
  key: 1,
  class: "input-status invalid"
};
const _hoisted_22$1 = { class: "input-footer" };
const _hoisted_23$1 = {
  key: 0,
  class: "url-preview"
};
const _hoisted_24$1 = {
  key: 1,
  class: "url-error"
};
const _hoisted_25 = {
  key: 2,
  class: "url-hint"
};
const _hoisted_26 = {
  key: 0,
  class: "validation-errors"
};
const _hoisted_27 = { class: "input-methods-bottom" };
const _hoisted_28 = { class: "method-icon" };
const _hoisted_29 = { class: "method-content" };
const _hoisted_30 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_31 = { class: "method-icon" };
const _hoisted_32 = { class: "method-content" };
const _hoisted_33 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_34 = { class: "analyze-section" };
const _hoisted_35 = ["disabled"];
const _hoisted_36 = {
  key: 0,
  class: "analyzing-spinner"
};
const _hoisted_37 = {
  key: 1,
  class: "analyze-icon"
};
const _hoisted_38 = {
  key: 0,
  class: "validation-summary"
};
const _hoisted_39 = {
  key: 1,
  class: "input-area-bottom"
};
const _hoisted_40 = {
  key: 0,
  class: "text-input"
};
const _hoisted_41 = { class: "textarea-container" };
const _hoisted_42 = ["disabled"];
const _hoisted_43 = {
  key: 0,
  class: "textarea-overlay"
};
const _hoisted_44 = { class: "input-footer" };
const _hoisted_45 = {
  key: 0,
  class: "min-length-hint"
};
const _hoisted_46 = {
  key: 0,
  class: "validation-errors"
};
const _hoisted_47 = {
  key: 1,
  class: "quick-citation-input-area"
};
const _hoisted_48 = { class: "quick-input-container" };
const _hoisted_49 = { class: "input-wrapper" };
const _hoisted_50 = ["disabled"];
const _hoisted_51 = {
  key: 0,
  class: "input-status valid"
};
const _sfc_main$3 = {
  __name: "UnifiedInput",
  props: {
    isAnalyzing: { type: Boolean, default: false }
  },
  emits: ["analyze"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const modeLabels = {
      text: "Paste Text",
      url: "URL",
      file: "Upload File",
      quick: "Quick Citation"
    };
    const modeDescriptions = {
      text: "Paste legal text or citations directly",
      url: "Analyze content from a web URL",
      file: "Upload a document for analysis",
      quick: "Enter a single citation and analyze instantly"
    };
    const methodIcons = {
      text: "📝",
      url: "🔗",
      file: "📁",
      quick: "🔎"
    };
    const VALIDATION_RULES = {
      text: {
        minLength: 10,
        maxLength: 5e4,
        minLengthMessage: "Text must be at least 10 characters long",
        maxLengthMessage: "Text is too long. Maximum 50,000 characters allowed."
      },
      url: {
        maxLength: 2048,
        maxLengthMessage: "URL is too long. Maximum 2,048 characters allowed."
      },
      file: {
        maxSize: 50 * 1024 * 1024,
        // 50MB
        allowedTypes: [".pdf", ".doc", ".docx", ".txt"],
        maxSizeMessage: "File is too large. Maximum 50MB allowed.",
        typeMessage: "Invalid file type. Please upload PDF, DOC, DOCX, or TXT files."
      }
    };
    const inputMode = ref("text");
    const text = ref("");
    const url = ref("");
    const file = ref(null);
    const isDragOver = ref(false);
    const fileInput = ref(null);
    const quickCitation = ref("");
    const validationErrors = ref({});
    const isDirty = ref({ text: false, url: false, file: false, quick: false });
    const showValidationWarning = ref(false);
    function validateText(text2) {
      const errors = [];
      const rules = VALIDATION_RULES.text;
      if (!text2.trim()) {
        errors.push("Text is required");
      } else if (text2.length < rules.minLength) {
        errors.push(rules.minLengthMessage);
      } else if (text2.length > rules.maxLength) {
        errors.push(rules.maxLengthMessage);
      }
      if (/[\x00-\x08\x0B\x0C\x0E-\x1F]/.test(text2)) {
        errors.push("Text contains invalid characters. Please remove any special characters.");
      }
      return errors;
    }
    function validateUrl(url2) {
      const errors = [];
      const rules = VALIDATION_RULES.url;
      if (!url2.trim()) {
        errors.push("URL is required");
      } else if (url2.length > rules.maxLength) {
        errors.push(rules.maxLengthMessage);
      } else {
        if (!/^https?:\/\//.test(url2)) {
          errors.push("URL must start with http:// or https://");
        } else if (!/\./.test(url2)) {
          errors.push("URL must contain a dot");
        }
      }
      return errors;
    }
    function validateFile(file2) {
      const errors = [];
      const rules = VALIDATION_RULES.file;
      if (!file2) {
        errors.push("Please select a file");
      } else {
        if (file2.size > rules.maxSize) {
          errors.push(rules.maxSizeMessage);
        }
        if (file2.size === 0) {
          errors.push("File is empty");
        }
        const extension = "." + file2.name.split(".").pop().toLowerCase();
        if (!rules.allowedTypes.includes(extension)) {
          errors.push(rules.typeMessage);
        }
      }
      return errors;
    }
    function validateCurrentInput() {
      const errors = {};
      if (inputMode.value === "text") {
        errors.text = validateText(text.value);
      } else if (inputMode.value === "url") {
        errors.url = validateUrl(url.value);
      } else if (inputMode.value === "file") {
        errors.file = validateFile(file.value);
      }
      validationErrors.value = errors;
    }
    function handleInputChange() {
      isDirty.value[inputMode.value] = true;
      showValidationWarning.value = false;
      validateCurrentInput();
      console.log("[handleInputChange] mode:", inputMode.value, "file:", file.value, "url:", url.value, "hasErrors:", hasErrors.value, "currentErrors:", currentErrors.value);
    }
    const currentErrors = computed(() => {
      return validationErrors.value[inputMode.value] || [];
    });
    const hasErrors = computed(() => {
      return currentErrors.value.length > 0;
    });
    const canAnalyze = computed(() => {
      let result = false;
      if (props.isAnalyzing) return false;
      if (inputMode.value === "text") {
        result = text.value.length >= VALIDATION_RULES.text.minLength && text.value.length <= VALIDATION_RULES.text.maxLength;
      } else if (inputMode.value === "url") {
        result = url.value.length > 0;
      } else if (inputMode.value === "file") {
        result = !!file.value;
      } else if (inputMode.value === "quick") {
        result = quickCitation.value.trim().length > 0;
      }
      console.log("[canAnalyze] mode:", inputMode.value, "result:", result, "file:", file.value, "url:", url.value, "hasErrors:", hasErrors.value, "currentErrors:", currentErrors.value);
      return result;
    });
    function onFileChange(e) {
      e.preventDefault();
      e.stopPropagation();
      file.value = e.target.files[0] || null;
      isDragOver.value = false;
      handleInputChange();
    }
    function onFileDrop(e) {
      e.preventDefault();
      e.stopPropagation();
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        file.value = droppedFile;
        handleInputChange();
      }
      isDragOver.value = false;
    }
    function triggerFileInput() {
      var _a;
      if (!props.isAnalyzing) {
        (_a = fileInput.value) == null ? void 0 : _a.click();
      }
    }
    function clearFile() {
      file.value = null;
      if (fileInput.value) {
        fileInput.value.value = "";
      }
      handleInputChange();
    }
    function emitAnalyze() {
      if (!canAnalyze.value) {
        showValidationWarning.value = true;
        return;
      }
      showValidationWarning.value = false;
      if (inputMode.value === "text") {
        emit("analyze", { text: text.value, type: "text" });
      } else if (inputMode.value === "url") {
        emit("analyze", { url: url.value, type: "url" });
      } else if (inputMode.value === "file") {
        const formData = new FormData();
        formData.append("file", file.value);
        formData.append("type", "file");
        emit("analyze", formData);
      } else if (inputMode.value === "quick") {
        emit("analyze", { text: quickCitation.value.trim(), type: "text", quick: true });
        quickCitation.value = "";
      }
    }
    function loadRecentInput(input) {
      inputMode.value = input.tab;
      switch (input.tab) {
        case "text":
          text.value = input.text || "";
          break;
        case "url":
          url.value = input.url || "";
          break;
        case "file":
          console.log("File input selected:", input.fileName);
          break;
      }
      validateCurrentInput();
    }
    function formatFileSize(bytes) {
      if (!bytes) return "0 Bytes";
      const k = 1024, sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }
    function onModeChange() {
      validationErrors.value = {};
      isDirty.value = { text: false, url: false, file: false, quick: false };
      showValidationWarning.value = false;
      validateCurrentInput();
      console.log("[onModeChange] inputMode:", inputMode.value, "file:", file.value, "url:", url.value, "hasErrors:", hasErrors.value, "currentErrors:", currentErrors.value);
    }
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$2, [
        createBaseVNode("div", _hoisted_2$2, [
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "file", disabled: __props.isAnalyzing }]),
            onClick: _cache[0] || (_cache[0] = ($event) => !__props.isAnalyzing && (inputMode.value = "file", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_3$1, toDisplayString(methodIcons.file), 1),
            createBaseVNode("div", _hoisted_4$1, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.file), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.file), 1)
            ]),
            inputMode.value === "file" ? (openBlock(), createElementBlock("div", _hoisted_5$1, "✓")) : createCommentVNode("", true)
          ], 2),
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "url", disabled: __props.isAnalyzing }]),
            onClick: _cache[1] || (_cache[1] = ($event) => !__props.isAnalyzing && (inputMode.value = "url", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_6$1, toDisplayString(methodIcons.url), 1),
            createBaseVNode("div", _hoisted_7$1, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.url), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.url), 1)
            ]),
            inputMode.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_8$1, "✓")) : createCommentVNode("", true)
          ], 2)
        ]),
        inputMode.value === "file" || inputMode.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_9$1, [
          inputMode.value === "file" ? (openBlock(), createElementBlock("div", _hoisted_10$1, [
            _cache[13] || (_cache[13] = createBaseVNode("label", { class: "input-label" }, [
              createBaseVNode("i", { class: "bi bi-file-earmark-arrow-up me-2" }),
              createTextVNode(" Upload a document ")
            ], -1)),
            createBaseVNode("div", {
              class: normalizeClass(["file-drop-zone", {
                "has-file": file.value,
                "dragover": isDragOver.value,
                "error": hasErrors.value && isDirty.value.file
              }]),
              onDrop: onFileDrop,
              onDragover: _cache[2] || (_cache[2] = withModifiers(($event) => isDragOver.value = true, ["prevent"])),
              onDragleave: _cache[3] || (_cache[3] = withModifiers(($event) => isDragOver.value = false, ["prevent"])),
              onClick: triggerFileInput
            }, [
              createBaseVNode("input", {
                ref_key: "fileInput",
                ref: fileInput,
                id: "fileInput",
                type: "file",
                onChange: onFileChange,
                disabled: __props.isAnalyzing,
                accept: ".pdf,.doc,.docx,.txt",
                style: { "display": "none" }
              }, null, 40, _hoisted_11$1),
              !file.value ? (openBlock(), createElementBlock("div", _hoisted_12$1, _cache[9] || (_cache[9] = [
                createStaticVNode('<div class="upload-icon" data-v-7bd870d9>📁</div><h5 class="drop-zone-title" data-v-7bd870d9>Click to browse or drag &amp; drop</h5><p class="file-types" data-v-7bd870d9>Supports: PDF, DOC, DOCX, TXT (max 50MB)</p><div class="drop-zone-hint" data-v-7bd870d9><i class="bi bi-arrow-up-circle" data-v-7bd870d9></i><span data-v-7bd870d9>Drop your file here</span></div>', 4)
              ]))) : (openBlock(), createElementBlock("div", _hoisted_13$1, [
                _cache[11] || (_cache[11] = createBaseVNode("div", { class: "file-icon" }, "📄", -1)),
                createBaseVNode("div", _hoisted_14$1, [
                  createBaseVNode("strong", null, toDisplayString(file.value.name), 1),
                  createBaseVNode("span", null, toDisplayString(formatFileSize(file.value.size)), 1)
                ]),
                !__props.isAnalyzing ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  onClick: withModifiers(clearFile, ["stop"]),
                  class: "clear-file-btn",
                  title: "Remove file"
                }, _cache[10] || (_cache[10] = [
                  createBaseVNode("i", { class: "bi bi-x-lg" }, null, -1)
                ]))) : createCommentVNode("", true)
              ]))
            ], 34),
            hasErrors.value && isDirty.value.file ? (openBlock(), createElementBlock("div", _hoisted_15$1, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[12] || (_cache[12] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : inputMode.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_16$1, [
            _cache[21] || (_cache[21] = createBaseVNode("label", { class: "input-label" }, [
              createBaseVNode("i", { class: "bi bi-link-45deg me-2" }),
              createTextVNode(" Enter URL to analyze ")
            ], -1)),
            createBaseVNode("div", _hoisted_17$1, [
              createBaseVNode("div", _hoisted_18$1, [
                _cache[16] || (_cache[16] = createBaseVNode("div", { class: "input-icon" }, [
                  createBaseVNode("i", { class: "bi bi-globe" })
                ], -1)),
                withDirectives(createBaseVNode("input", {
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => url.value = $event),
                  type: "url",
                  placeholder: "https://example.com/document.pdf",
                  disabled: __props.isAnalyzing,
                  onInput: handleInputChange,
                  class: normalizeClass([{ "error": hasErrors.value && isDirty.value.url }, "url-input-field"])
                }, null, 42, _hoisted_19$1), [
                  [vModelText, url.value]
                ]),
                url.value && !hasErrors.value ? (openBlock(), createElementBlock("div", _hoisted_20$1, _cache[14] || (_cache[14] = [
                  createBaseVNode("i", { class: "bi bi-check-circle-fill" }, null, -1)
                ]))) : url.value && hasErrors.value ? (openBlock(), createElementBlock("div", _hoisted_21$1, _cache[15] || (_cache[15] = [
                  createBaseVNode("i", { class: "bi bi-x-circle-fill" }, null, -1)
                ]))) : createCommentVNode("", true)
              ])
            ]),
            createBaseVNode("div", _hoisted_22$1, [
              url.value && !hasErrors.value ? (openBlock(), createElementBlock("span", _hoisted_23$1, [
                _cache[17] || (_cache[17] = createBaseVNode("i", { class: "bi bi-eye me-1" }, null, -1)),
                createTextVNode(" Will analyze: " + toDisplayString(url.value), 1)
              ])) : url.value && hasErrors.value ? (openBlock(), createElementBlock("span", _hoisted_24$1, _cache[18] || (_cache[18] = [
                createBaseVNode("i", { class: "bi bi-exclamation-triangle me-1" }, null, -1),
                createTextVNode(" Invalid URL format ")
              ]))) : (openBlock(), createElementBlock("span", _hoisted_25, _cache[19] || (_cache[19] = [
                createBaseVNode("i", { class: "bi bi-info-circle me-1" }, null, -1),
                createTextVNode(" Enter a valid URL to analyze web content ")
              ])))
            ]),
            hasErrors.value && isDirty.value.url ? (openBlock(), createElementBlock("div", _hoisted_26, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[20] || (_cache[20] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : createCommentVNode("", true)
        ])) : createCommentVNode("", true),
        createBaseVNode("div", _hoisted_27, [
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "quick", disabled: __props.isAnalyzing }]),
            onClick: _cache[5] || (_cache[5] = ($event) => !__props.isAnalyzing && (inputMode.value = "quick", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_28, toDisplayString(methodIcons.quick), 1),
            createBaseVNode("div", _hoisted_29, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.quick), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.quick), 1)
            ]),
            inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_30, "✓")) : createCommentVNode("", true)
          ], 2),
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "text", disabled: __props.isAnalyzing }]),
            onClick: _cache[6] || (_cache[6] = ($event) => !__props.isAnalyzing && (inputMode.value = "text", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_31, toDisplayString(methodIcons.text), 1),
            createBaseVNode("div", _hoisted_32, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.text), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.text), 1)
            ]),
            inputMode.value === "text" ? (openBlock(), createElementBlock("div", _hoisted_33, "✓")) : createCommentVNode("", true)
          ], 2)
        ]),
        createVNode(RecentInputs, { onLoadInput: loadRecentInput }),
        createBaseVNode("div", _hoisted_34, [
          createBaseVNode("button", {
            class: normalizeClass(["analyze-btn", { disabled: !canAnalyze.value || __props.isAnalyzing }]),
            disabled: !canAnalyze.value || __props.isAnalyzing,
            onClick: emitAnalyze
          }, [
            __props.isAnalyzing ? (openBlock(), createElementBlock("span", _hoisted_36)) : (openBlock(), createElementBlock("span", _hoisted_37, "🔍")),
            createTextVNode(" " + toDisplayString(__props.isAnalyzing ? "Analyzing..." : "Analyze Content"), 1)
          ], 10, _hoisted_35),
          showValidationWarning.value && hasErrors.value ? (openBlock(), createElementBlock("div", _hoisted_38, _cache[22] || (_cache[22] = [
            createBaseVNode("p", null, "Please fix the errors above before analyzing", -1)
          ]))) : createCommentVNode("", true)
        ]),
        inputMode.value === "text" || inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_39, [
          inputMode.value === "text" ? (openBlock(), createElementBlock("div", _hoisted_40, [
            _cache[27] || (_cache[27] = createBaseVNode("label", { class: "input-label" }, [
              createBaseVNode("i", { class: "bi bi-text-paragraph me-2" }),
              createTextVNode(" Paste your text here ")
            ], -1)),
            createBaseVNode("div", _hoisted_41, [
              withDirectives(createBaseVNode("textarea", {
                "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => text.value = $event),
                placeholder: "Paste legal text, citations, or document content here...",
                disabled: __props.isAnalyzing,
                rows: "8",
                onInput: handleInputChange,
                class: normalizeClass([{ "error": hasErrors.value && isDirty.value.text }, "text-input-field"])
              }, null, 42, _hoisted_42), [
                [vModelText, text.value]
              ]),
              !text.value ? (openBlock(), createElementBlock("div", _hoisted_43, _cache[23] || (_cache[23] = [
                createBaseVNode("i", { class: "bi bi-clipboard" }, null, -1),
                createBaseVNode("span", null, "Paste your content here", -1)
              ]))) : createCommentVNode("", true)
            ]),
            createBaseVNode("div", _hoisted_44, [
              createBaseVNode("span", {
                class: normalizeClass(["char-count", { "error": text.value.length > VALIDATION_RULES.text.maxLength }])
              }, [
                _cache[24] || (_cache[24] = createBaseVNode("i", { class: "bi bi-type me-1" }, null, -1)),
                createTextVNode(" " + toDisplayString(text.value.length) + " / " + toDisplayString(VALIDATION_RULES.text.maxLength) + " characters ", 1)
              ], 2),
              text.value.length < VALIDATION_RULES.text.minLength && isDirty.value.text ? (openBlock(), createElementBlock("span", _hoisted_45, [
                _cache[25] || (_cache[25] = createBaseVNode("i", { class: "bi bi-exclamation-circle me-1" }, null, -1)),
                createTextVNode(" Minimum " + toDisplayString(VALIDATION_RULES.text.minLength) + " characters required ", 1)
              ])) : createCommentVNode("", true)
            ]),
            hasErrors.value && isDirty.value.text ? (openBlock(), createElementBlock("div", _hoisted_46, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[26] || (_cache[26] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_47, [
            _cache[30] || (_cache[30] = createBaseVNode("label", { class: "input-label" }, [
              createBaseVNode("i", { class: "bi bi-lightning me-2" }),
              createTextVNode(" Enter a single citation ")
            ], -1)),
            createBaseVNode("div", _hoisted_48, [
              createBaseVNode("div", _hoisted_49, [
                _cache[29] || (_cache[29] = createBaseVNode("div", { class: "input-icon" }, [
                  createBaseVNode("i", { class: "bi bi-quote" })
                ], -1)),
                withDirectives(createBaseVNode("input", {
                  "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => quickCitation.value = $event),
                  type: "text",
                  placeholder: "e.g., 410 U.S. 113 (1973) or Roe v. Wade",
                  disabled: __props.isAnalyzing,
                  onKeyup: withKeys(emitAnalyze, ["enter"]),
                  class: "quick-citation-input"
                }, null, 40, _hoisted_50), [
                  [vModelText, quickCitation.value]
                ]),
                quickCitation.value ? (openBlock(), createElementBlock("div", _hoisted_51, _cache[28] || (_cache[28] = [
                  createBaseVNode("i", { class: "bi bi-check-circle-fill" }, null, -1)
                ]))) : createCommentVNode("", true)
              ])
            ]),
            _cache[31] || (_cache[31] = createBaseVNode("div", { class: "input-footer" }, [
              createBaseVNode("span", { class: "citation-hint" }, [
                createBaseVNode("i", { class: "bi bi-info-circle me-1" }),
                createTextVNode(" Enter a legal citation to verify quickly ")
              ])
            ], -1))
          ])) : createCommentVNode("", true)
        ])) : createCommentVNode("", true)
      ]);
    };
  }
};
const UnifiedInput = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["__scopeId", "data-v-7bd870d9"]]);
const _hoisted_1$1 = { class: "toast-icon" };
const _hoisted_2$1 = { class: "toast-message" };
const _sfc_main$2 = {
  __name: "Toast",
  props: {
    message: String,
    type: { type: String, default: "info" },
    // 'success', 'error', 'info'
    duration: { type: Number, default: 3500 }
  },
  emits: ["close"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const visible = ref(true);
    const icon = computed(() => {
      if (props.type === "success") return "✅";
      if (props.type === "error") return "❌";
      return "ℹ️";
    });
    function close() {
      visible.value = false;
      emit("close");
    }
    watch(() => props.message, (msg) => {
      if (msg) {
        visible.value = true;
        setTimeout(close, props.duration);
      }
    });
    return (_ctx, _cache) => {
      return openBlock(), createBlock(Transition, { name: "toast-fade" }, {
        default: withCtx(() => [
          visible.value ? (openBlock(), createElementBlock("div", {
            key: 0,
            class: normalizeClass(["toast", __props.type])
          }, [
            createBaseVNode("span", _hoisted_1$1, toDisplayString(icon.value), 1),
            createBaseVNode("span", _hoisted_2$1, toDisplayString(__props.message), 1),
            createBaseVNode("button", {
              class: "toast-close",
              onClick: close
            }, "×")
          ], 2)) : createCommentVNode("", true)
        ]),
        _: 1
      });
    };
  }
};
const Toast = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["__scopeId", "data-v-a1e0936f"]]);
const _sfc_main$1 = {
  __name: "SkeletonLoader",
  props: {
    lines: { type: Number, default: 3 },
    height: { type: String, default: "auto" },
    width: { type: String, default: "100%" }
  },
  setup(__props) {
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: "skeleton-loader",
        style: normalizeStyle({ height: __props.height, width: __props.width })
      }, [
        (openBlock(true), createElementBlock(Fragment, null, renderList(__props.lines, (n) => {
          return openBlock(), createElementBlock("div", {
            key: n,
            class: "skeleton-line"
          });
        }), 128))
      ], 4);
    };
  }
};
const SkeletonLoader = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-1c57e4a2"]]);
const _sfc_main = {
  name: "EnhancedValidator",
  components: {
    CitationResults,
    UnifiedInput,
    Toast,
    SkeletonLoader,
    RecentInputs
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const results = ref(null);
    const error = ref(null);
    const {
      isLoading: isLoading2,
      cancel: cancelValidation
    } = useApi({
      loadingMessage: "Validating citation...",
      showLoading: true
    });
    const hasActiveRequest = ref(false);
    const { isLoading: isGlobalLoading } = useLoadingState();
    const showLoading = computed(() => isLoading2.value || isGlobalLoading.value || hasActiveRequest.value);
    const {
      elapsedTime,
      remainingTime,
      totalProgress,
      currentStep,
      currentStepProgress,
      processingSteps,
      actualTimes,
      citationInfo,
      rateLimitInfo,
      timeout,
      processingError,
      canRetry,
      startProcessing,
      stopProcessing,
      updateProgress,
      setSteps,
      resetProcessing,
      setProcessingError
    } = useProcessingTime();
    const queuePosition = ref(0);
    const estimatedQueueTime = ref(null);
    const activeRequestId = ref(null);
    const pollInterval = ref(null);
    let lastPolledTaskId = ref(null);
    const toastMessage = ref("");
    const toastType = ref("info");
    const showToast = (msg, type = "info") => {
      toastMessage.value = msg;
      toastType.value = type;
    };
    const clearToast = () => {
      toastMessage.value = "";
    };
    const fallbackTimeout = ref(null);
    const fallbackTimeoutMs = 12e4;
    const fallbackError = ref("");
    const showTimer = computed(() => true);
    const progressCurrent = ref(0);
    const progressTotal = computed(() => citationInfo.value && citationInfo.value.total ? citationInfo.value.total : 0);
    const progressPercent = computed(() => {
      if (!progressTotal.value) return 0;
      return Math.min(100, Math.round(progressCurrent.value / progressTotal.value * 100));
    });
    const progressBarClass = computed(() => {
      if (progressPercent.value >= 80) return "bg-success";
      if (progressPercent.value >= 50) return "bg-info";
      if (progressPercent.value >= 30) return "bg-warning";
      return "bg-danger";
    });
    let progressTimer = null;
    const showFileUpload = ref(false);
    const { normalizeCitations } = useCitationNormalization();
    function formatTime(seconds) {
      if (!seconds || seconds < 0) return "0s";
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor(seconds % 3600 / 60);
      const secs = Math.floor(seconds % 60);
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
      } else {
        return `${minutes}:${secs.toString().padStart(2, "0")}`;
      }
    }
    function getProgressBarClass(value) {
      if (value >= 0.8) return "bg-success";
      if (value >= 0.5) return "bg-info";
      if (value >= 0.3) return "bg-warning";
      return "bg-danger";
    }
    function clearResults() {
      results.value = null;
      error.value = null;
      resetProcessing();
    }
    async function pollTaskStatus(taskId) {
      if (!taskId) return;
      try {
        const response = await api.get(`/task_status/${taskId}`);
        const data = response.data;
        if (data.status === "completed") {
          const citationResults = Array.isArray(data.results) ? data.results : data.citations || [];
          results.value = {
            citations: normalizeCitations(citationResults),
            metadata: data.metadata || {},
            total_citations: citationResults.length,
            verified_count: citationResults.filter((c) => {
              var _a, _b;
              return c.verified || c.valid || ((_a = c.data) == null ? void 0 : _a.valid) || ((_b = c.data) == null ? void 0 : _b.found);
            }).length,
            unverified_count: citationResults.filter((c) => {
              var _a, _b;
              return !(c.verified || c.valid || ((_a = c.data) == null ? void 0 : _a.valid) || ((_b = c.data) == null ? void 0 : _b.found));
            }).length
          };
          hasActiveRequest.value = false;
          stopProcessing();
          isLoading2.value = false;
          if (typeof isGlobalLoading !== "undefined" && isGlobalLoading.value !== void 0) {
            isGlobalLoading.value = false;
          }
          showToast("Citation analysis completed successfully!", "success");
          if (pollInterval.value) {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
          }
          if (citationResults.length === 0) {
            let debugMsg = "No citations found in the provided text or document.";
            if (data.status_message && data.status_message.toLowerCase().includes("rate limit")) {
              debugMsg += " (Possible cause: search engine rate limiting)";
            }
            if (data.error) {
              debugMsg += ` (Backend error: ${data.error})`;
            }
            error.value = debugMsg;
          }
          if (window && window.localStorage && window.localStorage.getItem("debugMode") === "true") {
            error.value += "\n[DEBUG] Raw backend response: " + JSON.stringify(data, null, 2);
          }
        } else if (data.status === "failed") {
          error.value = data.error || "Processing failed";
          hasActiveRequest.value = false;
          setProcessingError(data.error || "Processing failed");
          showToast(`Processing failed: ${data.error || "Unknown error"}`, "error");
          if (pollInterval.value) {
            clearInterval(pollInterval.value);
            pollInterval.value = null;
          }
        } else {
          hasActiveRequest.value = true;
          if (data.estimated_total_time && data.steps) {
            if (lastPolledTaskId.value !== taskId) {
              startProcessing({
                estimated_total_time: data.estimated_total_time,
                steps: data.steps
              });
              lastPolledTaskId.value = taskId;
            }
          } else if (data.estimated_total_time) {
            if (lastPolledTaskId.value !== taskId) {
              startProcessing(data.estimated_total_time);
              lastPolledTaskId.value = taskId;
            }
          }
          if (data.current_step) {
            updateProgress({
              step: data.current_step,
              progress: data.progress || 0
            });
          }
          if (data.total_citations !== void 0) {
            citationInfo.value = {
              total: data.total_citations,
              processed: data.processed_citations || 0,
              unique: data.unique_citations || 0
            };
          }
          results.value = {
            citations: [],
            metadata: data.metadata || {},
            progress: data.progress || 0,
            eta_seconds: data.eta_seconds || null,
            current_chunk: data.current_chunk || 0,
            total_chunks: data.total_chunks || 1,
            total_citations: data.total_citations || 0,
            verified_count: 0,
            unverified_count: 0
          };
          console.log("EnhancedValidator: Updated results with progress data:", results.value);
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(taskId), 2e3);
          }
        }
        onProgressOrResult();
      } catch (err) {
        console.error("Error polling task status:", err);
        error.value = "Failed to check processing status";
        hasActiveRequest.value = false;
        setProcessingError("Failed to check processing status");
        if (pollInterval.value) {
          clearInterval(pollInterval.value);
          pollInterval.value = null;
        }
      }
    }
    const retryProcessing = async () => {
      if (!activeRequestId.value) return;
      try {
        processingError.value = null;
        canRetry.value = false;
        resetProcessing();
        await api.cancelRequest(activeRequestId.value);
        const currentRequest = api.getRequestStatus(activeRequestId.value);
        if (currentRequest) {
          const { type, input } = currentRequest;
          await analyzeInput(input, type);
        }
      } catch (error2) {
        processingError.value = `Failed to retry: ${error2.message}`;
        canRetry.value = true;
      }
    };
    const analyzeInput = async (input, type) => {
      try {
        if (type === "file") {
          await handleFileAnalyze(input);
        } else if (type === "url") {
          await handleUrlAnalyze({ url: input });
        } else if (type === "text") {
          await handleTextAnalyze({ text: input });
        }
      } catch (error2) {
        processingError.value = `Failed to analyze input: ${error2.message}`;
        canRetry.value = true;
      }
    };
    const handleResults = (responseData) => {
      try {
        console.log("handleResults called with:", responseData);
        let rawCitations = [];
        if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        results.value = {
          ...responseData,
          citations: normalizeCitations(rawCitations),
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        };
        console.log("Results set to:", results.value);
        isLoading2.value = false;
        error.value = null;
        hasActiveRequest.value = false;
        activeRequestId.value = null;
        console.log("Loading states after setting results:");
        console.log("- isLoading.value:", isLoading2.value);
        console.log("- isGlobalLoading.value:", isGlobalLoading.value);
        console.log("- hasActiveRequest.value:", hasActiveRequest.value);
        console.log("- showLoading.value:", showLoading.value);
        if (typeof isGlobalLoading !== "undefined" && isGlobalLoading.value !== void 0) {
          isGlobalLoading.value = false;
        }
        nextTick(() => {
          const resultsElement = document.querySelector(".results-container");
          if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: "smooth" });
          }
        });
      } catch (err) {
        console.error("Error handling results:", err);
        error.value = "Failed to process results";
        isLoading2.value = false;
      }
    };
    const handleError = (err) => {
      console.error("Analysis error:", err);
      error.value = err.message || "An error occurred during analysis";
      isLoading2.value = false;
      hasActiveRequest.value = false;
      activeRequestId.value = null;
      processingError.value = err.message || "Analysis failed";
      canRetry.value = true;
      showToast(error.value, "error");
    };
    const handleTextAnalyze = async ({ text, options }) => {
      if (hasActiveRequest.value) {
        console.log("Request already in progress, ignoring duplicate text analysis");
        return;
      }
      isLoading2.value = true;
      error.value = null;
      results.value = null;
      try {
        const responseData = await analyze({
          text,
          type: "text"
        });
        handleResults(responseData);
        isLoading2.value = false;
      } catch (err) {
        handleError(err);
      }
    };
    const handleFileAnalyze = async (input) => {
      if (hasActiveRequest.value) {
        console.log("Request already in progress, ignoring duplicate file analysis");
        return;
      }
      isLoading2.value = true;
      error.value = null;
      results.value = null;
      try {
        let formData;
        if (input instanceof FormData) {
          formData = input;
        } else {
          formData = new FormData();
          formData.append("file", input.file);
          formData.append("type", "file");
        }
        const responseData = await analyze(formData);
        handleResults(responseData);
        isLoading2.value = false;
      } catch (err) {
        handleError(err);
      }
    };
    const handleUrlAnalyze = async ({ url }) => {
      if (hasActiveRequest.value) {
        console.log("Request already in progress, ignoring duplicate URL analysis");
        return;
      }
      isLoading2.value = true;
      error.value = null;
      results.value = null;
      try {
        const responseData = await analyze({
          url,
          type: "url"
        });
        handleResults(responseData);
        isLoading2.value = false;
      } catch (err) {
        handleError(err);
      }
    };
    function handleUnifiedAnalyze(payload) {
      console.log("handleUnifiedAnalyze payload:", payload);
      if (hasActiveRequest.value) {
        console.log("Request already in progress, ignoring duplicate submission");
        showToast("A request is already in progress. Please wait for it to complete.", "warning");
        return;
      }
      resetProcessing();
      setSteps([
        { step: "Preparing analysis", estimated_time: 5 },
        { step: "Processing content", estimated_time: 30 },
        { step: "Verifying citations", estimated_time: 60 }
      ]);
      startProcessing();
      hasActiveRequest.value = true;
      error.value = null;
      results.value = null;
      if (payload.file) {
        handleFileAnalyze(payload);
      } else if (payload.url) {
        handleUrlAnalyze(payload);
      } else if (payload.text) {
        if (payload.quick) {
          handleTextAnalyze({ text: payload.text, options: {} });
        } else {
          handleTextAnalyze({ text: payload.text, options: {} });
        }
      }
      onProcessingStart();
    }
    onMounted(() => {
      let input = { ...route.query };
      if (router.currentRoute.value.state && router.currentRoute.value.state.results) {
        console.log("[EnhancedValidator] Using results from router state, skipping new analysis.");
        const responseData = router.currentRoute.value.state.results;
        let rawCitations = [];
        if (Array.isArray(responseData.citations) && responseData.citations.length > 0) {
          rawCitations = responseData.citations;
        } else if (Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0) {
          rawCitations = responseData.validation_results;
        }
        if (rawCitations.length > 0) {
          results.value = {
            ...responseData,
            citations: normalizeCitations(rawCitations),
            total_citations: rawCitations.length,
            verified_count: rawCitations.filter((c) => {
              var _a, _b;
              return c.verified || c.valid || ((_a = c.data) == null ? void 0 : _a.valid) || ((_b = c.data) == null ? void 0 : _b.found);
            }).length,
            unverified_count: rawCitations.filter((c) => {
              var _a, _b;
              return !(c.verified || c.valid || ((_a = c.data) == null ? void 0 : _a.valid) || ((_b = c.data) == null ? void 0 : _b.found));
            }).length
          };
          showToast("Citation analysis completed successfully!", "success");
        } else {
          error.value = "No citations found in the provided text or document.";
        }
        return;
      }
      if (input.task_id) {
        console.log("Found task_id, starting polling:", input.task_id);
        activeRequestId.value = input.task_id;
        hasActiveRequest.value = true;
        pollTaskStatus(input.task_id);
        return;
      }
      if (!input.text && !input.url && !input.fileName && localStorage.getItem("lastCitationInput")) {
        try {
          const storedInput = JSON.parse(localStorage.getItem("lastCitationInput"));
          if (storedInput.fileName) {
            console.log("Found file upload in localStorage, skipping restoration:", storedInput.fileName);
            delete storedInput.fileName;
            if (Object.keys(storedInput).length === 0) {
              localStorage.removeItem("lastCitationInput");
            } else {
              localStorage.setItem("lastCitationInput", JSON.stringify(storedInput));
            }
            input = {};
          } else {
            input = storedInput;
          }
        } catch (e) {
          console.warn("Error parsing localStorage input:", e);
          input = {};
        }
      }
      if (input.text || input.url || input.fileName) {
        console.log("Triggering analysis with input:", input);
        clearResults();
        if (input.text) {
          handleTextAnalyze({ text: input.text });
        } else if (input.url) {
          handleUrlAnalyze({ url: input.url });
        } else if (input.fileName) {
          console.warn("Unexpected file upload in input:", input.fileName);
          error.value = `File "${input.fileName}" was previously uploaded but cannot be restored from history. Please upload the file again to analyze it.`;
          showFileUpload.value = true;
        }
      } else {
        results.value = null;
      }
      if (showTimer.value && progressTotal.value > 20) {
        progressCurrent.value = 0;
        if (progressTimer) clearInterval(progressTimer);
        progressTimer = setInterval(() => {
          if (progressCurrent.value < progressTotal.value) {
            progressCurrent.value++;
          }
        }, 2e3);
      }
      setTimeout(() => {
        const faIcons = document.querySelectorAll(".fas.fa-cog.fa-spin");
        const biIcons = document.querySelectorAll(".bi.bi-gear-fill.spinning");
        faIcons.forEach((faIcon, index) => {
          if (getComputedStyle(faIcon).fontFamily.indexOf("FontAwesome") === -1) {
            faIcon.style.display = "none";
            if (biIcons[index]) {
              biIcons[index].style.display = "inline-block";
            }
          }
        });
      }, 100);
    });
    onUnmounted(() => {
      if (hasActiveRequest.value) {
        cancelValidation();
      }
      if (pollInterval.value) {
        clearInterval(pollInterval.value);
        pollInterval.value = null;
      }
      clearFallbackTimer();
      if (progressTimer) clearInterval(progressTimer);
    });
    watch(() => results.value, (val) => {
      if (val && progressTimer) {
        progressCurrent.value = progressTotal.value;
        clearInterval(progressTimer);
      }
    });
    function copyResults() {
      console.log("copyResults called");
    }
    function downloadResults() {
      console.log("downloadResults called");
    }
    function startFallbackTimer() {
      clearFallbackTimer();
      fallbackTimeout.value = setTimeout(() => {
        fallbackError.value = "Processing timed out. No response from server.";
        setProcessingError(fallbackError.value);
        hasActiveRequest.value = false;
        showToast(fallbackError.value, "error");
      }, fallbackTimeoutMs);
    }
    function clearFallbackTimer() {
      if (fallbackTimeout.value) {
        clearTimeout(fallbackTimeout.value);
        fallbackTimeout.value = null;
      }
    }
    function onProcessingStart() {
      fallbackError.value = "";
      startFallbackTimer();
    }
    function onProgressOrResult() {
      clearFallbackTimer();
    }
    const loadRecentInput = (input) => {
      router.push({
        path: "/",
        query: {
          tab: input.tab,
          ...input.tab === "paste" && input.text ? { text: input.text } : {},
          ...input.tab === "url" && input.url ? { url: input.url } : {}
        }
      });
    };
    return {
      // State
      results,
      error,
      isLoading: showLoading,
      showLoading,
      hasActiveRequest,
      // Methods
      clearResults,
      handleUnifiedAnalyze,
      retryProcessing,
      cancelValidation,
      copyResults,
      downloadResults,
      // Processing time tracking
      elapsedTime,
      remainingTime,
      totalProgress,
      currentStep,
      currentStepProgress,
      processingSteps,
      actualTimes,
      formatTime,
      // Enhanced progress tracking
      citationInfo,
      queuePosition,
      estimatedQueueTime,
      rateLimitInfo,
      timeout,
      processingError,
      canRetry,
      // Helper functions
      getProgressBarClass,
      // Stub methods for CitationResults component
      applyCorrection: () => {
      },
      // Toast
      toastMessage,
      toastType,
      clearToast,
      // Fallback timer
      fallbackError,
      // Show timer computed property
      showTimer,
      // Progress bar state
      progressCurrent,
      progressTotal,
      progressPercent,
      progressBarClass,
      // Recent inputs
      loadRecentInput,
      // Show file upload option
      showFileUpload
    };
  }
};
const _hoisted_1 = { class: "enhanced-validator" };
const _hoisted_2 = { class: "header text-center mb-4" };
const _hoisted_3 = {
  key: 1,
  class: "loading-container"
};
const _hoisted_4 = { class: "loading-content" };
const _hoisted_5 = {
  key: 0,
  class: "progress-section"
};
const _hoisted_6 = { class: "progress-info mb-3" };
const _hoisted_7 = { class: "progress-stats" };
const _hoisted_8 = { class: "stat" };
const _hoisted_9 = { class: "stat" };
const _hoisted_10 = { class: "progress-container" };
const _hoisted_11 = {
  class: "progress",
  style: { "height": "1.5rem", "border-radius": "0.75rem" }
};
const _hoisted_12 = ["aria-valuenow"];
const _hoisted_13 = { class: "progress-text" };
const _hoisted_14 = {
  key: 2,
  class: "error-container"
};
const _hoisted_15 = { class: "error-content" };
const _hoisted_16 = {
  key: 0,
  class: "mt-4"
};
const _hoisted_17 = { class: "card" };
const _hoisted_18 = { class: "card-body" };
const _hoisted_19 = {
  key: 3,
  class: "main-content-wrapper"
};
const _hoisted_20 = { class: "main-content-area" };
const _hoisted_21 = {
  key: 0,
  class: "results-container"
};
const _hoisted_22 = {
  key: 1,
  class: "input-container"
};
const _hoisted_23 = {
  key: 2,
  class: "no-results-container"
};
const _hoisted_24 = { class: "recent-inputs-sidebar-container" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_Toast = resolveComponent("Toast");
  const _component_UnifiedInput = resolveComponent("UnifiedInput");
  const _component_CitationResults = resolveComponent("CitationResults");
  const _component_RecentInputs = resolveComponent("RecentInputs");
  return openBlock(), createElementBlock("div", _hoisted_1, [
    $setup.toastMessage ? (openBlock(), createBlock(_component_Toast, {
      key: 0,
      message: $setup.toastMessage,
      type: $setup.toastType,
      onClose: $setup.clearToast
    }, null, 8, ["message", "type", "onClose"])) : createCommentVNode("", true),
    createBaseVNode("div", _hoisted_2, [
      createBaseVNode("button", {
        class: "btn btn-link back-btn",
        onClick: _cache[0] || (_cache[0] = (...args) => _ctx.goHome && _ctx.goHome(...args))
      }, _cache[1] || (_cache[1] = [
        createBaseVNode("i", { class: "bi bi-arrow-left" }, null, -1),
        createTextVNode(" Back to Home ")
      ])),
      _cache[2] || (_cache[2] = createBaseVNode("h1", { class: "results-title" }, "Citation Verification Results", -1))
    ]),
    $setup.showLoading && !$setup.results ? (openBlock(), createElementBlock("div", _hoisted_3, [
      createBaseVNode("div", _hoisted_4, [
        _cache[5] || (_cache[5] = createBaseVNode("div", { class: "spinner-container" }, [
          createBaseVNode("div", {
            class: "spinner-border text-primary",
            role: "status"
          }, [
            createBaseVNode("span", { class: "visually-hidden" }, "Processing...")
          ])
        ], -1)),
        _cache[6] || (_cache[6] = createBaseVNode("h3", null, "Processing Citations", -1)),
        _cache[7] || (_cache[7] = createBaseVNode("p", { class: "text-muted" }, "Extracting and analyzing citations from your document...", -1)),
        $setup.showTimer ? (openBlock(), createElementBlock("div", _hoisted_5, [
          createBaseVNode("div", _hoisted_6, [
            createBaseVNode("div", _hoisted_7, [
              createBaseVNode("span", _hoisted_8, [
                _cache[3] || (_cache[3] = createBaseVNode("i", { class: "bi bi-list-ol text-primary" }, null, -1)),
                createTextVNode(" " + toDisplayString($setup.progressCurrent) + " of " + toDisplayString($setup.progressTotal) + " citations ", 1)
              ]),
              createBaseVNode("span", _hoisted_9, [
                _cache[4] || (_cache[4] = createBaseVNode("i", { class: "bi bi-clock text-primary" }, null, -1)),
                createTextVNode(" " + toDisplayString($setup.formatTime($setup.elapsedTime)) + " elapsed ", 1)
              ])
            ])
          ]),
          createBaseVNode("div", _hoisted_10, [
            createBaseVNode("div", _hoisted_11, [
              createBaseVNode("div", {
                class: normalizeClass(["progress-bar progress-bar-striped progress-bar-animated", $setup.progressBarClass]),
                role: "progressbar",
                style: normalizeStyle({ width: $setup.progressPercent + "%" }),
                "aria-valuenow": $setup.progressPercent,
                "aria-valuemin": "0",
                "aria-valuemax": "100"
              }, [
                createBaseVNode("span", _hoisted_13, toDisplayString($setup.progressPercent) + "%", 1)
              ], 14, _hoisted_12)
            ])
          ])
        ])) : createCommentVNode("", true)
      ])
    ])) : $setup.error && !$setup.showLoading ? (openBlock(), createElementBlock("div", _hoisted_14, [
      createBaseVNode("div", _hoisted_15, [
        _cache[10] || (_cache[10] = createBaseVNode("div", { class: "error-icon" }, [
          createBaseVNode("i", { class: "bi bi-exclamation-triangle" })
        ], -1)),
        _cache[11] || (_cache[11] = createBaseVNode("h3", null, "Analysis Failed", -1)),
        createBaseVNode("p", null, toDisplayString($setup.error), 1),
        $setup.showFileUpload ? (openBlock(), createElementBlock("div", _hoisted_16, [
          createBaseVNode("div", _hoisted_17, [
            _cache[9] || (_cache[9] = createBaseVNode("div", { class: "card-header bg-primary text-white" }, [
              createBaseVNode("h5", { class: "mb-0" }, [
                createBaseVNode("i", { class: "bi bi-file-earmark-arrow-up me-2" }),
                createTextVNode(" Re-upload File ")
              ])
            ], -1)),
            createBaseVNode("div", _hoisted_18, [
              _cache[8] || (_cache[8] = createBaseVNode("p", { class: "text-muted mb-3" }, " To analyze your file, please upload it again using the form below. ", -1)),
              createVNode(_component_UnifiedInput, {
                onAnalyze: _ctx.handleAnalyze,
                "is-analyzing": $setup.showLoading
              }, null, 8, ["onAnalyze", "is-analyzing"])
            ])
          ])
        ])) : createCommentVNode("", true)
      ])
    ])) : (openBlock(), createElementBlock("div", _hoisted_19, [
      createBaseVNode("div", _hoisted_20, [
        $setup.results ? (openBlock(), createElementBlock("div", _hoisted_21, [
          createVNode(_component_CitationResults, {
            results: $setup.results,
            "processing-time": $setup.elapsedTime,
            "show-details": true,
            onApplyCorrection: $setup.applyCorrection,
            onCopyResults: $setup.copyResults,
            onDownloadResults: $setup.downloadResults,
            onToast: _ctx.showToast
          }, null, 8, ["results", "processing-time", "onApplyCorrection", "onCopyResults", "onDownloadResults", "onToast"])
        ])) : $setup.showFileUpload ? (openBlock(), createElementBlock("div", _hoisted_22, [
          createVNode(_component_UnifiedInput, {
            onAnalyze: _ctx.handleAnalyze,
            "is-analyzing": $setup.showLoading
          }, null, 8, ["onAnalyze", "is-analyzing"])
        ])) : (openBlock(), createElementBlock("div", _hoisted_23, _cache[12] || (_cache[12] = [
          createBaseVNode("div", { class: "no-results-content" }, [
            createBaseVNode("div", { class: "no-results-icon" }, [
              createBaseVNode("i", { class: "bi bi-search" })
            ]),
            createBaseVNode("h3", null, "No Analysis Results"),
            createBaseVNode("p", { class: "lead" }, [
              createTextVNode("No results to display."),
              createBaseVNode("br"),
              createTextVNode("Please return to the home page to start a new analysis.")
            ])
          ], -1)
        ])))
      ]),
      createBaseVNode("div", _hoisted_24, [
        createVNode(_component_RecentInputs, { onLoadInput: $setup.loadRecentInput }, null, 8, ["onLoadInput"])
      ])
    ]))
  ]);
}
const EnhancedValidator = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-5da1c185"]]);
export {
  EnhancedValidator as default
};
//# sourceMappingURL=EnhancedValidator-C_1137yf.js.map
