import { _ as _export_sfc } from "./index-Ceo-VWYs.js";
import { c as createElementBlock, o as openBlock, b as createBaseVNode, d as createVNode, w as withCtx, g as createTextVNode, f as resolveComponent } from "./vendor-DU8YFPOn.js";
const _hoisted_1 = { class: "docs-page" };
const _hoisted_2 = { class: "docs-list" };
const _sfc_main = {
  __name: "Docs",
  setup(__props) {
    return (_ctx, _cache) => {
      const _component_router_link = resolveComponent("router-link");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        _cache[4] || (_cache[4] = createBaseVNode("h1", null, "CaseStrainer Documentation", -1)),
        _cache[5] || (_cache[5] = createBaseVNode("p", null, "Welcome to the CaseStrainer documentation hub. Find guides, API docs, and more below.", -1)),
        createBaseVNode("ul", _hoisted_2, [
          createBaseVNode("li", null, [
            createVNode(_component_router_link, { to: "/docs/api" }, {
              default: withCtx(() => _cache[0] || (_cache[0] = [
                createTextVNode("API Documentation")
              ])),
              _: 1,
              __: [0]
            })
          ]),
          _cache[2] || (_cache[2] = createBaseVNode("li", null, [
            createBaseVNode("a", {
              href: "https://github.com/your-org/CaseStrainer/blob/main/README.md",
              target: "_blank"
            }, "User Guide (README)")
          ], -1)),
          _cache[3] || (_cache[3] = createBaseVNode("li", null, [
            createBaseVNode("a", {
              href: "https://github.com/your-org/CaseStrainer/tree/main/docs",
              target: "_blank"
            }, "More Documentation")
          ], -1)),
          createBaseVNode("li", null, [
            createVNode(_component_router_link, { to: "/" }, {
              default: withCtx(() => _cache[1] || (_cache[1] = [
                createTextVNode("Back to Home")
              ])),
              _: 1,
              __: [1]
            })
          ])
        ])
      ]);
    };
  }
};
const Docs = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-4b072b05"]]);
export {
  Docs as default
};
//# sourceMappingURL=Docs-CMxF-wOe.js.map
