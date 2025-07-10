import { c as createElementBlock, o as openBlock, b as createBaseVNode, d as createVNode, w as withCtx, g as createTextVNode, f as resolveComponent, B as useRouter } from "./vendor-CDDSDoLJ.js";
import { _ as _export_sfc } from "./index-C6HUIkwi.js";
const _sfc_main = {
  name: "NotFound",
  setup() {
    const router = useRouter();
    const goBack = () => {
      router.go(-1);
    };
    return {
      goBack
    };
  }
};
const _hoisted_1 = { class: "not-found" };
const _hoisted_2 = { class: "container py-5" };
const _hoisted_3 = { class: "row justify-content-center" };
const _hoisted_4 = { class: "col-lg-8 text-center" };
const _hoisted_5 = { class: "error-404" };
const _hoisted_6 = { class: "d-flex justify-content-center gap-3" };
const _hoisted_7 = { class: "mt-5 pt-5" };
const _hoisted_8 = { class: "d-flex flex-wrap justify-content-center gap-3" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = resolveComponent("router-link");
  return openBlock(), createElementBlock("div", _hoisted_1, [
    createBaseVNode("div", _hoisted_2, [
      createBaseVNode("div", _hoisted_3, [
        createBaseVNode("div", _hoisted_4, [
          createBaseVNode("div", _hoisted_5, [
            _cache[3] || (_cache[3] = createBaseVNode("h1", { class: "display-1 fw-bold text-primary" }, "404", -1)),
            _cache[4] || (_cache[4] = createBaseVNode("h2", { class: "h3 mb-4" }, "Page Not Found", -1)),
            _cache[5] || (_cache[5] = createBaseVNode("p", { class: "lead text-muted mb-5" }, " Oops! The page you are looking for might have been removed, had its name changed, or is temporarily unavailable. ", -1)),
            createBaseVNode("div", _hoisted_6, [
              createVNode(_component_router_link, {
                to: "/",
                class: "btn btn-primary btn-lg"
              }, {
                default: withCtx(() => _cache[1] || (_cache[1] = [
                  createBaseVNode("i", { class: "bi bi-house-door me-2" }, null, -1),
                  createTextVNode(" Back to Home ")
                ])),
                _: 1,
                __: [1]
              }),
              createBaseVNode("a", {
                href: "#",
                class: "btn btn-outline-secondary btn-lg",
                onClick: _cache[0] || (_cache[0] = (...args) => $setup.goBack && $setup.goBack(...args))
              }, _cache[2] || (_cache[2] = [
                createBaseVNode("i", { class: "bi bi-arrow-left me-2" }, null, -1),
                createTextVNode(" Go Back ")
              ]))
            ])
          ]),
          createBaseVNode("div", _hoisted_7, [
            _cache[9] || (_cache[9] = createBaseVNode("h3", { class: "h5 mb-3" }, "Or try these helpful links:", -1)),
            createBaseVNode("div", _hoisted_8, [
              createVNode(_component_router_link, {
                to: "/enhanced-validator",
                class: "btn btn-outline-primary"
              }, {
                default: withCtx(() => _cache[6] || (_cache[6] = [
                  createBaseVNode("i", { class: "bi bi-shield-check me-2" }, null, -1),
                  createTextVNode(" Enhanced Validator ")
                ])),
                _: 1,
                __: [6]
              }),
              _cache[7] || (_cache[7] = createBaseVNode("a", {
                href: "#",
                class: "btn btn-outline-secondary"
              }, [
                createBaseVNode("i", { class: "bi bi-question-circle me-2" }),
                createTextVNode(" Help Center ")
              ], -1)),
              _cache[8] || (_cache[8] = createBaseVNode("a", {
                href: "#",
                class: "btn btn-outline-secondary"
              }, [
                createBaseVNode("i", { class: "bi bi-envelope me-2" }),
                createTextVNode(" Contact Support ")
              ], -1))
            ])
          ])
        ])
      ])
    ])
  ]);
}
const NotFound = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-abe75d55"]]);
export {
  NotFound as default
};
//# sourceMappingURL=NotFound-DpimPS8k.js.map
