import { r as ref, s as onMounted, u as useRoute, p as computed, c as createElementBlock, o as openBlock, b as createBaseVNode, v as createStaticVNode, x as normalizeClass, l as createCommentVNode, y as withDirectives, g as createTextVNode, z as vModelText, t as toDisplayString, A as withModifiers, d as createVNode, B as useRouter } from "./vendor-CDDSDoLJ.js";
import { u as useRecentInputs, R as RecentInputs, a as analyze } from "./RecentInputs-Dx2uh2Yn.js";
import { _ as _export_sfc } from "./index-C6HUIkwi.js";
const _hoisted_1 = { class: "home" };
const _hoisted_2 = { class: "container" };
const _hoisted_3 = { class: "main-content-wrapper" };
const _hoisted_4 = { class: "main-input-area" };
const _hoisted_5 = { class: "input-container" };
const _hoisted_6 = { class: "input-methods" };
const _hoisted_7 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_8 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_9 = {
  key: 0,
  class: "active-indicator"
};
const _hoisted_10 = { class: "input-content-area" };
const _hoisted_11 = {
  key: 0,
  class: "input-tab-content"
};
const _hoisted_12 = { class: "form-group" };
const _hoisted_13 = {
  key: 0,
  class: "input-quality-indicators"
};
const _hoisted_14 = { class: "quality-item" };
const _hoisted_15 = { class: "quality-value" };
const _hoisted_16 = { class: "quality-item" };
const _hoisted_17 = { class: "quality-value" };
const _hoisted_18 = { class: "quality-item" };
const _hoisted_19 = { class: "quality-value" };
const _hoisted_20 = {
  key: 1,
  class: "input-tab-content"
};
const _hoisted_21 = { class: "form-group" };
const _hoisted_22 = {
  key: 0,
  class: "selected-file"
};
const _hoisted_23 = { class: "file-info" };
const _hoisted_24 = { class: "file-name" };
const _hoisted_25 = { class: "file-size" };
const _hoisted_26 = {
  key: 1,
  class: "text-danger mt-2"
};
const _hoisted_27 = {
  key: 2,
  class: "input-tab-content"
};
const _hoisted_28 = { class: "form-group" };
const _hoisted_29 = {
  key: 0,
  class: "text-danger mt-2"
};
const _hoisted_30 = {
  key: 1,
  class: "form-text mt-2"
};
const _hoisted_31 = { class: "analyze-button-container" };
const _hoisted_32 = ["disabled"];
const _hoisted_33 = {
  key: 0,
  class: "spinner-border spinner-border-sm me-2",
  role: "status"
};
const _hoisted_34 = {
  key: 1,
  class: "bi bi-search me-2"
};
const _hoisted_35 = { class: "recent-inputs-sidebar-container" };
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
    const { addRecentInput } = useRecentInputs();
    onMounted(() => {
      const route = useRoute();
      if (route.query.tab) {
        activeTab.value = route.query.tab;
        if (route.query.text) {
          textContent.value = route.query.text;
        }
        if (route.query.url) {
          urlContent.value = route.query.url;
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
        /\d+\s+[Aa]pp\.?\s+\d+/g,
        /\d+\s+[A-Z][a-z]*\.?\s*(?:2d|3d)?\s+\d+/g
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
    const fileInput = ref(null);
    const triggerFileInput = () => {
      if (!isAnalyzing.value && fileInput.value) {
        fileInput.value.click();
      }
    };
    const clearFile = () => {
      selectedFile.value = null;
      fileError.value = "";
      if (fileInput.value) {
        fileInput.value.value = "";
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
        if (activeTab.value !== "file") {
          addRecentInput(inputData);
          localStorage.setItem("lastCitationInput", JSON.stringify(inputData));
        } else {
          addRecentInput(inputData);
        }
        let response;
        if (activeTab.value === "url" && urlContent.value.trim()) {
          router.push({
            path: "/enhanced-validator",
            query: {
              tab: activeTab.value,
              url: urlContent.value.trim()
            }
          });
          return;
        }
        switch (activeTab.value) {
          case "paste":
            if (textContent.value.trim()) {
              response = await analyze({
                text: textContent.value.trim(),
                type: "text"
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
        if (response && response.task_id) {
          router.push({
            name: "EnhancedValidator",
            query: { task_id: response.task_id }
          });
          return;
        }
        if (response) {
          router.push({
            path: "/enhanced-validator",
            query: {
              tab: activeTab.value,
              ...activeTab.value === "paste" && textContent.value.trim() ? { text: textContent.value.trim() } : {}
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
        _cache[29] || (_cache[29] = createBaseVNode("div", { class: "background-pattern" }, null, -1)),
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("div", _hoisted_4, [
              _cache[28] || (_cache[28] = createStaticVNode('<div class="hero-content" data-v-9ee29028><div class="hero-text" data-v-9ee29028><h1 class="hero-title" data-v-9ee29028><i class="bi bi-shield-check me-3" data-v-9ee29028></i> Legal Citation Verification </h1><p class="hero-subtitle" data-v-9ee29028> Upload legal documents, paste text, or provide URLs to automatically extract and verify citations against authoritative legal databases. </p></div><div class="experimental-banner" data-v-9ee29028><i class="bi bi-flask me-2" data-v-9ee29028></i><strong data-v-9ee29028>Experimental Use:</strong> This tool is for research and educational purposes. Always verify results independently. </div></div>', 1)),
              createBaseVNode("div", _hoisted_5, [
                createBaseVNode("div", _hoisted_6, [
                  createBaseVNode("div", {
                    class: normalizeClass(["input-method-card", { active: activeTab.value === "paste" }]),
                    onClick: _cache[0] || (_cache[0] = ($event) => activeTab.value = "paste")
                  }, [
                    _cache[8] || (_cache[8] = createBaseVNode("div", { class: "method-icon" }, [
                      createBaseVNode("i", { class: "bi bi-clipboard-text" })
                    ], -1)),
                    _cache[9] || (_cache[9] = createBaseVNode("div", { class: "method-content" }, [
                      createBaseVNode("h4", null, "Paste Text"),
                      createBaseVNode("p", null, "Copy and paste legal text directly")
                    ], -1)),
                    activeTab.value === "paste" ? (openBlock(), createElementBlock("div", _hoisted_7, _cache[7] || (_cache[7] = [
                      createBaseVNode("i", { class: "bi bi-check" }, null, -1)
                    ]))) : createCommentVNode("", true)
                  ], 2),
                  createBaseVNode("div", {
                    class: normalizeClass(["input-method-card", { active: activeTab.value === "file" }]),
                    onClick: _cache[1] || (_cache[1] = ($event) => activeTab.value = "file")
                  }, [
                    _cache[11] || (_cache[11] = createBaseVNode("div", { class: "method-icon" }, [
                      createBaseVNode("i", { class: "bi bi-file-earmark-text" })
                    ], -1)),
                    _cache[12] || (_cache[12] = createBaseVNode("div", { class: "method-content" }, [
                      createBaseVNode("h4", null, "Upload File"),
                      createBaseVNode("p", null, "Upload PDF, DOC, DOCX, or TXT files")
                    ], -1)),
                    activeTab.value === "file" ? (openBlock(), createElementBlock("div", _hoisted_8, _cache[10] || (_cache[10] = [
                      createBaseVNode("i", { class: "bi bi-check" }, null, -1)
                    ]))) : createCommentVNode("", true)
                  ], 2),
                  createBaseVNode("div", {
                    class: normalizeClass(["input-method-card", { active: activeTab.value === "url" }]),
                    onClick: _cache[2] || (_cache[2] = ($event) => activeTab.value = "url")
                  }, [
                    _cache[14] || (_cache[14] = createBaseVNode("div", { class: "method-icon" }, [
                      createBaseVNode("i", { class: "bi bi-link-45deg" })
                    ], -1)),
                    _cache[15] || (_cache[15] = createBaseVNode("div", { class: "method-content" }, [
                      createBaseVNode("h4", null, "URL Input"),
                      createBaseVNode("p", null, "Provide a URL to analyze online content")
                    ], -1)),
                    activeTab.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_9, _cache[13] || (_cache[13] = [
                      createBaseVNode("i", { class: "bi bi-check" }, null, -1)
                    ]))) : createCommentVNode("", true)
                  ], 2)
                ]),
                createBaseVNode("div", _hoisted_10, [
                  activeTab.value === "paste" ? (openBlock(), createElementBlock("div", _hoisted_11, [
                    createBaseVNode("div", _hoisted_12, [
                      _cache[19] || (_cache[19] = createBaseVNode("label", { class: "form-label" }, [
                        createBaseVNode("i", { class: "bi bi-clipboard-text me-2" }),
                        createTextVNode(" Legal Text Content ")
                      ], -1)),
                      withDirectives(createBaseVNode("textarea", {
                        "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => textContent.value = $event),
                        class: "form-control input-field",
                        rows: "8",
                        placeholder: "Paste your legal text here... (minimum 10 characters)",
                        onInput: validateInput
                      }, null, 544), [
                        [vModelText, textContent.value]
                      ]),
                      textContent.value ? (openBlock(), createElementBlock("div", _hoisted_13, [
                        createBaseVNode("div", _hoisted_14, [
                          _cache[16] || (_cache[16] = createBaseVNode("span", { class: "quality-label" }, "Words:", -1)),
                          createBaseVNode("span", _hoisted_15, toDisplayString(wordCount.value), 1)
                        ]),
                        createBaseVNode("div", _hoisted_16, [
                          _cache[17] || (_cache[17] = createBaseVNode("span", { class: "quality-label" }, "Est. Citations:", -1)),
                          createBaseVNode("span", _hoisted_17, toDisplayString(estimatedCitations.value), 1)
                        ]),
                        createBaseVNode("div", _hoisted_18, [
                          _cache[18] || (_cache[18] = createBaseVNode("span", { class: "quality-label" }, "Years:", -1)),
                          createBaseVNode("span", _hoisted_19, toDisplayString(yearCount.value), 1)
                        ])
                      ])) : createCommentVNode("", true)
                    ])
                  ])) : createCommentVNode("", true),
                  activeTab.value === "file" ? (openBlock(), createElementBlock("div", _hoisted_20, [
                    createBaseVNode("div", _hoisted_21, [
                      _cache[24] || (_cache[24] = createBaseVNode("label", { class: "form-label" }, [
                        createBaseVNode("i", { class: "bi bi-file-earmark-text me-2" }),
                        createTextVNode(" Document File ")
                      ], -1)),
                      createBaseVNode("div", {
                        class: normalizeClass(["file-drop-zone", { "drag-over": isDragOver.value }]),
                        onDrop: onFileDrop,
                        onDragover: _cache[4] || (_cache[4] = withModifiers(($event) => isDragOver.value = true, ["prevent"])),
                        onDragleave: _cache[5] || (_cache[5] = withModifiers(($event) => isDragOver.value = false, ["prevent"])),
                        onClick: triggerFileInput
                      }, [
                        _cache[20] || (_cache[20] = createBaseVNode("div", { class: "file-drop-content" }, [
                          createBaseVNode("i", { class: "bi bi-cloud-upload file-drop-icon" }),
                          createBaseVNode("p", { class: "file-drop-text" }, [
                            createBaseVNode("strong", null, "Click to select"),
                            createTextVNode(" or drag and drop your file here ")
                          ]),
                          createBaseVNode("p", { class: "file-drop-hint" }, " Supported formats: PDF, DOC, DOCX, TXT (max 50MB) ")
                        ], -1)),
                        createBaseVNode("input", {
                          ref_key: "fileInput",
                          ref: fileInput,
                          type: "file",
                          class: "file-input-hidden",
                          accept: ".pdf,.doc,.docx,.txt",
                          onChange: onFileChange
                        }, null, 544)
                      ], 34),
                      selectedFile.value ? (openBlock(), createElementBlock("div", _hoisted_22, [
                        createBaseVNode("div", _hoisted_23, [
                          _cache[21] || (_cache[21] = createBaseVNode("i", { class: "bi bi-file-earmark-text me-2" }, null, -1)),
                          createBaseVNode("span", _hoisted_24, toDisplayString(selectedFile.value.name), 1),
                          createBaseVNode("span", _hoisted_25, "(" + toDisplayString(formatFileSize(selectedFile.value.size)) + ")", 1)
                        ]),
                        createBaseVNode("button", {
                          onClick: clearFile,
                          class: "btn btn-sm btn-outline-danger"
                        }, _cache[22] || (_cache[22] = [
                          createBaseVNode("i", { class: "bi bi-x" }, null, -1)
                        ]))
                      ])) : createCommentVNode("", true),
                      fileError.value ? (openBlock(), createElementBlock("div", _hoisted_26, [
                        _cache[23] || (_cache[23] = createBaseVNode("i", { class: "bi bi-exclamation-triangle me-1" }, null, -1)),
                        createTextVNode(" " + toDisplayString(fileError.value), 1)
                      ])) : createCommentVNode("", true)
                    ])
                  ])) : createCommentVNode("", true),
                  activeTab.value === "url" ? (openBlock(), createElementBlock("div", _hoisted_27, [
                    createBaseVNode("div", _hoisted_28, [
                      _cache[27] || (_cache[27] = createBaseVNode("label", { class: "form-label" }, [
                        createBaseVNode("i", { class: "bi bi-link-45deg me-2" }),
                        createTextVNode(" Document URL ")
                      ], -1)),
                      withDirectives(createBaseVNode("input", {
                        "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => urlContent.value = $event),
                        type: "url",
                        class: "form-control input-field",
                        placeholder: "https://example.com/legal-document",
                        onInput: validateInput
                      }, null, 544), [
                        [vModelText, urlContent.value]
                      ]),
                      urlError.value ? (openBlock(), createElementBlock("div", _hoisted_29, [
                        _cache[25] || (_cache[25] = createBaseVNode("i", { class: "bi bi-exclamation-triangle me-1" }, null, -1)),
                        createTextVNode(" " + toDisplayString(urlError.value), 1)
                      ])) : urlContent.value && !urlError.value ? (openBlock(), createElementBlock("div", _hoisted_30, _cache[26] || (_cache[26] = [
                        createBaseVNode("i", { class: "bi bi-info-circle me-1" }, null, -1),
                        createTextVNode(" We'll fetch and analyze the document from the provided URL ")
                      ]))) : createCommentVNode("", true)
                    ])
                  ])) : createCommentVNode("", true)
                ]),
                createBaseVNode("div", _hoisted_31, [
                  createBaseVNode("button", {
                    class: normalizeClass(["btn", "analyze-btn", { "disabled": !canAnalyze.value || isAnalyzing.value }]),
                    disabled: !canAnalyze.value || isAnalyzing.value,
                    onClick: analyzeContent
                  }, [
                    isAnalyzing.value ? (openBlock(), createElementBlock("span", _hoisted_33)) : (openBlock(), createElementBlock("i", _hoisted_34)),
                    createBaseVNode("span", null, toDisplayString(isAnalyzing.value ? "Analyzing..." : "Analyze Content"), 1)
                  ], 10, _hoisted_32)
                ])
              ])
            ]),
            createBaseVNode("div", _hoisted_35, [
              createVNode(RecentInputs, { onLoadInput: loadRecentInput })
            ])
          ])
        ]),
        _cache[30] || (_cache[30] = createStaticVNode('<div class="container" data-v-9ee29028><div class="features-section" data-v-9ee29028><div class="text-center mb-4" data-v-9ee29028><h2 class="text-white mb-3" data-v-9ee29028>Powerful Citation Analysis Features</h2><p class="text-white opacity-75" data-v-9ee29028>Everything you need for comprehensive legal citation verification</p></div><div class="features-grid" data-v-9ee29028><div class="feature-card" data-v-9ee29028><div class="feature-icon" data-v-9ee29028><i class="bi bi-search" data-v-9ee29028></i></div><h4 class="feature-title" data-v-9ee29028>Smart Detection</h4><p class="feature-description" data-v-9ee29028>Automatically identifies and extracts citations from complex legal documents using advanced pattern recognition.</p></div><div class="feature-card" data-v-9ee29028><div class="feature-icon" data-v-9ee29028><i class="bi bi-shield-check" data-v-9ee29028></i></div><h4 class="feature-title" data-v-9ee29028>Accuracy Verification</h4><p class="feature-description" data-v-9ee29028>Cross-references citations against authoritative legal databases to ensure accuracy and validity.</p></div><div class="feature-card" data-v-9ee29028><div class="feature-icon" data-v-9ee29028><i class="bi bi-lightning" data-v-9ee29028></i></div><h4 class="feature-title" data-v-9ee29028>Instant Analysis</h4><p class="feature-description" data-v-9ee29028>Get comprehensive results in seconds with detailed breakdowns of citation quality and completeness.</p></div><div class="feature-card" data-v-9ee29028><div class="feature-icon" data-v-9ee29028><i class="bi bi-file-earmark-text" data-v-9ee29028></i></div><h4 class="feature-title" data-v-9ee29028>Multiple Formats</h4><p class="feature-description" data-v-9ee29028>Supports PDF, Word documents, plain text, and direct URL analysis for maximum flexibility.</p></div></div></div></div>', 1))
      ]);
    };
  }
};
const HomeView = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-9ee29028"]]);
export {
  HomeView as default
};
//# sourceMappingURL=HomeView-CI4EUgxv.js.map
