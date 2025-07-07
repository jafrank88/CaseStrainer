import { r as ref, A as onUnmounted, p as computed, B as watch, c as createElementBlock, o as openBlock, l as createCommentVNode, b as createBaseVNode, t as toDisplayString, g as createTextVNode, F as Fragment, n as renderList, u as normalizeClass, v as withDirectives, x as vModelText, y as withModifiers, C as withKeys, h as createBlock, w as withCtx, T as Transition, D as normalizeStyle, f as resolveComponent, d as createVNode, s as onMounted, E as useRoute, z as useRouter, G as nextTick } from "./vendor-D1FvkS8x.js";
import { c as createLoader, _ as _export_sfc } from "./index-enUF1-WP.js";
import { b as api } from "./api-BfUkQ5CO.js";
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
const _hoisted_8$2 = { class: "stat-item" };
const _hoisted_9$2 = { class: "stat-number" };
const _hoisted_10$2 = { class: "stat-item verified" };
const _hoisted_11$2 = { class: "stat-number" };
const _hoisted_12$2 = { class: "stat-item invalid" };
const _hoisted_13$2 = { class: "stat-number" };
const _hoisted_14$2 = {
  key: 0,
  class: "stats-section"
};
const _hoisted_15$2 = { class: "stats-grid" };
const _hoisted_16$2 = { class: "stat-card" };
const _hoisted_17$2 = { class: "stat-value" };
const _hoisted_18$2 = { class: "stat-card" };
const _hoisted_19$2 = { class: "stat-value" };
const _hoisted_20$2 = { class: "stat-card verified" };
const _hoisted_21$2 = { class: "stat-value" };
const _hoisted_22$2 = { class: "stat-card invalid" };
const _hoisted_23$2 = { class: "stat-value" };
const _hoisted_24$2 = { class: "filter-section" };
const _hoisted_25$1 = { class: "filter-controls" };
const _hoisted_26$1 = ["onClick"];
const _hoisted_27$1 = { class: "filter-count" };
const _hoisted_28$1 = { class: "search-box" };
const _hoisted_29$1 = {
  key: 1,
  class: "citations-list"
};
const _hoisted_30$1 = {
  key: 0,
  class: "group-icon"
};
const _hoisted_31$1 = {
  key: 1,
  class: "group-icon"
};
const _hoisted_32$1 = { class: "group-title" };
const _hoisted_33$1 = { class: "citation-header" };
const _hoisted_34$1 = { class: "citation-main" };
const _hoisted_35$1 = ["title", "onMouseenter", "onClick"];
const _hoisted_36$1 = {
  key: 0,
  class: "score-tooltip"
};
const _hoisted_37$1 = { class: "case-name" };
const _hoisted_38$1 = ["href"];
const _hoisted_39$1 = { key: 1 };
const _hoisted_40$1 = { class: "citation-link" };
const _hoisted_41$1 = ["href"];
const _hoisted_42 = {
  key: 1,
  class: "citation-text"
};
const _hoisted_43 = {
  key: 2,
  class: "complex-indicator",
  title: "Complex citation with multiple components"
};
const _hoisted_44 = { class: "citation-actions" };
const _hoisted_45 = ["onClick", "title"];
const _hoisted_46 = {
  key: 0,
  class: "citation-details"
};
const _hoisted_47 = { class: "detail-section" };
const _hoisted_48 = { class: "detail-row" };
const _hoisted_49 = { class: "detail-value" };
const _hoisted_50 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_51 = { class: "detail-value" };
const _hoisted_52 = { class: "detail-row" };
const _hoisted_53 = { class: "detail-section" };
const _hoisted_54 = { class: "detail-row" };
const _hoisted_55 = { class: "detail-value" };
const _hoisted_56 = { class: "detail-row" };
const _hoisted_57 = { class: "detail-value" };
const _hoisted_58 = { class: "detail-row" };
const _hoisted_59 = { class: "detail-value" };
const _hoisted_60 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_61 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_62 = { class: "detail-section" };
const _hoisted_63 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_64 = { class: "detail-value" };
const _hoisted_65 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_66 = { class: "detail-value" };
const _hoisted_67 = {
  key: 2,
  class: "detail-row"
};
const _hoisted_68 = { class: "detail-value" };
const _hoisted_69 = {
  key: 3,
  class: "detail-row"
};
const _hoisted_70 = { class: "detail-value" };
const _hoisted_71 = {
  key: 4,
  class: "detail-row"
};
const _hoisted_72 = { class: "detail-value" };
const _hoisted_73 = {
  key: 0,
  class: "detail-section"
};
const _hoisted_74 = { class: "detail-row" };
const _hoisted_75 = { class: "detail-value" };
const _hoisted_76 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_77 = { class: "detail-value" };
const _hoisted_78 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_79 = { class: "detail-value" };
const _hoisted_80 = {
  key: 2,
  class: "detail-row"
};
const _hoisted_81 = {
  key: 1,
  class: "detail-section"
};
const _hoisted_82 = { class: "context-box" };
const _hoisted_83 = {
  key: 2,
  class: "detail-section"
};
const _hoisted_84 = { class: "parallel-citations" };
const _hoisted_85 = { class: "parallel-citation-text" };
const _hoisted_86 = {
  key: 0,
  class: "inherited-badge",
  title: "Verified by association with primary"
};
const _hoisted_87 = { class: "detail-section" };
const _hoisted_88 = { class: "detail-row" };
const _hoisted_89 = { class: "detail-value" };
const _hoisted_90 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_91 = { class: "detail-value" };
const _hoisted_92 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_93 = { class: "detail-value note" };
const _hoisted_94 = {
  key: 3,
  class: "detail-section"
};
const _hoisted_95 = { class: "complex-citation-info" };
const _hoisted_96 = {
  key: 0,
  class: "detail-row"
};
const _hoisted_97 = { class: "detail-value" };
const _hoisted_98 = {
  key: 1,
  class: "detail-row"
};
const _hoisted_99 = { class: "detail-value" };
const _hoisted_100 = {
  key: 2,
  class: "detail-row"
};
const _hoisted_101 = { class: "detail-value" };
const _hoisted_102 = {
  key: 3,
  class: "detail-row"
};
const _hoisted_103 = { class: "detail-value" };
const _hoisted_104 = {
  key: 4,
  class: "detail-row"
};
const _hoisted_105 = { class: "detail-value" };
const _hoisted_106 = {
  key: 5,
  class: "detail-row"
};
const _hoisted_107 = { class: "detail-value" };
const _hoisted_108 = {
  key: 6,
  class: "detail-row"
};
const _hoisted_109 = { class: "detail-value" };
const _hoisted_110 = {
  key: 1,
  class: "parallel-citations-section"
};
const _hoisted_111 = { class: "citation-header" };
const _hoisted_112 = { class: "citation-main" };
const _hoisted_113 = {
  key: 0,
  class: "inherited-badge",
  title: "Verified by association with primary"
};
const _hoisted_114 = { class: "case-name" };
const _hoisted_115 = { class: "citation-link" };
const _hoisted_116 = { class: "citation-text" };
const _hoisted_117 = {
  key: 0,
  class: "pagination"
};
const _hoisted_118 = ["disabled"];
const _hoisted_119 = { class: "page-info" };
const _hoisted_120 = ["disabled"];
const _hoisted_121 = {
  key: 2,
  class: "empty-filter"
};
const _hoisted_122 = {
  key: 3,
  class: "no-results"
};
const _hoisted_123 = { class: "modal-body" };
const _hoisted_124 = { class: "detail-section" };
const _hoisted_125 = { class: "detail-grid" };
const _hoisted_126 = { class: "detail-item" };
const _hoisted_127 = { class: "detail-value" };
const _hoisted_128 = { class: "detail-item" };
const _hoisted_129 = { class: "detail-value" };
const _hoisted_130 = { class: "detail-item" };
const _hoisted_131 = { class: "detail-section" };
const _hoisted_132 = { class: "detail-grid" };
const _hoisted_133 = {
  key: 0,
  class: "detail-item"
};
const _hoisted_134 = { class: "detail-value" };
const _hoisted_135 = {
  key: 1,
  class: "detail-item"
};
const _hoisted_136 = { class: "detail-value" };
const _hoisted_137 = {
  key: 2,
  class: "detail-item"
};
const _hoisted_138 = { class: "detail-value" };
const _hoisted_139 = {
  key: 3,
  class: "detail-item"
};
const _hoisted_140 = { class: "detail-value" };
const _hoisted_141 = {
  key: 4,
  class: "detail-item"
};
const _hoisted_142 = { class: "detail-value" };
const _hoisted_143 = { class: "detail-section" };
const _hoisted_144 = { class: "detail-grid" };
const _hoisted_145 = {
  key: 0,
  class: "detail-item"
};
const _hoisted_146 = { class: "detail-value" };
const _hoisted_147 = {
  key: 1,
  class: "detail-item"
};
const _hoisted_148 = { class: "detail-value" };
const _hoisted_149 = {
  key: 2,
  class: "detail-item"
};
const _hoisted_150 = { class: "detail-value" };
const _hoisted_151 = {
  key: 3,
  class: "detail-item"
};
const _hoisted_152 = { class: "detail-value" };
const _hoisted_153 = { class: "detail-section" };
const _hoisted_154 = { class: "detail-grid" };
const _hoisted_155 = {
  key: 0,
  class: "detail-item"
};
const _hoisted_156 = { class: "detail-value" };
const _hoisted_157 = {
  key: 1,
  class: "detail-item"
};
const _hoisted_158 = { class: "detail-value" };
const _hoisted_159 = {
  key: 2,
  class: "detail-item"
};
const _hoisted_160 = { class: "detail-value" };
const _hoisted_161 = {
  key: 0,
  class: "detail-section"
};
const _hoisted_162 = { class: "raw-data" };
const _hoisted_163 = {
  key: 1,
  class: "detail-section"
};
const _hoisted_164 = { class: "parallel-citations" };
const itemsPerPage = 50;
const _sfc_main$4 = {
  __name: "CitationResults",
  props: {
    results: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ""
    }
  },
  emits: ["apply-correction", "copy-results", "download-results", "toast"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const activeFilter = ref("all");
    const searchQuery = ref("");
    const currentPage = ref(1);
    const selectedCitation = ref(null);
    const expandedCitations = ref(/* @__PURE__ */ new Set());
    const scoreTooltipGroup = ref(null);
    const validCount = computed(() => {
      var _a;
      if (!((_a = props.results) == null ? void 0 : _a.citations)) return 0;
      return props.results.citations.filter((c) => c.verified).length;
    });
    const invalidCount = computed(() => {
      var _a;
      if (!((_a = props.results) == null ? void 0 : _a.citations)) return 0;
      return props.results.citations.filter((c) => !c.verified).length;
    });
    const filteredCitations = computed(() => {
      var _a;
      if (!((_a = props.results) == null ? void 0 : _a.citations)) return [];
      let filtered = props.results.citations;
      if (activeFilter.value === "verified") {
        filtered = filtered.filter((c) => c.verified);
      } else if (activeFilter.value === "invalid") {
        filtered = filtered.filter((c) => !c.verified);
      }
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(
          (c) => c.citation.toLowerCase().includes(query) || getCaseName(c) && getCaseName(c).toLowerCase().includes(query) || getExtractedCaseName(c) && getExtractedCaseName(c).toLowerCase().includes(query) || getCourt(c) && getCourt(c).toLowerCase().includes(query) || getDocket(c) && getDocket(c).toLowerCase().includes(query) || getDateFiled(c) && getDateFiled(c).toLowerCase().includes(query) || getExtractedDate(c) && getExtractedDate(c).toLowerCase().includes(query) || getParallelCitations(c) && getParallelCitations(c).some((p) => p.toLowerCase().includes(query)) || getSource(c) && getSource(c).toLowerCase().includes(query)
        );
      }
      filtered.sort((a, b) => {
        const scoreA = a.score || 0;
        const scoreB = b.score || 0;
        return scoreA - scoreB;
      });
      return filtered;
    });
    const totalPages = computed(() => {
      return Math.ceil(filteredCitations.value.length / itemsPerPage);
    });
    const paginatedCitations = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage;
      const end = start + itemsPerPage;
      return filteredCitations.value.slice(start, end);
    });
    const filters = computed(() => {
      var _a, _b;
      return [
        { value: "all", label: "All", count: ((_b = (_a = props.results) == null ? void 0 : _a.citations) == null ? void 0 : _b.length) || 0 },
        { value: "verified", label: "Verified", count: validCount.value },
        { value: "invalid", label: "Invalid", count: invalidCount.value }
      ];
    });
    const groupedCitations = computed(() => {
      const verified = paginatedCitations.value.filter((c) => c.verified);
      const unverified = paginatedCitations.value.filter((c) => !c.verified);
      return [
        { status: "verified", citations: verified },
        { status: "unverified", citations: unverified }
      ].filter((group) => group.citations.length > 0);
    });
    const citationClusters = computed(() => {
      var _a;
      if (!((_a = props.results) == null ? void 0 : _a.citations)) return [];
      const clusters = /* @__PURE__ */ new Map();
      paginatedCitations.value.forEach((citation) => {
        const primaryCitation = citation.primary_citation || citation.citation;
        if (!clusters.has(primaryCitation)) {
          clusters.set(primaryCitation, {
            primary: null,
            parallels: [],
            isComplex: false
          });
        }
        const cluster = clusters.get(primaryCitation);
        if (citation.citation === primaryCitation || !citation.is_parallel_citation) {
          cluster.primary = citation;
        } else {
          cluster.parallels.push(citation);
        }
        if (citation.is_complex_citation) {
          cluster.isComplex = true;
        }
      });
      clusters.forEach((cluster) => {
        const seen = /* @__PURE__ */ new Set();
        cluster.parallels = cluster.parallels.filter((parallel) => {
          const key = parallel.canonical_citation || parallel.citation;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
      });
      return Array.from(clusters.values()).sort((a, b) => {
        var _a2, _b, _c, _d;
        const aVerified = ((_a2 = a.primary) == null ? void 0 : _a2.verified) || a.parallels.some((p) => p.verified);
        const bVerified = ((_b = b.primary) == null ? void 0 : _b.verified) || b.parallels.some((p) => p.verified);
        if (aVerified !== bVerified) return bVerified ? 1 : -1;
        const aText = ((_c = a.primary) == null ? void 0 : _c.citation) || "";
        const bText = ((_d = b.primary) == null ? void 0 : _d.citation) || "";
        return aText.localeCompare(bText);
      });
    });
    const getCaseName = (citation) => {
      var _a, _b;
      const canonical = citation.case_name || ((_a = citation.metadata) == null ? void 0 : _a.case_name) || ((_b = citation.group_metadata) == null ? void 0 : _b.case_name);
      if (canonical && canonical !== "N/A" && canonical.trim() !== "") return canonical;
      const extracted = citation.extracted_case_name || null;
      if (extracted && extracted !== "N/A" && extracted.trim() !== "") return extracted;
      return "N/A";
    };
    const getExtractedCaseName = (citation) => {
      return citation.extracted_case_name || null;
    };
    const getCaseNameSimilarity = (citation) => {
      return citation.case_name_similarity || null;
    };
    const getCaseNameMismatch = (citation) => {
      return citation.case_name_mismatch || false;
    };
    const getCourt = (citation) => {
      var _a, _b;
      return citation.court || ((_a = citation.metadata) == null ? void 0 : _a.court) || ((_b = citation.group_metadata) == null ? void 0 : _b.court) || null;
    };
    const getDocket = (citation) => {
      var _a, _b;
      return citation.docket_number || ((_a = citation.metadata) == null ? void 0 : _a.docket) || ((_b = citation.group_metadata) == null ? void 0 : _b.docket) || null;
    };
    const getDateFiled = (citation) => {
      var _a;
      return citation.date_filed || ((_a = citation.group_metadata) == null ? void 0 : _a.date_filed) || null;
    };
    const getExtractedDate = (citation) => {
      return citation.extracted_date || null;
    };
    const getCanonicalDate = (citation) => {
      var _a;
      return citation.canonical_date || ((_a = citation.group_metadata) == null ? void 0 : _a.canonical_date) || null;
    };
    const getParallelCitations = (citation) => {
      return citation.parallel_citations && citation.parallel_citations.length > 0 ? citation.parallel_citations : citation.all_citations || [];
    };
    const getCitationUrl = (citation) => {
      var _a, _b;
      return citation.url || ((_a = citation.metadata) == null ? void 0 : _a.url) || ((_b = citation.group_metadata) == null ? void 0 : _b.url) || null;
    };
    const getSource = (citation) => {
      var _a;
      const urlField = citation.url || "";
      if (urlField) {
        try {
          const domain = new URL(urlField).hostname.replace(/^www\./, "");
          return domain;
        } catch (e) {
          return urlField;
        }
      }
      const citationUrl = citation.citation_url || "";
      if (citationUrl) {
        try {
          const domain = new URL(citationUrl).hostname.replace(/^www\./, "");
          return domain;
        } catch (e) {
          return citationUrl;
        }
      }
      return citation.source || ((_a = citation.metadata) == null ? void 0 : _a.source) || "Unknown";
    };
    const getNote = (citation) => {
      return citation.note || null;
    };
    const formatDate = (dateString) => {
      if (!dateString) return "N/A";
      const yearMatch = /^\d{4}/.exec(dateString);
      if (yearMatch) return yearMatch[0];
      try {
        const date = new Date(dateString);
        return date.getFullYear();
      } catch (err) {
        return dateString;
      }
    };
    const getSimilarityClass = (similarity) => {
      if (similarity >= 0.8) return "high-similarity";
      if (similarity >= 0.6) return "medium-similarity";
      return "low-similarity";
    };
    const copyResults = async () => {
      try {
        const resultsText = filteredCitations.value.map((c) => `${c.citation} - ${c.verified ? "Verified" : "Invalid"}`).join("\n");
        await navigator.clipboard.writeText(resultsText);
        emit("copy-results");
        emit("toast", "Results copied to clipboard!", "success");
      } catch (err) {
        emit("toast", "Failed to copy results", "error");
      }
    };
    const downloadResults = () => {
      try {
        const data = {
          timestamp: (/* @__PURE__ */ new Date()).toISOString(),
          total: filteredCitations.value.length,
          verified: validCount.value,
          invalid: invalidCount.value,
          citations: filteredCitations.value.map((c) => ({
            citation: c.citation,
            verified: c.verified,
            case_name: getCaseName(c),
            extracted_case_name: getExtractedCaseName(c),
            case_name_similarity: getCaseNameSimilarity(c),
            case_name_mismatch: getCaseNameMismatch(c),
            court: getCourt(c),
            docket_number: getDocket(c),
            date_filed: getDateFiled(c),
            extracted_date: getExtractedDate(c),
            parallel_citations: getParallelCitations(c),
            url: getCitationUrl(c),
            source: getSource(c),
            note: getNote(c),
            metadata: c.metadata
            // Keep original metadata for backward compatibility
          }))
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `citation-results-${(/* @__PURE__ */ new Date()).toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        emit("download-results");
        emit("toast", "Results downloaded successfully!", "success");
      } catch (err) {
        emit("toast", "Failed to download results", "error");
      }
    };
    const resetPagination = () => {
      currentPage.value = 1;
    };
    watch(activeFilter, resetPagination);
    watch(searchQuery, resetPagination);
    const formatParallelCitation = (parallel) => {
      if (!parallel) return "";
      if (typeof parallel === "string") return parallel;
      if (typeof parallel === "object") {
        if (parallel.citation) return parallel.citation;
        if (parallel.cite) return parallel.cite;
        if (parallel.text) return parallel.text;
        if (parallel.volume || parallel.reporter || parallel.page) {
          const v = parallel.volume || "";
          const r = parallel.reporter || "";
          const p = parallel.page || "";
          const y = parallel.year || "";
          let citation = [v, r, p].filter(Boolean).join(" ");
          if (y && citation && !citation.includes(y)) citation += ` (${y})`;
          if (citation) return citation;
        }
        return String(parallel);
      }
      return String(parallel);
    };
    const getMainCitationText = (group) => {
      if (!group) return "";
      let citation = group.citation;
      if (Array.isArray(citation)) {
        if (citation.length > 0) return citation[0];
      } else if (typeof citation === "string") {
        return citation;
      }
      let canonical = group.canonical_citation;
      if (Array.isArray(canonical)) {
        if (canonical.length > 0) return canonical[0];
      } else if (typeof canonical === "string") {
        return canonical;
      }
      if (group.cite) return group.cite;
      if (group.text) return group.text;
      return "Citation not available";
    };
    const getOtherParallelCitations = (group) => {
      let citation = group.citation;
      if (Array.isArray(citation) && citation.length > 1) {
        return citation.slice(1);
      }
      if (!Array.isArray(citation) && Array.isArray(group.canonical_citation) && group.canonical_citation.length > 1) {
        return group.canonical_citation.slice(1);
      }
      if (Array.isArray(group.parallel_citations) && group.parallel_citations.length > 0) {
        return group.parallel_citations;
      }
      return [];
    };
    const closeCitationDetails = () => {
      selectedCitation.value = null;
    };
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return "N/A";
      try {
        return new Date(timestamp).toLocaleString();
      } catch (e) {
        return timestamp;
      }
    };
    const formatJson = (jsonString) => {
      if (!jsonString) return "N/A";
      try {
        const parsed = typeof jsonString === "string" ? JSON.parse(jsonString) : jsonString;
        return JSON.stringify(parsed, null, 2);
      } catch (e) {
        return jsonString;
      }
    };
    const toggleCitationDetails = (citation) => {
      if (expandedCitations.value.has(citation.citation)) {
        expandedCitations.value.delete(citation.citation);
      } else {
        expandedCitations.value.add(citation.citation);
      }
    };
    const getScoreDescription = (score) => {
      const descriptions = {
        0: "No verification data available",
        1: "Limited verification - some data available",
        2: "Good verification - case name found",
        3: "Very good verification - case name and additional data",
        4: "Excellent verification - all data matches"
      };
      return descriptions[score] || "Unknown score";
    };
    const showScoreTooltip = (group) => {
      scoreTooltipGroup.value = group;
    };
    const hideScoreTooltip = () => {
      scoreTooltipGroup.value = null;
    };
    const toggleScoreTooltip = (group) => {
      scoreTooltipGroup.value = scoreTooltipGroup.value === group ? null : group;
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$3, [
        __props.loading ? (openBlock(), createElementBlock("div", _hoisted_2$3, _cache[4] || (_cache[4] = [
          createBaseVNode("div", { class: "loading-spinner" }, null, -1),
          createBaseVNode("h3", null, "Analyzing citations...", -1)
        ]))) : __props.error ? (openBlock(), createElementBlock("div", _hoisted_3$2, [
          _cache[5] || (_cache[5] = createBaseVNode("div", { class: "error-icon" }, "❌", -1)),
          _cache[6] || (_cache[6] = createBaseVNode("h3", null, "Analysis Error", -1)),
          createBaseVNode("p", null, toDisplayString(__props.error), 1)
        ])) : __props.results && __props.results.citations && __props.results.citations.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_4$2, [
          createBaseVNode("div", _hoisted_5$2, [
            createBaseVNode("div", _hoisted_6$2, [
              _cache[10] || (_cache[10] = createBaseVNode("h2", null, "Citation Analysis Results", -1)),
              createBaseVNode("div", _hoisted_7$2, [
                createBaseVNode("div", _hoisted_8$2, [
                  createBaseVNode("span", _hoisted_9$2, toDisplayString(__props.results.citations.length), 1),
                  _cache[7] || (_cache[7] = createBaseVNode("span", { class: "stat-label" }, "Total", -1))
                ]),
                createBaseVNode("div", _hoisted_10$2, [
                  createBaseVNode("span", _hoisted_11$2, toDisplayString(validCount.value), 1),
                  _cache[8] || (_cache[8] = createBaseVNode("span", { class: "stat-label" }, "Verified", -1))
                ]),
                createBaseVNode("div", _hoisted_12$2, [
                  createBaseVNode("span", _hoisted_13$2, toDisplayString(invalidCount.value), 1),
                  _cache[9] || (_cache[9] = createBaseVNode("span", { class: "stat-label" }, "Invalid", -1))
                ])
              ])
            ]),
            createBaseVNode("div", { class: "action-buttons" }, [
              createBaseVNode("button", {
                onClick: copyResults,
                class: "action-btn copy-btn"
              }, _cache[11] || (_cache[11] = [
                createBaseVNode("span", { class: "btn-icon" }, "📋", -1),
                createTextVNode(" Copy Results ")
              ])),
              createBaseVNode("button", {
                onClick: downloadResults,
                class: "action-btn download-btn"
              }, _cache[12] || (_cache[12] = [
                createBaseVNode("span", { class: "btn-icon" }, "💾", -1),
                createTextVNode(" Download ")
              ]))
            ])
          ]),
          __props.results.stats ? (openBlock(), createElementBlock("div", _hoisted_14$2, [
            _cache[17] || (_cache[17] = createBaseVNode("h3", null, "Processing Breakdown", -1)),
            createBaseVNode("div", _hoisted_15$2, [
              createBaseVNode("div", _hoisted_16$2, [
                createBaseVNode("span", _hoisted_17$2, toDisplayString(__props.results.stats.total_extracted), 1),
                _cache[13] || (_cache[13] = createBaseVNode("span", { class: "stat-title" }, "Extracted", -1))
              ]),
              createBaseVNode("div", _hoisted_18$2, [
                createBaseVNode("span", _hoisted_19$2, toDisplayString(__props.results.stats.deduplicated), 1),
                _cache[14] || (_cache[14] = createBaseVNode("span", { class: "stat-title" }, "Unique", -1))
              ]),
              createBaseVNode("div", _hoisted_20$2, [
                createBaseVNode("span", _hoisted_21$2, toDisplayString(__props.results.stats.verified_in_cache + __props.results.stats.verified_in_json_array + __props.results.stats.verified_in_text_blob + __props.results.stats.verified_in_single + __props.results.stats.verified_in_langsearch), 1),
                _cache[15] || (_cache[15] = createBaseVNode("span", { class: "stat-title" }, "Verified", -1))
              ]),
              createBaseVNode("div", _hoisted_22$2, [
                createBaseVNode("span", _hoisted_23$2, toDisplayString(__props.results.stats.not_verified), 1),
                _cache[16] || (_cache[16] = createBaseVNode("span", { class: "stat-title" }, "Not Verified", -1))
              ])
            ])
          ])) : createCommentVNode("", true),
          createBaseVNode("div", _hoisted_24$2, [
            createBaseVNode("div", _hoisted_25$1, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(filters.value, (filter) => {
                return openBlock(), createElementBlock("button", {
                  key: filter.value,
                  class: normalizeClass(["filter-btn", { active: activeFilter.value === filter.value }]),
                  onClick: ($event) => activeFilter.value = filter.value
                }, [
                  createTextVNode(toDisplayString(filter.label) + " ", 1),
                  createBaseVNode("span", _hoisted_27$1, "(" + toDisplayString(filter.count) + ")", 1)
                ], 10, _hoisted_26$1);
              }), 128))
            ]),
            createBaseVNode("div", _hoisted_28$1, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => searchQuery.value = $event),
                type: "text",
                placeholder: "Search citations...",
                class: "search-input"
              }, null, 512), [
                [vModelText, searchQuery.value]
              ])
            ])
          ]),
          filteredCitations.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_29$1, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(groupedCitations.value, (group, groupIndex) => {
              return openBlock(), createElementBlock(Fragment, {
                key: group.status
              }, [
                createBaseVNode("div", {
                  class: normalizeClass(["group-header", group.status])
                }, [
                  group.status === "verified" ? (openBlock(), createElementBlock("span", _hoisted_30$1, "✔️")) : group.status === "unverified" ? (openBlock(), createElementBlock("span", _hoisted_31$1, "❌")) : createCommentVNode("", true),
                  createBaseVNode("span", _hoisted_32$1, toDisplayString(group.status === "verified" ? "Verified Citations" : "Unverified Citations") + " (" + toDisplayString(group.citations.length) + ") ", 1)
                ], 2),
                (openBlock(true), createElementBlock(Fragment, null, renderList(citationClusters.value.filter((c) => {
                  var _a;
                  const isVerified = ((_a = c.primary) == null ? void 0 : _a.verified) || c.parallels.some((p) => p.verified);
                  return group.status === "verified" ? isVerified : !isVerified;
                }), (cluster) => {
                  var _a;
                  return openBlock(), createElementBlock("div", {
                    key: ((_a = cluster.primary) == null ? void 0 : _a.citation) || "cluster",
                    class: "citation-cluster"
                  }, [
                    cluster.primary ? (openBlock(), createElementBlock("div", {
                      key: 0,
                      class: normalizeClass(["citation-item", { verified: cluster.primary.verified, invalid: !cluster.primary.verified }])
                    }, [
                      createBaseVNode("div", _hoisted_33$1, [
                        createBaseVNode("div", _hoisted_34$1, [
                          _cache[22] || (_cache[22] = createBaseVNode("div", {
                            class: "primary-badge",
                            title: "Primary citation in this cluster"
                          }, " 🎯 Primary ", -1)),
                          createBaseVNode("div", {
                            class: normalizeClass(["score-flag", `score-${cluster.primary.scoreColor}`]),
                            title: getScoreDescription(cluster.primary.score),
                            onMouseenter: ($event) => showScoreTooltip(cluster.primary),
                            onMouseleave: hideScoreTooltip,
                            onClick: ($event) => toggleScoreTooltip(cluster.primary),
                            style: { "cursor": "pointer", "position": "relative" }
                          }, [
                            createTextVNode(toDisplayString(cluster.primary.score) + "/4 ", 1),
                            scoreTooltipGroup.value === cluster.primary ? (openBlock(), createElementBlock("div", _hoisted_36$1, [
                              _cache[21] || (_cache[21] = createBaseVNode("div", null, [
                                createBaseVNode("strong", null, "Score Breakdown:")
                              ], -1)),
                              createBaseVNode("div", null, [
                                _cache[18] || (_cache[18] = createTextVNode("Case name match: ")),
                                createBaseVNode("span", {
                                  class: normalizeClass({ "text-success": cluster.primary.case_name && cluster.primary.case_name !== "N/A" })
                                }, toDisplayString(cluster.primary.case_name && cluster.primary.case_name !== "N/A" ? "+2" : "0"), 3)
                              ]),
                              createBaseVNode("div", null, [
                                _cache[19] || (_cache[19] = createTextVNode("Hinted name similarity: ")),
                                createBaseVNode("span", {
                                  class: normalizeClass({ "text-success": getCaseNameSimilarity(cluster.primary) >= 0.5 })
                                }, toDisplayString(getCaseNameSimilarity(cluster.primary) >= 0.5 ? "+1" : "0"), 3)
                              ]),
                              createBaseVNode("div", null, [
                                _cache[20] || (_cache[20] = createTextVNode("Year match: ")),
                                createBaseVNode("span", {
                                  class: normalizeClass({ "text-success": getExtractedDate(cluster.primary) && getCanonicalDate(cluster.primary) && getExtractedDate(cluster.primary).substring(0, 4) === getCanonicalDate(cluster.primary).substring(0, 4) })
                                }, toDisplayString(getExtractedDate(cluster.primary) && getCanonicalDate(cluster.primary) && getExtractedDate(cluster.primary).substring(0, 4) === getCanonicalDate(cluster.primary).substring(0, 4) ? "+1" : "0"), 3)
                              ])
                            ])) : createCommentVNode("", true)
                          ], 42, _hoisted_35$1),
                          createBaseVNode("div", _hoisted_37$1, [
                            cluster.primary.verified && getCitationUrl(cluster.primary) ? (openBlock(), createElementBlock("a", {
                              key: 0,
                              href: getCitationUrl(cluster.primary),
                              target: "_blank",
                              class: "case-name-link",
                              title: "View case details"
                            }, toDisplayString(getCaseName(cluster.primary) || "Unknown Case"), 9, _hoisted_38$1)) : (openBlock(), createElementBlock("span", _hoisted_39$1, toDisplayString(getCaseName(cluster.primary) || "Unknown Case"), 1))
                          ]),
                          createBaseVNode("div", _hoisted_40$1, [
                            cluster.primary.verified && getCitationUrl(cluster.primary) ? (openBlock(), createElementBlock("a", {
                              key: 0,
                              href: getCitationUrl(cluster.primary),
                              target: "_blank",
                              class: "citation-hyperlink",
                              title: "View case details"
                            }, toDisplayString(getMainCitationText(cluster.primary)), 9, _hoisted_41$1)) : (openBlock(), createElementBlock("span", _hoisted_42, toDisplayString(getMainCitationText(cluster.primary)), 1)),
                            cluster.isComplex ? (openBlock(), createElementBlock("span", _hoisted_43, " 🔗 ")) : createCommentVNode("", true)
                          ])
                        ]),
                        createBaseVNode("div", _hoisted_44, [
                          createBaseVNode("button", {
                            onClick: ($event) => toggleCitationDetails(cluster.primary),
                            class: normalizeClass(["expand-btn", { expanded: expandedCitations.value.has(cluster.primary.citation) }]),
                            title: expandedCitations.value.has(cluster.primary.citation) ? "Hide details" : "Show details"
                          }, toDisplayString(expandedCitations.value.has(cluster.primary.citation) ? "▼" : "▶"), 11, _hoisted_45)
                        ])
                      ]),
                      expandedCitations.value.has(cluster.primary.citation) ? (openBlock(), createElementBlock("div", _hoisted_46, [
                        createBaseVNode("div", _hoisted_47, [
                          _cache[29] || (_cache[29] = createBaseVNode("h4", { class: "section-title" }, "Citation Information", -1)),
                          createBaseVNode("div", _hoisted_48, [
                            _cache[23] || (_cache[23] = createBaseVNode("span", { class: "detail-label" }, "Citation Text:", -1)),
                            _cache[24] || (_cache[24] = createTextVNode()),
                            createBaseVNode("span", _hoisted_49, toDisplayString(getMainCitationText(cluster.primary)), 1)
                          ]),
                          cluster.primary.id ? (openBlock(), createElementBlock("div", _hoisted_50, [
                            _cache[25] || (_cache[25] = createBaseVNode("span", { class: "detail-label" }, "Database ID:", -1)),
                            _cache[26] || (_cache[26] = createTextVNode()),
                            createBaseVNode("span", _hoisted_51, toDisplayString(cluster.primary.id), 1)
                          ])) : createCommentVNode("", true),
                          createBaseVNode("div", _hoisted_52, [
                            _cache[27] || (_cache[27] = createBaseVNode("span", { class: "detail-label" }, "Status:", -1)),
                            _cache[28] || (_cache[28] = createTextVNode()),
                            createBaseVNode("span", {
                              class: normalizeClass(["detail-value", cluster.primary.verified ? "verified" : "invalid"])
                            }, toDisplayString(cluster.primary.verified ? "Verified" : "Not Verified"), 3)
                          ])
                        ]),
                        createBaseVNode("div", _hoisted_53, [
                          _cache[39] || (_cache[39] = createBaseVNode("h4", { class: "section-title" }, "Case Information", -1)),
                          createBaseVNode("div", _hoisted_54, [
                            _cache[30] || (_cache[30] = createBaseVNode("span", { class: "detail-label" }, "Canonical Case Name:", -1)),
                            _cache[31] || (_cache[31] = createTextVNode()),
                            createBaseVNode("span", _hoisted_55, toDisplayString(getCaseName(cluster.primary) || "N/A"), 1)
                          ]),
                          createBaseVNode("div", _hoisted_56, [
                            _cache[32] || (_cache[32] = createBaseVNode("span", { class: "detail-label" }, "Extracted Case Name:", -1)),
                            _cache[33] || (_cache[33] = createTextVNode()),
                            createBaseVNode("span", _hoisted_57, toDisplayString(getExtractedCaseName(cluster.primary) || "N/A"), 1)
                          ]),
                          createBaseVNode("div", _hoisted_58, [
                            _cache[34] || (_cache[34] = createBaseVNode("span", { class: "detail-label" }, "Hinted Case Name:", -1)),
                            _cache[35] || (_cache[35] = createTextVNode()),
                            createBaseVNode("span", _hoisted_59, toDisplayString(cluster.primary.hinted_case_name || "N/A"), 1)
                          ]),
                          getCaseNameSimilarity(cluster.primary) !== null ? (openBlock(), createElementBlock("div", _hoisted_60, [
                            _cache[36] || (_cache[36] = createBaseVNode("span", { class: "detail-label" }, "Name Similarity:", -1)),
                            _cache[37] || (_cache[37] = createTextVNode()),
                            createBaseVNode("span", {
                              class: normalizeClass(["detail-value", getSimilarityClass(getCaseNameSimilarity(cluster.primary))])
                            }, toDisplayString((getCaseNameSimilarity(cluster.primary) * 100).toFixed(1)) + "%", 3)
                          ])) : createCommentVNode("", true),
                          getCaseNameMismatch(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_61, _cache[38] || (_cache[38] = [
                            createBaseVNode("span", { class: "detail-label" }, "Name Mismatch:", -1),
                            createTextVNode(),
                            createBaseVNode("span", { class: "detail-value warning" }, "⚠️ Case names differ significantly", -1)
                          ]))) : createCommentVNode("", true)
                        ]),
                        createBaseVNode("div", _hoisted_62, [
                          _cache[50] || (_cache[50] = createBaseVNode("h4", { class: "section-title" }, "Citation Components", -1)),
                          cluster.primary.volume ? (openBlock(), createElementBlock("div", _hoisted_63, [
                            _cache[40] || (_cache[40] = createBaseVNode("span", { class: "detail-label" }, "Volume:", -1)),
                            _cache[41] || (_cache[41] = createTextVNode()),
                            createBaseVNode("span", _hoisted_64, toDisplayString(cluster.primary.volume), 1)
                          ])) : createCommentVNode("", true),
                          cluster.primary.reporter ? (openBlock(), createElementBlock("div", _hoisted_65, [
                            _cache[42] || (_cache[42] = createBaseVNode("span", { class: "detail-label" }, "Reporter:", -1)),
                            _cache[43] || (_cache[43] = createTextVNode()),
                            createBaseVNode("span", _hoisted_66, toDisplayString(cluster.primary.reporter), 1)
                          ])) : createCommentVNode("", true),
                          cluster.primary.page ? (openBlock(), createElementBlock("div", _hoisted_67, [
                            _cache[44] || (_cache[44] = createBaseVNode("span", { class: "detail-label" }, "Page:", -1)),
                            _cache[45] || (_cache[45] = createTextVNode()),
                            createBaseVNode("span", _hoisted_68, toDisplayString(cluster.primary.page), 1)
                          ])) : createCommentVNode("", true),
                          cluster.primary.year ? (openBlock(), createElementBlock("div", _hoisted_69, [
                            _cache[46] || (_cache[46] = createBaseVNode("span", { class: "detail-label" }, "Year:", -1)),
                            _cache[47] || (_cache[47] = createTextVNode()),
                            createBaseVNode("span", _hoisted_70, toDisplayString(cluster.primary.year), 1)
                          ])) : createCommentVNode("", true),
                          cluster.primary.court ? (openBlock(), createElementBlock("div", _hoisted_71, [
                            _cache[48] || (_cache[48] = createBaseVNode("span", { class: "detail-label" }, "Court:", -1)),
                            _cache[49] || (_cache[49] = createTextVNode()),
                            createBaseVNode("span", _hoisted_72, toDisplayString(cluster.primary.court), 1)
                          ])) : createCommentVNode("", true)
                        ]),
                        getDateFiled(cluster.primary) || getExtractedDate(cluster.primary) || getCanonicalDate(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_73, [
                          _cache[59] || (_cache[59] = createBaseVNode("h4", { class: "section-title" }, "Decision Information", -1)),
                          createBaseVNode("div", _hoisted_74, [
                            _cache[51] || (_cache[51] = createBaseVNode("span", { class: "detail-label" }, "Extracted Date:", -1)),
                            _cache[52] || (_cache[52] = createTextVNode()),
                            createBaseVNode("span", _hoisted_75, toDisplayString(formatDate(getExtractedDate(cluster.primary)) || "N/A"), 1)
                          ]),
                          getCanonicalDate(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_76, [
                            _cache[53] || (_cache[53] = createBaseVNode("span", { class: "detail-label" }, "Canonical Date (Case Name):", -1)),
                            _cache[54] || (_cache[54] = createTextVNode()),
                            createBaseVNode("span", _hoisted_77, toDisplayString(formatDate(getCanonicalDate(cluster.primary))), 1)
                          ])) : createCommentVNode("", true),
                          getDateFiled(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_78, [
                            _cache[55] || (_cache[55] = createBaseVNode("span", { class: "detail-label" }, "Canonical Date (Verified):", -1)),
                            _cache[56] || (_cache[56] = createTextVNode()),
                            createBaseVNode("span", _hoisted_79, toDisplayString(formatDate(getDateFiled(cluster.primary))), 1)
                          ])) : createCommentVNode("", true),
                          getExtractedDate(cluster.primary) && getDateFiled(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_80, [
                            _cache[57] || (_cache[57] = createBaseVNode("span", { class: "detail-label" }, "Date Match:", -1)),
                            _cache[58] || (_cache[58] = createTextVNode()),
                            createBaseVNode("span", {
                              class: normalizeClass(["detail-value", getExtractedDate(cluster.primary) === getDateFiled(cluster.primary) ? "high-similarity" : "low-similarity"])
                            }, toDisplayString(getExtractedDate(cluster.primary) === getDateFiled(cluster.primary) ? "✓ Match" : "✗ Different"), 3)
                          ])) : createCommentVNode("", true)
                        ])) : createCommentVNode("", true),
                        cluster.primary.context ? (openBlock(), createElementBlock("div", _hoisted_81, [
                          _cache[60] || (_cache[60] = createBaseVNode("h4", { class: "section-title" }, "Context", -1)),
                          createBaseVNode("div", _hoisted_82, toDisplayString(cluster.primary.context), 1)
                        ])) : createCommentVNode("", true),
                        cluster.parallels.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_83, [
                          _cache[62] || (_cache[62] = createBaseVNode("h4", { class: "section-title" }, "Parallel Citations in This Cluster", -1)),
                          createBaseVNode("div", _hoisted_84, [
                            (openBlock(true), createElementBlock(Fragment, null, renderList(cluster.parallels, (parallel, index) => {
                              return openBlock(), createElementBlock("div", {
                                key: index,
                                class: "parallel-citation-item"
                              }, [
                                _cache[61] || (_cache[61] = createBaseVNode("span", {
                                  class: "parallel-badge",
                                  title: "Parallel citation"
                                }, "🔗 Parallel", -1)),
                                createBaseVNode("span", _hoisted_85, toDisplayString(parallel.citation), 1),
                                parallel.verified === "true_by_parallel" ? (openBlock(), createElementBlock("span", _hoisted_86, "✓ Inherited")) : createCommentVNode("", true)
                              ]);
                            }), 128))
                          ])
                        ])) : createCommentVNode("", true),
                        createBaseVNode("div", _hoisted_87, [
                          _cache[69] || (_cache[69] = createBaseVNode("h4", { class: "section-title" }, "Verification Details", -1)),
                          createBaseVNode("div", _hoisted_88, [
                            _cache[63] || (_cache[63] = createBaseVNode("span", { class: "detail-label" }, "Source:", -1)),
                            _cache[64] || (_cache[64] = createTextVNode()),
                            createBaseVNode("span", _hoisted_89, toDisplayString(getSource(cluster.primary) || "N/A"), 1)
                          ]),
                          cluster.primary.confidence !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_90, [
                            _cache[65] || (_cache[65] = createBaseVNode("span", { class: "detail-label" }, "Confidence:", -1)),
                            _cache[66] || (_cache[66] = createTextVNode()),
                            createBaseVNode("span", _hoisted_91, toDisplayString((cluster.primary.confidence * 100).toFixed(1)) + "%", 1)
                          ])) : createCommentVNode("", true),
                          getNote(cluster.primary) ? (openBlock(), createElementBlock("div", _hoisted_92, [
                            _cache[67] || (_cache[67] = createBaseVNode("span", { class: "detail-label" }, "Note:", -1)),
                            _cache[68] || (_cache[68] = createTextVNode()),
                            createBaseVNode("span", _hoisted_93, toDisplayString(getNote(cluster.primary)), 1)
                          ])) : createCommentVNode("", true)
                        ]),
                        cluster.isComplex && cluster.primary.complex_metadata ? (openBlock(), createElementBlock("div", _hoisted_94, [
                          _cache[77] || (_cache[77] = createBaseVNode("h4", { class: "section-title" }, "Complex Citation Details", -1)),
                          createBaseVNode("div", _hoisted_95, [
                            cluster.primary.complex_metadata.primary_citation ? (openBlock(), createElementBlock("div", _hoisted_96, [
                              _cache[70] || (_cache[70] = createBaseVNode("span", { class: "detail-label" }, "Primary Citation:", -1)),
                              createBaseVNode("span", _hoisted_97, toDisplayString(cluster.primary.complex_metadata.primary_citation), 1)
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.parallel_citations && cluster.primary.complex_metadata.parallel_citations.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_98, [
                              _cache[71] || (_cache[71] = createBaseVNode("span", { class: "detail-label" }, "Parallel Citations:", -1)),
                              createBaseVNode("div", _hoisted_99, [
                                (openBlock(true), createElementBlock(Fragment, null, renderList(cluster.primary.complex_metadata.parallel_citations, (parallel, index) => {
                                  return openBlock(), createElementBlock("span", {
                                    key: index,
                                    class: "parallel-citation-tag"
                                  }, toDisplayString(parallel), 1);
                                }), 128))
                              ])
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.pinpoint_pages && cluster.primary.complex_metadata.pinpoint_pages.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_100, [
                              _cache[72] || (_cache[72] = createBaseVNode("span", { class: "detail-label" }, "Pinpoint Pages:", -1)),
                              createBaseVNode("span", _hoisted_101, toDisplayString(cluster.primary.complex_metadata.pinpoint_pages.join(", ")), 1)
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.docket_numbers && cluster.primary.complex_metadata.docket_numbers.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_102, [
                              _cache[73] || (_cache[73] = createBaseVNode("span", { class: "detail-label" }, "Docket Numbers:", -1)),
                              createBaseVNode("span", _hoisted_103, toDisplayString(cluster.primary.complex_metadata.docket_numbers.join(", ")), 1)
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.case_history && cluster.primary.complex_metadata.case_history.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_104, [
                              _cache[74] || (_cache[74] = createBaseVNode("span", { class: "detail-label" }, "Case History:", -1)),
                              createBaseVNode("span", _hoisted_105, toDisplayString(cluster.primary.complex_metadata.case_history.join(", ")), 1)
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.publication_status ? (openBlock(), createElementBlock("div", _hoisted_106, [
                              _cache[75] || (_cache[75] = createBaseVNode("span", { class: "detail-label" }, "Publication Status:", -1)),
                              createBaseVNode("span", _hoisted_107, toDisplayString(cluster.primary.complex_metadata.publication_status), 1)
                            ])) : createCommentVNode("", true),
                            cluster.primary.complex_metadata.year ? (openBlock(), createElementBlock("div", _hoisted_108, [
                              _cache[76] || (_cache[76] = createBaseVNode("span", { class: "detail-label" }, "Year:", -1)),
                              createBaseVNode("span", _hoisted_109, toDisplayString(cluster.primary.complex_metadata.year), 1)
                            ])) : createCommentVNode("", true)
                          ])
                        ])) : createCommentVNode("", true)
                      ])) : createCommentVNode("", true)
                    ], 2)) : createCommentVNode("", true),
                    cluster.parallels.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_110, [
                      (openBlock(true), createElementBlock(Fragment, null, renderList(cluster.parallels, (parallel) => {
                        return openBlock(), createElementBlock("div", {
                          key: parallel.citation,
                          class: normalizeClass(["citation-item", "parallel-item", { verified: parallel.verified, invalid: !parallel.verified }])
                        }, [
                          createBaseVNode("div", _hoisted_111, [
                            createBaseVNode("div", _hoisted_112, [
                              _cache[78] || (_cache[78] = createBaseVNode("div", {
                                class: "parallel-badge",
                                title: "Parallel citation"
                              }, " 🔗 Parallel ", -1)),
                              parallel.verified === "true_by_parallel" ? (openBlock(), createElementBlock("div", _hoisted_113, " ✓ Inherited ")) : createCommentVNode("", true),
                              createBaseVNode("div", _hoisted_114, [
                                createBaseVNode("span", null, toDisplayString(getCaseName(parallel) || "Unknown Case"), 1)
                              ]),
                              createBaseVNode("div", _hoisted_115, [
                                createBaseVNode("span", _hoisted_116, toDisplayString(getMainCitationText(parallel)), 1)
                              ])
                            ])
                          ])
                        ], 2);
                      }), 128))
                    ])) : createCommentVNode("", true)
                  ]);
                }), 128))
              ], 64);
            }), 128)),
            totalPages.value > 1 ? (openBlock(), createElementBlock("div", _hoisted_117, [
              createBaseVNode("button", {
                onClick: _cache[1] || (_cache[1] = ($event) => currentPage.value--),
                disabled: currentPage.value <= 1,
                class: "pagination-btn"
              }, " ← Previous ", 8, _hoisted_118),
              createBaseVNode("span", _hoisted_119, "Page " + toDisplayString(currentPage.value) + " of " + toDisplayString(totalPages.value), 1),
              createBaseVNode("button", {
                onClick: _cache[2] || (_cache[2] = ($event) => currentPage.value++),
                disabled: currentPage.value >= totalPages.value,
                class: "pagination-btn"
              }, " Next → ", 8, _hoisted_120)
            ])) : createCommentVNode("", true)
          ])) : createCommentVNode("", true),
          filteredCitations.value.length === 0 && __props.results.citations.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_121, _cache[79] || (_cache[79] = [
            createBaseVNode("div", { class: "empty-icon" }, "🔍", -1),
            createBaseVNode("h3", null, "No citations match your filter", -1),
            createBaseVNode("p", null, "Try adjusting your search or filter criteria", -1)
          ]))) : createCommentVNode("", true)
        ])) : (openBlock(), createElementBlock("div", _hoisted_122, _cache[80] || (_cache[80] = [
          createBaseVNode("div", { class: "no-results-icon" }, "📄", -1),
          createBaseVNode("h3", null, "No Citations Found", -1),
          createBaseVNode("p", null, "The document didn't contain any recognizable legal citations", -1)
        ]))),
        selectedCitation.value ? (openBlock(), createElementBlock("div", {
          key: 4,
          class: "modal-overlay",
          onClick: closeCitationDetails
        }, [
          createBaseVNode("div", {
            class: "modal-content",
            onClick: _cache[3] || (_cache[3] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", { class: "modal-header" }, [
              _cache[81] || (_cache[81] = createBaseVNode("h3", null, "Citation Details", -1)),
              createBaseVNode("button", {
                onClick: closeCitationDetails,
                class: "modal-close"
              }, "×")
            ]),
            createBaseVNode("div", _hoisted_123, [
              createBaseVNode("div", _hoisted_124, [
                _cache[85] || (_cache[85] = createBaseVNode("h4", null, "Citation Information", -1)),
                createBaseVNode("div", _hoisted_125, [
                  createBaseVNode("div", _hoisted_126, [
                    _cache[82] || (_cache[82] = createBaseVNode("span", { class: "detail-label" }, "Citation Text:", -1)),
                    createBaseVNode("span", _hoisted_127, toDisplayString(getMainCitationText(selectedCitation.value)), 1)
                  ]),
                  createBaseVNode("div", _hoisted_128, [
                    _cache[83] || (_cache[83] = createBaseVNode("span", { class: "detail-label" }, "Database ID:", -1)),
                    createBaseVNode("span", _hoisted_129, toDisplayString(selectedCitation.value.id || "N/A"), 1)
                  ]),
                  createBaseVNode("div", _hoisted_130, [
                    _cache[84] || (_cache[84] = createBaseVNode("span", { class: "detail-label" }, "Status:", -1)),
                    createBaseVNode("span", {
                      class: normalizeClass(["detail-value", selectedCitation.value.verified ? "verified" : "invalid"])
                    }, toDisplayString(selectedCitation.value.verified ? "Verified" : "Not Verified"), 3)
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_131, [
                _cache[91] || (_cache[91] = createBaseVNode("h4", null, "Citation Components", -1)),
                createBaseVNode("div", _hoisted_132, [
                  selectedCitation.value.volume ? (openBlock(), createElementBlock("div", _hoisted_133, [
                    _cache[86] || (_cache[86] = createBaseVNode("span", { class: "detail-label" }, "Volume:", -1)),
                    createBaseVNode("span", _hoisted_134, toDisplayString(selectedCitation.value.volume), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.reporter ? (openBlock(), createElementBlock("div", _hoisted_135, [
                    _cache[87] || (_cache[87] = createBaseVNode("span", { class: "detail-label" }, "Reporter:", -1)),
                    createBaseVNode("span", _hoisted_136, toDisplayString(selectedCitation.value.reporter), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.page ? (openBlock(), createElementBlock("div", _hoisted_137, [
                    _cache[88] || (_cache[88] = createBaseVNode("span", { class: "detail-label" }, "Page:", -1)),
                    createBaseVNode("span", _hoisted_138, toDisplayString(selectedCitation.value.page), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.year ? (openBlock(), createElementBlock("div", _hoisted_139, [
                    _cache[89] || (_cache[89] = createBaseVNode("span", { class: "detail-label" }, "Year:", -1)),
                    createBaseVNode("span", _hoisted_140, toDisplayString(selectedCitation.value.year), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.court ? (openBlock(), createElementBlock("div", _hoisted_141, [
                    _cache[90] || (_cache[90] = createBaseVNode("span", { class: "detail-label" }, "Court:", -1)),
                    createBaseVNode("span", _hoisted_142, toDisplayString(selectedCitation.value.court), 1)
                  ])) : createCommentVNode("", true)
                ])
              ]),
              createBaseVNode("div", _hoisted_143, [
                _cache[96] || (_cache[96] = createBaseVNode("h4", null, "Verification Details", -1)),
                createBaseVNode("div", _hoisted_144, [
                  selectedCitation.value.verification_source ? (openBlock(), createElementBlock("div", _hoisted_145, [
                    _cache[92] || (_cache[92] = createBaseVNode("span", { class: "detail-label" }, "Verification Source:", -1)),
                    createBaseVNode("span", _hoisted_146, toDisplayString(selectedCitation.value.verification_source), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.verification_confidence !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_147, [
                    _cache[93] || (_cache[93] = createBaseVNode("span", { class: "detail-label" }, "Verification Confidence:", -1)),
                    createBaseVNode("span", _hoisted_148, toDisplayString((selectedCitation.value.verification_confidence * 100).toFixed(1)) + "%", 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.verification_count !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_149, [
                    _cache[94] || (_cache[94] = createBaseVNode("span", { class: "detail-label" }, "Times Verified:", -1)),
                    createBaseVNode("span", _hoisted_150, toDisplayString(selectedCitation.value.verification_count), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.error_count !== void 0 ? (openBlock(), createElementBlock("div", _hoisted_151, [
                    _cache[95] || (_cache[95] = createBaseVNode("span", { class: "detail-label" }, "Verification Errors:", -1)),
                    createBaseVNode("span", _hoisted_152, toDisplayString(selectedCitation.value.error_count), 1)
                  ])) : createCommentVNode("", true)
                ])
              ]),
              createBaseVNode("div", _hoisted_153, [
                _cache[100] || (_cache[100] = createBaseVNode("h4", null, "Database Timestamps", -1)),
                createBaseVNode("div", _hoisted_154, [
                  selectedCitation.value.created_at ? (openBlock(), createElementBlock("div", _hoisted_155, [
                    _cache[97] || (_cache[97] = createBaseVNode("span", { class: "detail-label" }, "First Added:", -1)),
                    createBaseVNode("span", _hoisted_156, toDisplayString(formatTimestamp(selectedCitation.value.created_at)), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.updated_at ? (openBlock(), createElementBlock("div", _hoisted_157, [
                    _cache[98] || (_cache[98] = createBaseVNode("span", { class: "detail-label" }, "Last Updated:", -1)),
                    createBaseVNode("span", _hoisted_158, toDisplayString(formatTimestamp(selectedCitation.value.updated_at)), 1)
                  ])) : createCommentVNode("", true),
                  selectedCitation.value.last_verified_at ? (openBlock(), createElementBlock("div", _hoisted_159, [
                    _cache[99] || (_cache[99] = createBaseVNode("span", { class: "detail-label" }, "Last Verified:", -1)),
                    createBaseVNode("span", _hoisted_160, toDisplayString(formatTimestamp(selectedCitation.value.last_verified_at)), 1)
                  ])) : createCommentVNode("", true)
                ])
              ]),
              selectedCitation.value.verification_result ? (openBlock(), createElementBlock("div", _hoisted_161, [
                _cache[101] || (_cache[101] = createBaseVNode("h4", null, "Raw Verification Data", -1)),
                createBaseVNode("div", _hoisted_162, [
                  createBaseVNode("pre", null, toDisplayString(formatJson(selectedCitation.value.verification_result)), 1)
                ])
              ])) : createCommentVNode("", true),
              getOtherParallelCitations(selectedCitation.value) && getOtherParallelCitations(selectedCitation.value).length > 0 ? (openBlock(), createElementBlock("div", _hoisted_163, [
                _cache[102] || (_cache[102] = createBaseVNode("h4", null, "Additional Parallel Citations", -1)),
                createBaseVNode("div", _hoisted_164, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(getOtherParallelCitations(selectedCitation.value), (parallel, index) => {
                    return openBlock(), createElementBlock("span", {
                      key: index,
                      class: "parallel-citation"
                    }, toDisplayString(formatParallelCitation(parallel)), 1);
                  }), 128))
                ])
              ])) : createCommentVNode("", true)
            ]),
            createBaseVNode("div", { class: "modal-footer" }, [
              createBaseVNode("button", {
                onClick: closeCitationDetails,
                class: "btn btn-secondary"
              }, "Close")
            ])
          ])
        ])) : createCommentVNode("", true)
      ]);
    };
  }
};
const CitationResults = /* @__PURE__ */ _export_sfc(_sfc_main$4, [["__scopeId", "data-v-fa09b1fb"]]);
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
const _hoisted_17$1 = ["disabled"];
const _hoisted_18$1 = { class: "input-footer" };
const _hoisted_19$1 = {
  key: 0,
  class: "url-preview"
};
const _hoisted_20$1 = {
  key: 1,
  class: "url-error"
};
const _hoisted_21$1 = {
  key: 0,
  class: "validation-errors"
};
const _hoisted_22$1 = { class: "input-methods-bottom" };
const _hoisted_23$1 = { class: "method-icon" };
const _hoisted_24$1 = { class: "method-content" };
const _hoisted_25 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_26 = { class: "method-icon" };
const _hoisted_27 = { class: "method-content" };
const _hoisted_28 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_29 = { class: "analyze-section" };
const _hoisted_30 = ["disabled"];
const _hoisted_31 = {
  key: 0,
  class: "analyzing-spinner"
};
const _hoisted_32 = {
  key: 1,
  class: "analyze-icon"
};
const _hoisted_33 = {
  key: 0,
  class: "validation-summary"
};
const _hoisted_34 = {
  key: 1,
  class: "input-area-bottom"
};
const _hoisted_35 = {
  key: 0,
  class: "text-input"
};
const _hoisted_36 = ["disabled"];
const _hoisted_37 = { class: "input-footer" };
const _hoisted_38 = {
  key: 0,
  class: "min-length-hint"
};
const _hoisted_39 = {
  key: 0,
  class: "validation-errors"
};
const _hoisted_40 = {
  key: 1,
  class: "quick-citation-input-area"
};
const _hoisted_41 = ["disabled"];
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
            _cache[12] || (_cache[12] = createBaseVNode("label", null, "Upload a document", -1)),
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
                createBaseVNode("div", { class: "upload-icon" }, "📁", -1),
                createBaseVNode("p", null, "Click to browse or drag & drop", -1),
                createBaseVNode("p", { class: "file-types" }, "Supports: PDF, DOC, DOCX, TXT (max 50MB)", -1)
              ]))) : (openBlock(), createElementBlock("div", _hoisted_13$1, [
                _cache[10] || (_cache[10] = createBaseVNode("div", { class: "file-icon" }, "📄", -1)),
                createBaseVNode("div", _hoisted_14$1, [
                  createBaseVNode("strong", null, toDisplayString(file.value.name), 1),
                  createBaseVNode("span", null, toDisplayString(formatFileSize(file.value.size)), 1)
                ]),
                !__props.isAnalyzing ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  onClick: withModifiers(clearFile, ["stop"]),
                  class: "clear-file-btn"
                }, " ✕ ")) : createCommentVNode("", true)
              ]))
            ], 34),
            hasErrors.value && isDirty.value.file ? (openBlock(), createElementBlock("div", _hoisted_15$1, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[11] || (_cache[11] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : inputMode.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_16$1, [
            _cache[14] || (_cache[14] = createBaseVNode("label", null, "Enter URL to analyze", -1)),
            withDirectives(createBaseVNode("input", {
              "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => url.value = $event),
              type: "url",
              placeholder: "https://example.com/document.pdf",
              disabled: __props.isAnalyzing,
              onInput: handleInputChange,
              class: normalizeClass({ "error": hasErrors.value && isDirty.value.url })
            }, null, 42, _hoisted_17$1), [
              [vModelText, url.value]
            ]),
            createBaseVNode("div", _hoisted_18$1, [
              url.value && !hasErrors.value ? (openBlock(), createElementBlock("span", _hoisted_19$1, "Will analyze: " + toDisplayString(url.value), 1)) : url.value && hasErrors.value ? (openBlock(), createElementBlock("span", _hoisted_20$1, "Invalid URL format")) : createCommentVNode("", true)
            ]),
            hasErrors.value && isDirty.value.url ? (openBlock(), createElementBlock("div", _hoisted_21$1, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[13] || (_cache[13] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : createCommentVNode("", true)
        ])) : createCommentVNode("", true),
        createBaseVNode("div", _hoisted_22$1, [
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "quick", disabled: __props.isAnalyzing }]),
            onClick: _cache[5] || (_cache[5] = ($event) => !__props.isAnalyzing && (inputMode.value = "quick", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_23$1, toDisplayString(methodIcons.quick), 1),
            createBaseVNode("div", _hoisted_24$1, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.quick), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.quick), 1)
            ]),
            inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_25, "✓")) : createCommentVNode("", true)
          ], 2),
          createBaseVNode("div", {
            class: normalizeClass(["input-method-card", { active: inputMode.value === "text", disabled: __props.isAnalyzing }]),
            onClick: _cache[6] || (_cache[6] = ($event) => !__props.isAnalyzing && (inputMode.value = "text", onModeChange()))
          }, [
            createBaseVNode("div", _hoisted_26, toDisplayString(methodIcons.text), 1),
            createBaseVNode("div", _hoisted_27, [
              createBaseVNode("h4", null, toDisplayString(modeLabels.text), 1),
              createBaseVNode("p", null, toDisplayString(modeDescriptions.text), 1)
            ]),
            inputMode.value === "text" ? (openBlock(), createElementBlock("div", _hoisted_28, "✓")) : createCommentVNode("", true)
          ], 2)
        ]),
        createBaseVNode("div", _hoisted_29, [
          createBaseVNode("button", {
            class: normalizeClass(["analyze-btn", { disabled: !canAnalyze.value || __props.isAnalyzing }]),
            disabled: !canAnalyze.value || __props.isAnalyzing,
            onClick: emitAnalyze
          }, [
            __props.isAnalyzing ? (openBlock(), createElementBlock("span", _hoisted_31)) : (openBlock(), createElementBlock("span", _hoisted_32, "🔍")),
            createTextVNode(" " + toDisplayString(__props.isAnalyzing ? "Analyzing..." : "Analyze Content"), 1)
          ], 10, _hoisted_30),
          showValidationWarning.value && hasErrors.value ? (openBlock(), createElementBlock("div", _hoisted_33, _cache[15] || (_cache[15] = [
            createBaseVNode("p", null, "Please fix the errors above before analyzing", -1)
          ]))) : createCommentVNode("", true)
        ]),
        inputMode.value === "text" || inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_34, [
          inputMode.value === "text" ? (openBlock(), createElementBlock("div", _hoisted_35, [
            _cache[17] || (_cache[17] = createBaseVNode("label", null, "Paste your text here", -1)),
            withDirectives(createBaseVNode("textarea", {
              "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => text.value = $event),
              placeholder: "Paste legal text, citations, or document content here...",
              disabled: __props.isAnalyzing,
              rows: "6",
              onInput: handleInputChange,
              class: normalizeClass({ "error": hasErrors.value && isDirty.value.text })
            }, null, 42, _hoisted_36), [
              [vModelText, text.value]
            ]),
            createBaseVNode("div", _hoisted_37, [
              createBaseVNode("span", {
                class: normalizeClass(["char-count", { "error": text.value.length > VALIDATION_RULES.text.maxLength }])
              }, toDisplayString(text.value.length) + " / " + toDisplayString(VALIDATION_RULES.text.maxLength) + " characters ", 3),
              text.value.length < VALIDATION_RULES.text.minLength && isDirty.value.text ? (openBlock(), createElementBlock("span", _hoisted_38, " Minimum " + toDisplayString(VALIDATION_RULES.text.minLength) + " characters required ", 1)) : createCommentVNode("", true)
            ]),
            hasErrors.value && isDirty.value.text ? (openBlock(), createElementBlock("div", _hoisted_39, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(currentErrors.value, (error) => {
                return openBlock(), createElementBlock("div", {
                  key: error,
                  class: "error-message"
                }, [
                  _cache[16] || (_cache[16] = createBaseVNode("span", { class: "error-icon" }, "⚠️", -1)),
                  createTextVNode(" " + toDisplayString(error), 1)
                ]);
              }), 128))
            ])) : createCommentVNode("", true)
          ])) : inputMode.value === "quick" ? (openBlock(), createElementBlock("div", _hoisted_40, [
            _cache[18] || (_cache[18] = createBaseVNode("label", null, "Enter a single citation", -1)),
            withDirectives(createBaseVNode("input", {
              "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => quickCitation.value = $event),
              type: "text",
              placeholder: "Enter citation...",
              disabled: __props.isAnalyzing,
              onKeyup: withKeys(emitAnalyze, ["enter"]),
              class: "quick-citation-input"
            }, null, 40, _hoisted_41), [
              [vModelText, quickCitation.value]
            ])
          ])) : createCommentVNode("", true)
        ])) : createCommentVNode("", true)
      ]);
    };
  }
};
const UnifiedInput = /* @__PURE__ */ _export_sfc(_sfc_main$3, [["__scopeId", "data-v-5acecf32"]]);
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
    SkeletonLoader
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
    const showTimer = computed(() => {
      return citationInfo.value && citationInfo.value.total >= 35;
    });
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
    function normalizeCitations(citations) {
      console.log("Normalizing citations:", citations);
      return (citations || []).map((citation) => {
        let citationText = citation.citation;
        if (Array.isArray(citationText)) {
          citationText = citationText.join("; ");
        }
        let verified = false;
        if (typeof citation.verified === "string") {
          verified = citation.verified === "true" || citation.verified === "true_by_parallel";
        } else {
          verified = !!citation.verified;
        }
        let score = 0;
        if (citation.case_name && citation.case_name !== "N/A") {
          score += 2;
        }
        if (citation.extracted_case_name && citation.extracted_case_name !== "N/A" && citation.case_name && citation.case_name !== "N/A") {
          const canonicalWords = citation.case_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
          const extractedWords = citation.extracted_case_name.toLowerCase().split(/\s+/).filter((w) => w.length > 2);
          const commonWords = canonicalWords.filter((word) => extractedWords.includes(word));
          const similarity = commonWords.length / Math.max(canonicalWords.length, extractedWords.length);
          if (similarity >= 0.5) {
            score += 1;
          }
        }
        if (citation.extracted_date && citation.canonical_date) {
          const extractedYear = citation.extracted_date.toString().substring(0, 4);
          const canonicalYear = citation.canonical_date.toString().substring(0, 4);
          if (extractedYear === canonicalYear && extractedYear.length === 4) {
            score += 1;
          }
        }
        let scoreColor = "red";
        if (score === 4) scoreColor = "green";
        else if (score === 3) scoreColor = "green";
        else if (score === 2) scoreColor = "yellow";
        else if (score === 1) scoreColor = "orange";
        const normalizedCitation = {
          ...citation,
          citation: citationText,
          verified,
          valid: verified,
          score,
          scoreColor,
          case_name: citation.case_name || "N/A",
          extracted_case_name: citation.extracted_case_name || "N/A",
          hinted_case_name: citation.hinted_case_name || "N/A",
          canonical_date: citation.canonical_date || null,
          extracted_date: citation.extracted_date || null,
          metadata: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          },
          details: {
            case_name: citation.case_name,
            canonical_date: citation.canonical_date,
            court: citation.court,
            confidence: citation.confidence,
            method: citation.method,
            pattern: citation.pattern
          }
        };
        console.log("Normalized citation:", {
          citation: normalizedCitation.citation,
          case_name: normalizedCitation.case_name,
          extracted_case_name: normalizedCitation.extracted_case_name,
          verified: normalizedCitation.verified,
          score: normalizedCitation.score
        });
        return normalizedCitation;
      });
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
        const rawCitations = Array.isArray(responseData.validation_results) && responseData.validation_results.length > 0 ? responseData.validation_results : responseData.citations || [];
        results.value = {
          ...responseData,
          citations: normalizeCitations(rawCitations),
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        };
        isLoading2.value = false;
        error.value = null;
        hasActiveRequest.value = false;
        activeRequestId.value = null;
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
      isLoading2.value = true;
      error.value = null;
      results.value = null;
      try {
        const response = await api.post("/analyze", {
          text,
          type: "text"
        }, {
          timeout: 3e5
          // 5 minutes for text processing
        });
        if (response.data.status === "processing" && response.data.task_id) {
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2e3);
          }
        } else {
          handleResults(response.data);
          isLoading2.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };
    const handleFileAnalyze = async (input) => {
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
        const response = await api.post("/analyze", formData, {
          headers: {
            "Content-Type": "multipart/form-data"
          },
          timeout: 3e5
          // 5 minutes for file processing
        });
        if (response.data.status === "processing" && response.data.task_id) {
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2e3);
          }
        } else {
          handleResults(response.data);
          isLoading2.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };
    const handleUrlAnalyze = async ({ url }) => {
      isLoading2.value = true;
      error.value = null;
      results.value = null;
      try {
        const response = await api.post("/analyze", {
          url,
          type: "url"
        }, {
          timeout: 3e5
          // 5 minutes for URL processing
        });
        if (response.data.status === "processing" && response.data.task_id) {
          hasActiveRequest.value = true;
          activeRequestId.value = response.data.task_id;
          if (!pollInterval.value) {
            pollInterval.value = setInterval(() => pollTaskStatus(response.data.task_id), 2e3);
          }
        } else {
          handleResults(response.data);
          isLoading2.value = false;
        }
      } catch (err) {
        handleError(err);
      }
    };
    function handleUnifiedAnalyze(payload) {
      console.log("handleUnifiedAnalyze payload:", payload);
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
        console.log("Found results in router state:", router.currentRoute.value.state.results);
        const responseData = router.currentRoute.value.state.results;
        if (responseData.citations && responseData.citations.length > 0) {
          results.value = {
            citations: normalizeCitations(responseData.citations),
            metadata: responseData.metadata || {},
            total_citations: responseData.citations.length,
            verified_count: responseData.citations.filter((c) => {
              var _a, _b;
              return c.verified || c.valid || ((_a = c.data) == null ? void 0 : _a.valid) || ((_b = c.data) == null ? void 0 : _b.found);
            }).length,
            unverified_count: responseData.citations.filter((c) => {
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
          input = JSON.parse(localStorage.getItem("lastCitationInput"));
        } catch (e) {
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
          error.value = "File upload not available from history. Please upload the file again.";
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
      progressBarClass
    };
  }
};
const _hoisted_1 = { class: "enhanced-validator" };
const _hoisted_2 = { class: "header text-center mb-4" };
const _hoisted_3 = { class: "main-content" };
const _hoisted_4 = {
  key: 0,
  class: "progress-container"
};
const _hoisted_5 = {
  key: 1,
  class: "processing-section mb-4"
};
const _hoisted_6 = {
  key: 2,
  class: "processing-section mb-4"
};
const _hoisted_7 = { class: "card processing-card" };
const _hoisted_8 = { class: "card-body text-center" };
const _hoisted_9 = { class: "processing-content" };
const _hoisted_10 = { class: "progress-info mb-3" };
const _hoisted_11 = { class: "progress-stats" };
const _hoisted_12 = { class: "stat" };
const _hoisted_13 = { class: "stat" };
const _hoisted_14 = { class: "progress-container" };
const _hoisted_15 = {
  class: "progress",
  style: { "height": "1.5rem", "border-radius": "0.75rem" }
};
const _hoisted_16 = ["aria-valuenow"];
const _hoisted_17 = { class: "progress-text" };
const _hoisted_18 = { class: "progress-label mt-2" };
const _hoisted_19 = { class: "text-muted" };
const _hoisted_20 = { class: "processing-steps mt-4" };
const _hoisted_21 = {
  key: 3,
  class: "results-container"
};
const _hoisted_22 = {
  key: 4,
  class: "error-container"
};
const _hoisted_23 = { class: "error-card" };
const _hoisted_24 = {
  key: 5,
  class: "no-results-state text-center mt-5"
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_Toast = resolveComponent("Toast");
  const _component_SkeletonLoader = resolveComponent("SkeletonLoader");
  const _component_CitationResults = resolveComponent("CitationResults");
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
    createBaseVNode("div", _hoisted_3, [
      $setup.showLoading && !$setup.results ? (openBlock(), createElementBlock("div", _hoisted_4, [
        createVNode(_component_SkeletonLoader, {
          lines: 4,
          height: "6em"
        })
      ])) : createCommentVNode("", true),
      $setup.showLoading && !$setup.showTimer ? (openBlock(), createElementBlock("div", _hoisted_5, _cache[3] || (_cache[3] = [
        createBaseVNode("div", { class: "card processing-card" }, [
          createBaseVNode("div", { class: "card-body text-center" }, [
            createBaseVNode("div", { class: "processing-header" }, [
              createBaseVNode("div", { class: "spinner-container" }, [
                createBaseVNode("div", {
                  class: "spinner-border text-primary",
                  role: "status"
                }, [
                  createBaseVNode("span", { class: "visually-hidden" }, "Processing...")
                ])
              ]),
              createBaseVNode("h5", { class: "card-title mt-3" }, [
                createBaseVNode("i", { class: "fas fa-cog fa-spin me-2 text-primary" }),
                createBaseVNode("i", {
                  class: "bi bi-gear-fill spinning me-2 text-primary",
                  style: { "display": "none" }
                }),
                createTextVNode(" Processing Citations ")
              ])
            ]),
            createBaseVNode("div", { class: "processing-content" }, [
              createBaseVNode("p", { class: "text-muted mb-3" }, "Extracting and analyzing citations from your document..."),
              createBaseVNode("div", { class: "progress-dots" }, [
                createBaseVNode("span", { class: "dot" }),
                createBaseVNode("span", { class: "dot" }),
                createBaseVNode("span", { class: "dot" })
              ]),
              createBaseVNode("div", { class: "processing-steps mt-4" }, [
                createBaseVNode("div", { class: "step active" }, [
                  createBaseVNode("i", { class: "bi bi-file-earmark-text text-primary" }),
                  createBaseVNode("span", null, "Document Analysis")
                ]),
                createBaseVNode("div", { class: "step" }, [
                  createBaseVNode("i", { class: "bi bi-search text-muted" }),
                  createBaseVNode("span", null, "Citation Extraction")
                ]),
                createBaseVNode("div", { class: "step" }, [
                  createBaseVNode("i", { class: "bi bi-check-circle text-muted" }),
                  createBaseVNode("span", null, "Verification")
                ])
              ])
            ])
          ])
        ], -1)
      ]))) : createCommentVNode("", true),
      $setup.showLoading && $setup.showTimer ? (openBlock(), createElementBlock("div", _hoisted_6, [
        createBaseVNode("div", _hoisted_7, [
          createBaseVNode("div", _hoisted_8, [
            _cache[9] || (_cache[9] = createBaseVNode("div", { class: "processing-header" }, [
              createBaseVNode("div", { class: "spinner-container" }, [
                createBaseVNode("div", {
                  class: "spinner-border text-primary",
                  role: "status"
                }, [
                  createBaseVNode("span", { class: "visually-hidden" }, "Processing...")
                ])
              ]),
              createBaseVNode("h5", { class: "card-title mt-3" }, [
                createBaseVNode("i", { class: "fas fa-cog fa-spin me-2 text-primary" }),
                createBaseVNode("i", {
                  class: "bi bi-gear-fill spinning me-2 text-primary",
                  style: { "display": "none" }
                }),
                createTextVNode(" Processing Citations ")
              ])
            ], -1)),
            createBaseVNode("div", _hoisted_9, [
              createBaseVNode("div", _hoisted_10, [
                createBaseVNode("div", _hoisted_11, [
                  createBaseVNode("span", _hoisted_12, [
                    _cache[4] || (_cache[4] = createBaseVNode("i", { class: "bi bi-list-ol text-primary" }, null, -1)),
                    createTextVNode(" " + toDisplayString($setup.progressCurrent) + " of " + toDisplayString($setup.progressTotal) + " citations ", 1)
                  ]),
                  createBaseVNode("span", _hoisted_13, [
                    _cache[5] || (_cache[5] = createBaseVNode("i", { class: "bi bi-clock text-primary" }, null, -1)),
                    createTextVNode(" " + toDisplayString($setup.formatTime($setup.elapsedTime)) + " elapsed ", 1)
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_14, [
                createBaseVNode("div", _hoisted_15, [
                  createBaseVNode("div", {
                    class: normalizeClass(["progress-bar progress-bar-striped progress-bar-animated", $setup.progressBarClass]),
                    role: "progressbar",
                    style: normalizeStyle({ width: $setup.progressPercent + "%" }),
                    "aria-valuenow": $setup.progressPercent,
                    "aria-valuemin": "0",
                    "aria-valuemax": "100"
                  }, [
                    createBaseVNode("span", _hoisted_17, toDisplayString($setup.progressPercent) + "%", 1)
                  ], 14, _hoisted_16)
                ]),
                createBaseVNode("div", _hoisted_18, [
                  createBaseVNode("small", _hoisted_19, toDisplayString($setup.progressPercent === 100 ? "Finalizing results..." : "Processing citations..."), 1)
                ])
              ]),
              createBaseVNode("div", _hoisted_20, [
                createBaseVNode("div", {
                  class: normalizeClass(["step", { active: $setup.progressPercent < 33 }])
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(["bi bi-file-earmark-text", $setup.progressPercent < 33 ? "text-primary" : "text-success"])
                  }, null, 2),
                  _cache[6] || (_cache[6] = createBaseVNode("span", null, "Document Analysis", -1))
                ], 2),
                createBaseVNode("div", {
                  class: normalizeClass(["step", { active: $setup.progressPercent >= 33 && $setup.progressPercent < 66 }])
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(["bi bi-search", $setup.progressPercent >= 33 && $setup.progressPercent < 66 ? "text-primary" : $setup.progressPercent >= 66 ? "text-success" : "text-muted"])
                  }, null, 2),
                  _cache[7] || (_cache[7] = createBaseVNode("span", null, "Citation Extraction", -1))
                ], 2),
                createBaseVNode("div", {
                  class: normalizeClass(["step", { active: $setup.progressPercent >= 66 }])
                }, [
                  createBaseVNode("i", {
                    class: normalizeClass(["bi bi-check-circle", $setup.progressPercent >= 66 ? "text-primary" : "text-muted"])
                  }, null, 2),
                  _cache[8] || (_cache[8] = createBaseVNode("span", null, "Verification", -1))
                ], 2)
              ])
            ])
          ])
        ])
      ])) : createCommentVNode("", true),
      $setup.results && !$setup.showLoading ? (openBlock(), createElementBlock("div", _hoisted_21, [
        createVNode(_component_CitationResults, {
          results: $setup.results,
          onApplyCorrection: $setup.applyCorrection,
          onCopyResults: $setup.copyResults,
          onDownloadResults: $setup.downloadResults,
          onToast: _ctx.showToast
        }, null, 8, ["results", "onApplyCorrection", "onCopyResults", "onDownloadResults", "onToast"])
      ])) : createCommentVNode("", true),
      $setup.error && !$setup.showLoading ? (openBlock(), createElementBlock("div", _hoisted_22, [
        createBaseVNode("div", _hoisted_23, [
          _cache[10] || (_cache[10] = createBaseVNode("i", { class: "error-icon" }, "❌", -1)),
          _cache[11] || (_cache[11] = createBaseVNode("h3", null, "Analysis Failed", -1)),
          createBaseVNode("p", null, toDisplayString($setup.error), 1)
        ])
      ])) : createCommentVNode("", true),
      !$setup.results && !$setup.showLoading && !$setup.error ? (openBlock(), createElementBlock("div", _hoisted_24, _cache[12] || (_cache[12] = [
        createBaseVNode("p", { class: "lead" }, [
          createTextVNode("No results to display."),
          createBaseVNode("br"),
          createTextVNode("Please return to the home page to start a new analysis.")
        ], -1)
      ]))) : createCommentVNode("", true)
    ])
  ]);
}
const EnhancedValidator = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-f8d32417"]]);
export {
  EnhancedValidator as default
};
//# sourceMappingURL=EnhancedValidator-CyJNsU7d.js.map
