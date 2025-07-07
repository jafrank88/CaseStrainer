import { r as ref, s as onMounted, p as computed, c as createElementBlock, o as openBlock, b as createBaseVNode, l as createCommentVNode, u as normalizeClass, g as createTextVNode, v as withDirectives, x as vModelText, y as withModifiers, t as toDisplayString, F as Fragment, n as renderList, z as useRouter } from "./vendor-DU8YFPOn.js";
import { a as analyze } from "./api-Ta3xA295.js";
import { _ as _export_sfc } from "./index-Ceo-VWYs.js";
const _hoisted_1 = { class: "home" };
const _hoisted_2 = { class: "container" };
const _hoisted_3 = { class: "modern-card shadow-sm mt-5" };
const _hoisted_4 = { class: "card-body p-5" };
const _hoisted_5 = { class: "mb-5" };
const _hoisted_6 = {
  class: "btn-group w-100 modern-tab-group",
  role: "group"
};
const _hoisted_7 = ["disabled"];
const _hoisted_8 = ["disabled"];
const _hoisted_9 = ["disabled"];
const _hoisted_10 = { class: "modern-tab-content" };
const _hoisted_11 = {
  key: 0,
  class: "my-tab-pane"
};
const _hoisted_12 = { class: "form-group mb-4" };
const _hoisted_13 = ["disabled"];
const _hoisted_14 = {
  key: 1,
  class: "my-tab-pane"
};
const _hoisted_15 = { class: "form-group mb-4" };
const _hoisted_16 = ["disabled"];
const _hoisted_17 = {
  key: 0,
  class: "drop-zone-content"
};
const _hoisted_18 = {
  key: 1,
  class: "file-info"
};
const _hoisted_19 = { class: "file-details" };
const _hoisted_20 = { class: "text-muted" };
const _hoisted_21 = {
  key: 0,
  class: "text-danger mt-2"
};
const _hoisted_22 = {
  key: 2,
  class: "my-tab-pane"
};
const _hoisted_23 = { class: "form-group mb-4" };
const _hoisted_24 = ["disabled"];
const _hoisted_25 = {
  key: 0,
  class: "invalid-feedback"
};
const _hoisted_26 = {
  key: 1,
  class: "form-text mt-1"
};
const _hoisted_27 = {
  key: 0,
  class: "mb-4"
};
const _hoisted_28 = { class: "recent-inputs" };
const _hoisted_29 = ["onClick"];
const _hoisted_30 = { class: "recent-input-content" };
const _hoisted_31 = { class: "recent-input-title" };
const _hoisted_32 = { class: "recent-input-preview" };
const _hoisted_33 = ["onClick"];
const _hoisted_34 = { class: "mt-5" };
const _hoisted_35 = ["disabled"];
const _hoisted_36 = {
  key: 0,
  class: "spinner-border spinner-border-sm me-2",
  role: "status"
};
const _hoisted_37 = {
  key: 1,
  class: "bi bi-search me-2"
};
const _sfc_main = {
  __name: "HomeView",
  setup(__props) {
    const router = useRouter();
    const activeTab = ref("paste");
    const textContent = ref("");
    const urlContent = ref("");
    const selectedFile = ref(null);
    const isAnalyzing = ref(false);
    const isDragOver = ref(false);
    const fileError = ref("");
    const urlError = ref("");
    const recentInputs = ref([]);
    onMounted(() => {
      const saved = localStorage.getItem("recentCitationInputs");
      if (saved) {
        try {
          recentInputs.value = JSON.parse(saved).slice(0, 5);
        } catch (e) {
          console.error("Error loading recent inputs:", e);
        }
      }
    });
    const wordCount = computed(() => {
      if (!textContent.value) return 0;
      return textContent.value.trim().split(/\s+/).length;
    });
    const estimatedCitations = computed(() => {
      if (!textContent.value) return 0;
      const citationPatterns = [
        /\d+\s+[Uu]\.?[Ss]\.?\s+\d+/g,
        /\d+\s+[Ff]\.?\d*\s+\d+/g,
        /\d+\s+[Ss]\.?\s+\d+/g,
        /\d+\s+[Aa]pp\.?\s+\d+/g
      ];
      let count = 0;
      citationPatterns.forEach((pattern) => {
        const matches = textContent.value.match(pattern);
        if (matches) count += matches.length;
      });
      return Math.max(count, Math.floor(wordCount.value / 100));
    });
    const yearCount = computed(() => {
      if (!textContent.value) return 0;
      const yearMatches = textContent.value.match(/\b(19|20)\d{2}\b/g);
      return yearMatches ? new Set(yearMatches).size : 0;
    });
    const qualityScore = computed(() => {
      if (!textContent.value) return 0;
      let score = 0;
      const lengthScore = Math.min(30, textContent.value.length / 1e3 * 10);
      score += lengthScore;
      const wordScore = Math.min(25, wordCount.value / 50 * 5);
      score += wordScore;
      const citationDensity = estimatedCitations.value / Math.max(1, wordCount.value / 100);
      const citationScore = Math.min(25, citationDensity * 10);
      score += citationScore;
      const yearScore = Math.min(20, yearCount.value * 4);
      score += yearScore;
      return Math.round(score);
    });
    computed(() => {
      if (qualityScore.value >= 80) return "excellent";
      if (qualityScore.value >= 60) return "good";
      if (qualityScore.value >= 40) return "fair";
      return "poor";
    });
    const canAnalyze = computed(() => {
      switch (activeTab.value) {
        case "paste":
          return textContent.value.trim().length >= 10;
        case "file":
          return selectedFile.value !== null;
        case "url":
          return urlContent.value.trim() !== "" && !urlError.value;
        default:
          return false;
      }
    });
    const validateInput = () => {
      fileError.value = "";
      urlError.value = "";
      if (activeTab.value === "url" && urlContent.value.trim()) {
        try {
          new URL(urlContent.value);
        } catch {
          urlError.value = "Please enter a valid URL";
        }
      }
      if (activeTab.value === "paste" && textContent.value.length > 5e4) ;
    };
    const loadRecentInput = (input) => {
      activeTab.value = input.tab;
      switch (input.tab) {
        case "paste":
          textContent.value = input.text || "";
          break;
        case "url":
          urlContent.value = input.url || "";
          break;
      }
      validateInput();
    };
    const removeRecentInput = (index) => {
      recentInputs.value.splice(index, 1);
      saveRecentInputs();
    };
    const saveRecentInputs = () => {
      localStorage.setItem("recentCitationInputs", JSON.stringify(recentInputs.value));
    };
    const addToRecentInputs = (inputData) => {
      recentInputs.value = recentInputs.value.filter(
        (input) => !(input.tab === inputData.tab && (input.tab === "paste" && input.text === inputData.text || input.tab === "url" && input.url === inputData.url || input.tab === "file" && input.fileName === inputData.fileName))
      );
      recentInputs.value.unshift(inputData);
      recentInputs.value = recentInputs.value.slice(0, 5);
      saveRecentInputs();
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
          return `File: ${input.fileName}`;
        case "url":
          return "URL Input";
        default:
          return "Unknown Input";
      }
    };
    const getInputPreview = (input) => {
      switch (input.tab) {
        case "paste":
          return input.text ? input.text.substring(0, 60) + (input.text.length > 60 ? "..." : "") : "";
        case "file":
          return input.fileName || "Unknown file";
        case "url":
          return input.url || "";
        default:
          return "";
      }
    };
    const onFileChange = (event) => {
      const file = event.target.files[0];
      if (file) {
        handleFile(file);
      }
    };
    const onFileDrop = (event) => {
      event.preventDefault();
      isDragOver.value = false;
      const file = event.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    };
    const handleFile = (file) => {
      fileError.value = "";
      const allowedTypes = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
      if (!allowedTypes.includes(file.type)) {
        fileError.value = "Please select a valid file type (PDF, DOC, DOCX, or TXT)";
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        fileError.value = "File size must be less than 50MB";
        return;
      }
      selectedFile.value = file;
    };
    const triggerFileInput = () => {
      if (!isAnalyzing.value) {
        const fileInputElement = document.getElementById("fileInput");
        if (fileInputElement) {
          fileInputElement.click();
        }
      }
    };
    const clearFile = () => {
      selectedFile.value = null;
      fileError.value = "";
      if (document.getElementById("fileInput")) {
        document.getElementById("fileInput").value = "";
      }
    };
    const formatFileSize = (bytes) => {
      if (bytes === 0) return "0 Bytes";
      const k = 1024;
      const sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    };
    const analyzeContent = async () => {
      var _a, _b;
      if (!canAnalyze.value || isAnalyzing.value) return;
      isAnalyzing.value = true;
      try {
        const inputData = {
          tab: activeTab.value,
          text: textContent.value,
          url: urlContent.value,
          fileName: selectedFile.value ? selectedFile.value.name : null,
          timestamp: (/* @__PURE__ */ new Date()).toISOString()
        };
        addToRecentInputs(inputData);
        localStorage.setItem("lastCitationInput", JSON.stringify(inputData));
        let response;
        switch (activeTab.value) {
          case "paste":
            if (textContent.value.trim()) {
              response = await analyze({
                text: textContent.value.trim(),
                type: "text"
              });
            }
            break;
          case "url":
            if (urlContent.value.trim()) {
              response = await analyze({
                url: urlContent.value.trim(),
                type: "url"
              });
            }
            break;
          case "file":
            if (selectedFile.value) {
              const formData = new FormData();
              formData.append("file", selectedFile.value);
              formData.append("type", "file");
              response = await analyze(formData);
            }
            break;
        }
        if (response) {
          router.push({
            path: "/enhanced-validator",
            query: {
              tab: activeTab.value,
              ...activeTab.value === "paste" && textContent.value.trim() ? { text: textContent.value.trim() } : {},
              ...activeTab.value === "url" && urlContent.value.trim() ? { url: urlContent.value.trim() } : {}
            },
            state: {
              results: response
            }
          });
        }
      } catch (error) {
        console.error("Analysis error:", error);
        let errorMessage = "An error occurred during analysis. Please try again.";
        if (error.response) {
          switch (error.response.status) {
            case 400:
              errorMessage = ((_a = error.response.data) == null ? void 0 : _a.message) || "Invalid input. Please check your data and try again.";
              break;
            case 413:
              errorMessage = "File too large. Please use a smaller file.";
              break;
            case 429:
              errorMessage = "Too many requests. Please wait a moment and try again.";
              break;
            case 500:
              errorMessage = "Server error. Please try again later.";
              break;
            default:
              errorMessage = ((_b = error.response.data) == null ? void 0 : _b.message) || `Server error (${error.response.status}). Please try again.`;
          }
        } else if (error.code === "ECONNABORTED") {
          errorMessage = "Request timed out. Please try again.";
        } else if (error.code === "NETWORK_ERROR") {
          errorMessage = "Network error. Please check your connection and try again.";
        }
        alert(errorMessage);
      } finally {
        isAnalyzing.value = false;
      }
    };
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("div", _hoisted_4, [
              _cache[19] || (_cache[19] = createBaseVNode("h2", { class: "mb-5 text-center modern-title" }, "Citation Verifier", -1)),
              createBaseVNode("div", _hoisted_5, [
                createBaseVNode("div", _hoisted_6, [
                  createBaseVNode("button", {
                    type: "button",
                    class: normalizeClass(["btn modern-tab-btn", activeTab.value === "paste" ? "active" : ""]),
                    onClick: _cache[0] || (_cache[0] = ($event) => activeTab.value = "paste"),
                    disabled: isAnalyzing.value
                  }, _cache[7] || (_cache[7] = [
                    createBaseVNode("i", { class: "bi bi-clipboard-text me-2" }, null, -1),
                    createTextVNode(" Paste Text ")
                  ]), 10, _hoisted_7),
                  createBaseVNode("button", {
                    type: "button",
                    class: normalizeClass(["btn modern-tab-btn", activeTab.value === "file" ? "active" : ""]),
                    onClick: _cache[1] || (_cache[1] = ($event) => activeTab.value = "file"),
                    disabled: isAnalyzing.value
                  }, _cache[8] || (_cache[8] = [
                    createBaseVNode("i", { class: "bi bi-upload me-2" }, null, -1),
                    createTextVNode(" File Upload ")
                  ]), 10, _hoisted_8),
                  createBaseVNode("button", {
                    type: "button",
                    class: normalizeClass(["btn modern-tab-btn", activeTab.value === "url" ? "active" : ""]),
                    onClick: _cache[2] || (_cache[2] = ($event) => activeTab.value = "url"),
                    disabled: isAnalyzing.value
                  }, _cache[9] || (_cache[9] = [
                    createBaseVNode("i", { class: "bi bi-link-45deg me-2" }, null, -1),
                    createTextVNode(" URL Upload ")
                  ]), 10, _hoisted_9)
                ])
              ]),
              createBaseVNode("div", _hoisted_10, [
                activeTab.value === "paste" ? (openBlock(), createElementBlock("div", _hoisted_11, [
                  createBaseVNode("div", _hoisted_12, [
                    _cache[10] || (_cache[10] = createBaseVNode("label", {
                      for: "textInput",
                      class: "form-label"
                    }, "Paste your text here", -1)),
                    withDirectives(createBaseVNode("textarea", {
                      id: "textInput",
                      "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => textContent.value = $event),
                      class: "form-control modern-input",
                      rows: "8",
                      placeholder: "Paste legal text, citations, or document content here...",
                      disabled: isAnalyzing.value,
                      onInput: validateInput
                    }, null, 40, _hoisted_13), [
                      [vModelText, textContent.value]
                    ])
                  ])
                ])) : createCommentVNode("", true),
                activeTab.value === "file" ? (openBlock(), createElementBlock("div", _hoisted_14, [
                  createBaseVNode("div", _hoisted_15, [
                    _cache[15] || (_cache[15] = createBaseVNode("label", { class: "form-label" }, "Upload a document", -1)),
                    createBaseVNode("div", {
                      class: normalizeClass(["file-drop-zone modern-drop-zone", {
                        "has-file": selectedFile.value,
                        "dragover": isDragOver.value,
                        "error": fileError.value
                      }]),
                      onDrop: onFileDrop,
                      onDragover: _cache[4] || (_cache[4] = withModifiers(($event) => isDragOver.value = true, ["prevent"])),
                      onDragleave: _cache[5] || (_cache[5] = withModifiers(($event) => isDragOver.value = false, ["prevent"])),
                      onClick: triggerFileInput
                    }, [
                      createBaseVNode("input", {
                        ref: "fileInput",
                        id: "fileInput",
                        type: "file",
                        onChange: onFileChange,
                        disabled: isAnalyzing.value,
                        accept: ".pdf,.doc,.docx,.txt",
                        style: { "display": "none" }
                      }, null, 40, _hoisted_16),
                      !selectedFile.value ? (openBlock(), createElementBlock("div", _hoisted_17, _cache[11] || (_cache[11] = [
                        createBaseVNode("i", { class: "bi bi-cloud-upload fs-1 text-muted mb-3" }, null, -1),
                        createBaseVNode("p", { class: "mb-2" }, "Click to browse or drag & drop", -1),
                        createBaseVNode("p", { class: "text-muted small" }, "Supports: PDF, DOC, DOCX, TXT (max 50MB)", -1)
                      ]))) : (openBlock(), createElementBlock("div", _hoisted_18, [
                        _cache[13] || (_cache[13] = createBaseVNode("i", { class: "bi bi-file-earmark-text fs-3 text-primary me-3" }, null, -1)),
                        createBaseVNode("div", _hoisted_19, [
                          createBaseVNode("strong", null, toDisplayString(selectedFile.value.name), 1),
                          createBaseVNode("span", _hoisted_20, toDisplayString(formatFileSize(selectedFile.value.size)), 1)
                        ]),
                        !isAnalyzing.value ? (openBlock(), createElementBlock("button", {
                          key: 0,
                          onClick: withModifiers(clearFile, ["stop"]),
                          class: "btn btn-sm btn-outline-danger"
                        }, _cache[12] || (_cache[12] = [
                          createBaseVNode("i", { class: "bi bi-x" }, null, -1)
                        ]))) : createCommentVNode("", true)
                      ]))
                    ], 34),
                    fileError.value ? (openBlock(), createElementBlock("div", _hoisted_21, [
                      _cache[14] || (_cache[14] = createBaseVNode("i", { class: "bi bi-exclamation-triangle me-1" }, null, -1)),
                      createTextVNode(" " + toDisplayString(fileError.value), 1)
                    ])) : createCommentVNode("", true)
                  ])
                ])) : createCommentVNode("", true),
                activeTab.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_22, [
                  createBaseVNode("div", _hoisted_23, [
                    _cache[16] || (_cache[16] = createBaseVNode("label", {
                      for: "urlInput",
                      class: "form-label"
                    }, "Enter URL to analyze", -1)),
                    withDirectives(createBaseVNode("input", {
                      id: "urlInput",
                      "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => urlContent.value = $event),
                      type: "url",
                      class: normalizeClass(["form-control modern-input", { "is-invalid": urlError.value }]),
                      placeholder: "https://example.com/document.pdf",
                      disabled: isAnalyzing.value,
                      onInput: validateInput
                    }, null, 42, _hoisted_24), [
                      [vModelText, urlContent.value]
                    ]),
                    urlError.value ? (openBlock(), createElementBlock("div", _hoisted_25, toDisplayString(urlError.value), 1)) : urlContent.value && !urlError.value ? (openBlock(), createElementBlock("div", _hoisted_26, " Will analyze: " + toDisplayString(urlContent.value), 1)) : createCommentVNode("", true)
                  ])
                ])) : createCommentVNode("", true)
              ]),
              recentInputs.value.length > 0 ? (openBlock(), createElementBlock("div", _hoisted_27, [
                _cache[18] || (_cache[18] = createBaseVNode("label", { class: "form-label" }, "Recent Inputs", -1)),
                createBaseVNode("div", _hoisted_28, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(recentInputs.value, (input, index) => {
                    return openBlock(), createElementBlock("div", {
                      key: index,
                      class: "recent-input-item",
                      onClick: ($event) => loadRecentInput(input)
                    }, [
                      createBaseVNode("div", _hoisted_30, [
                        createBaseVNode("div", _hoisted_31, [
                          createBaseVNode("i", {
                            class: normalizeClass([getInputIcon(input.tab), "me-2"])
                          }, null, 2),
                          createTextVNode(" " + toDisplayString(getInputTitle(input)), 1)
                        ]),
                        createBaseVNode("div", _hoisted_32, toDisplayString(getInputPreview(input)), 1)
                      ]),
                      createBaseVNode("button", {
                        onClick: withModifiers(($event) => removeRecentInput(index), ["stop"]),
                        class: "btn btn-sm btn-outline-secondary",
                        title: "Remove from history"
                      }, _cache[17] || (_cache[17] = [
                        createBaseVNode("i", { class: "bi bi-x" }, null, -1)
                      ]), 8, _hoisted_33)
                    ], 8, _hoisted_29);
                  }), 128))
                ])
              ])) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_34, [
                createBaseVNode("button", {
                  class: normalizeClass(["btn", "btn-primary", "btn-lg", "w-100", { "disabled": !canAnalyze.value || isAnalyzing.value }]),
                  disabled: !canAnalyze.value || isAnalyzing.value,
                  onClick: analyzeContent
                }, [
                  isAnalyzing.value ? (openBlock(), createElementBlock("span", _hoisted_36)) : (openBlock(), createElementBlock("i", _hoisted_37)),
                  createTextVNode(" " + toDisplayString(isAnalyzing.value ? "Analyzing..." : "Analyze Content"), 1)
                ], 10, _hoisted_35)
              ])
            ])
          ])
        ])
      ]);
    };
  }
};
const HomeView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-bb810a51"]]);
export {
  HomeView as default
};
//# sourceMappingURL=HomeView-o8aQVgyH.js.map
