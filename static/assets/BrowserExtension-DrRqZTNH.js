import { _ as _export_sfc } from "./index-Ceo-VWYs.js";
import { c as createElementBlock, o as openBlock, b as createBaseVNode, H as createStaticVNode, d as createVNode, w as withCtx, g as createTextVNode, f as resolveComponent } from "./vendor-DU8YFPOn.js";
const _sfc_main = {
  name: "BrowserExtension"
};
const _hoisted_1 = { class: "container py-5" };
const _hoisted_2 = { class: "row justify-content-center" };
const _hoisted_3 = { class: "col-lg-8 text-center" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = resolveComponent("router-link");
  return openBlock(), createElementBlock("div", _hoisted_1, [
    createBaseVNode("div", _hoisted_2, [
      createBaseVNode("div", _hoisted_3, [
        _cache[1] || (_cache[1] = createStaticVNode('<h1 class="display-4 mb-3" data-v-801abb10><i class="bi bi-puzzle me-2" data-v-801abb10></i> CaseStrainer Browser Extension</h1><p class="lead mb-4" data-v-801abb10>Validate legal citations directly while browsing the web. Highlight, verify, and get authoritative links instantly on any legal document or case page.</p><div class="alert alert-info py-4" data-v-801abb10><h4 class="mb-2" data-v-801abb10>Coming Soon!</h4><p data-v-801abb10>We are working on a Chrome/Edge/Firefox extension for seamless citation validation. Stay tuned for updates and download links.</p></div>', 3)),
        createVNode(_component_router_link, {
          to: "/",
          class: "btn btn-primary mt-3"
        }, {
          default: withCtx(() => _cache[0] || (_cache[0] = [
            createBaseVNode("i", { class: "bi bi-house-door me-1" }, null, -1),
            createTextVNode(" Back to Home ")
          ])),
          _: 1,
          __: [0]
        })
      ])
    ])
  ]);
}
const BrowserExtension = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-801abb10"]]);
export {
  BrowserExtension as default
};
//# sourceMappingURL=BrowserExtension-DrRqZTNH.js.map
