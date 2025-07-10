import { _ as _export_sfc } from "./index-Dl5kF7e3.js";
import { c as createElementBlock, o as openBlock, b as createBaseVNode, v as createStaticVNode, d as createVNode, w as withCtx, g as createTextVNode, f as resolveComponent } from "./vendor-0f3ixpnm.js";
const _sfc_main = {
  name: "WordPlugin"
};
const _hoisted_1 = { class: "container py-5" };
const _hoisted_2 = { class: "row justify-content-center" };
const _hoisted_3 = { class: "col-lg-8 text-center" };
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = resolveComponent("router-link");
  return openBlock(), createElementBlock("div", _hoisted_1, [
    createBaseVNode("div", _hoisted_2, [
      createBaseVNode("div", _hoisted_3, [
        _cache[1] || (_cache[1] = createStaticVNode('<h1 class="display-4 mb-3" data-v-687e57dc><i class="bi bi-file-earmark-word me-2" data-v-687e57dc></i> CaseStrainer Word Plug-in</h1><p class="lead mb-4" data-v-687e57dc>Validate legal citations directly inside your Microsoft Word documents. Highlight, verify, and correct citations as you write.</p><div class="alert alert-info py-4" data-v-687e57dc><h4 class="mb-2" data-v-687e57dc>Coming Soon!</h4><p data-v-687e57dc>We are developing a Microsoft Word add-in for seamless in-document citation validation. Stay tuned for updates and download links.</p></div>', 3)),
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
const WordPlugin = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-687e57dc"]]);
export {
  WordPlugin as default
};
//# sourceMappingURL=WordPlugin-CxcKzwKV.js.map
