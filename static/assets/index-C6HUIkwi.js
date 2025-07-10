const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/HomeView-CI4EUgxv.js","assets/vendor-CDDSDoLJ.js","assets/RecentInputs-Dx2uh2Yn.js","assets/RecentInputs-F1BDFzyY.css","assets/HomeView-BOlnLWsi.css","assets/EnhancedValidator-B30_4ffa.js","assets/EnhancedValidator-Jg3eubeh.css","assets/NotFound-DpimPS8k.js","assets/NotFound-Dwg51vAD.css","assets/BrowserExtension-ClwUVEdP.js","assets/BrowserExtension-DlofO4L7.css","assets/WordPlugin-c3pnPb2h.js","assets/WordPlugin-DGJUnz3y.css","assets/ApiDocs-CvQsyIwM.js","assets/ApiDocs-Cp2bLcFt.css","assets/Docs-CVXY35kc.js","assets/Docs-RWUYxnzg.css"])))=>i.map(i=>d[i]);
import { e as effectScope, r as ref, m as markRaw, a as readonly, c as createElementBlock, b as createBaseVNode, d as createVNode, w as withCtx, f as resolveComponent, t as toDisplayString, o as openBlock, g as createTextVNode, T as Transition, h as createBlock, i as resolveDynamicComponent, j as createRouter, k as createWebHistory, l as createCommentVNode, F as Fragment, n as renderList, p as computed, q as createApp } from "./vendor-CDDSDoLJ.js";
(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) {
    return;
  }
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) {
    processPreload(link);
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") {
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.tagName === "LINK" && node.rel === "modulepreload")
          processPreload(node);
      }
    }
  }).observe(document, { childList: true, subtree: true });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials")
      fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep)
      return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
})();
function bind(fn, thisArg) {
  return function wrap() {
    return fn.apply(thisArg, arguments);
  };
}
const { toString } = Object.prototype;
const { getPrototypeOf } = Object;
const { iterator, toStringTag } = Symbol;
const kindOf = /* @__PURE__ */ ((cache) => (thing) => {
  const str = toString.call(thing);
  return cache[str] || (cache[str] = str.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null));
const kindOfTest = (type) => {
  type = type.toLowerCase();
  return (thing) => kindOf(thing) === type;
};
const typeOfTest = (type) => (thing) => typeof thing === type;
const { isArray } = Array;
const isUndefined = typeOfTest("undefined");
function isBuffer(val) {
  return val !== null && !isUndefined(val) && val.constructor !== null && !isUndefined(val.constructor) && isFunction(val.constructor.isBuffer) && val.constructor.isBuffer(val);
}
const isArrayBuffer = kindOfTest("ArrayBuffer");
function isArrayBufferView(val) {
  let result;
  if (typeof ArrayBuffer !== "undefined" && ArrayBuffer.isView) {
    result = ArrayBuffer.isView(val);
  } else {
    result = val && val.buffer && isArrayBuffer(val.buffer);
  }
  return result;
}
const isString = typeOfTest("string");
const isFunction = typeOfTest("function");
const isNumber = typeOfTest("number");
const isObject = (thing) => thing !== null && typeof thing === "object";
const isBoolean = (thing) => thing === true || thing === false;
const isPlainObject = (val) => {
  if (kindOf(val) !== "object") {
    return false;
  }
  const prototype2 = getPrototypeOf(val);
  return (prototype2 === null || prototype2 === Object.prototype || Object.getPrototypeOf(prototype2) === null) && !(toStringTag in val) && !(iterator in val);
};
const isDate = kindOfTest("Date");
const isFile = kindOfTest("File");
const isBlob = kindOfTest("Blob");
const isFileList = kindOfTest("FileList");
const isStream = (val) => isObject(val) && isFunction(val.pipe);
const isFormData = (thing) => {
  let kind;
  return thing && (typeof FormData === "function" && thing instanceof FormData || isFunction(thing.append) && ((kind = kindOf(thing)) === "formdata" || // detect form-data instance
  kind === "object" && isFunction(thing.toString) && thing.toString() === "[object FormData]"));
};
const isURLSearchParams = kindOfTest("URLSearchParams");
const [isReadableStream, isRequest, isResponse, isHeaders] = ["ReadableStream", "Request", "Response", "Headers"].map(kindOfTest);
const trim = (str) => str.trim ? str.trim() : str.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function forEach(obj, fn, { allOwnKeys = false } = {}) {
  if (obj === null || typeof obj === "undefined") {
    return;
  }
  let i;
  let l;
  if (typeof obj !== "object") {
    obj = [obj];
  }
  if (isArray(obj)) {
    for (i = 0, l = obj.length; i < l; i++) {
      fn.call(null, obj[i], i, obj);
    }
  } else {
    const keys = allOwnKeys ? Object.getOwnPropertyNames(obj) : Object.keys(obj);
    const len = keys.length;
    let key;
    for (i = 0; i < len; i++) {
      key = keys[i];
      fn.call(null, obj[key], key, obj);
    }
  }
}
function findKey(obj, key) {
  key = key.toLowerCase();
  const keys = Object.keys(obj);
  let i = keys.length;
  let _key;
  while (i-- > 0) {
    _key = keys[i];
    if (key === _key.toLowerCase()) {
      return _key;
    }
  }
  return null;
}
const _global = (() => {
  if (typeof globalThis !== "undefined") return globalThis;
  return typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : global;
})();
const isContextDefined = (context) => !isUndefined(context) && context !== _global;
function merge() {
  const { caseless } = isContextDefined(this) && this || {};
  const result = {};
  const assignValue = (val, key) => {
    const targetKey = caseless && findKey(result, key) || key;
    if (isPlainObject(result[targetKey]) && isPlainObject(val)) {
      result[targetKey] = merge(result[targetKey], val);
    } else if (isPlainObject(val)) {
      result[targetKey] = merge({}, val);
    } else if (isArray(val)) {
      result[targetKey] = val.slice();
    } else {
      result[targetKey] = val;
    }
  };
  for (let i = 0, l = arguments.length; i < l; i++) {
    arguments[i] && forEach(arguments[i], assignValue);
  }
  return result;
}
const extend = (a, b, thisArg, { allOwnKeys } = {}) => {
  forEach(b, (val, key) => {
    if (thisArg && isFunction(val)) {
      a[key] = bind(val, thisArg);
    } else {
      a[key] = val;
    }
  }, { allOwnKeys });
  return a;
};
const stripBOM = (content) => {
  if (content.charCodeAt(0) === 65279) {
    content = content.slice(1);
  }
  return content;
};
const inherits = (constructor, superConstructor, props, descriptors2) => {
  constructor.prototype = Object.create(superConstructor.prototype, descriptors2);
  constructor.prototype.constructor = constructor;
  Object.defineProperty(constructor, "super", {
    value: superConstructor.prototype
  });
  props && Object.assign(constructor.prototype, props);
};
const toFlatObject = (sourceObj, destObj, filter2, propFilter) => {
  let props;
  let i;
  let prop;
  const merged = {};
  destObj = destObj || {};
  if (sourceObj == null) return destObj;
  do {
    props = Object.getOwnPropertyNames(sourceObj);
    i = props.length;
    while (i-- > 0) {
      prop = props[i];
      if ((!propFilter || propFilter(prop, sourceObj, destObj)) && !merged[prop]) {
        destObj[prop] = sourceObj[prop];
        merged[prop] = true;
      }
    }
    sourceObj = filter2 !== false && getPrototypeOf(sourceObj);
  } while (sourceObj && (!filter2 || filter2(sourceObj, destObj)) && sourceObj !== Object.prototype);
  return destObj;
};
const endsWith = (str, searchString, position) => {
  str = String(str);
  if (position === void 0 || position > str.length) {
    position = str.length;
  }
  position -= searchString.length;
  const lastIndex = str.indexOf(searchString, position);
  return lastIndex !== -1 && lastIndex === position;
};
const toArray = (thing) => {
  if (!thing) return null;
  if (isArray(thing)) return thing;
  let i = thing.length;
  if (!isNumber(i)) return null;
  const arr = new Array(i);
  while (i-- > 0) {
    arr[i] = thing[i];
  }
  return arr;
};
const isTypedArray = /* @__PURE__ */ ((TypedArray) => {
  return (thing) => {
    return TypedArray && thing instanceof TypedArray;
  };
})(typeof Uint8Array !== "undefined" && getPrototypeOf(Uint8Array));
const forEachEntry = (obj, fn) => {
  const generator = obj && obj[iterator];
  const _iterator = generator.call(obj);
  let result;
  while ((result = _iterator.next()) && !result.done) {
    const pair = result.value;
    fn.call(obj, pair[0], pair[1]);
  }
};
const matchAll = (regExp, str) => {
  let matches;
  const arr = [];
  while ((matches = regExp.exec(str)) !== null) {
    arr.push(matches);
  }
  return arr;
};
const isHTMLForm = kindOfTest("HTMLFormElement");
const toCamelCase = (str) => {
  return str.toLowerCase().replace(
    /[-_\s]([a-z\d])(\w*)/g,
    function replacer(m, p1, p2) {
      return p1.toUpperCase() + p2;
    }
  );
};
const hasOwnProperty = (({ hasOwnProperty: hasOwnProperty2 }) => (obj, prop) => hasOwnProperty2.call(obj, prop))(Object.prototype);
const isRegExp = kindOfTest("RegExp");
const reduceDescriptors = (obj, reducer) => {
  const descriptors2 = Object.getOwnPropertyDescriptors(obj);
  const reducedDescriptors = {};
  forEach(descriptors2, (descriptor, name) => {
    let ret;
    if ((ret = reducer(descriptor, name, obj)) !== false) {
      reducedDescriptors[name] = ret || descriptor;
    }
  });
  Object.defineProperties(obj, reducedDescriptors);
};
const freezeMethods = (obj) => {
  reduceDescriptors(obj, (descriptor, name) => {
    if (isFunction(obj) && ["arguments", "caller", "callee"].indexOf(name) !== -1) {
      return false;
    }
    const value = obj[name];
    if (!isFunction(value)) return;
    descriptor.enumerable = false;
    if ("writable" in descriptor) {
      descriptor.writable = false;
      return;
    }
    if (!descriptor.set) {
      descriptor.set = () => {
        throw Error("Can not rewrite read-only method '" + name + "'");
      };
    }
  });
};
const toObjectSet = (arrayOrString, delimiter) => {
  const obj = {};
  const define = (arr) => {
    arr.forEach((value) => {
      obj[value] = true;
    });
  };
  isArray(arrayOrString) ? define(arrayOrString) : define(String(arrayOrString).split(delimiter));
  return obj;
};
const noop = () => {
};
const toFiniteNumber = (value, defaultValue) => {
  return value != null && Number.isFinite(value = +value) ? value : defaultValue;
};
function isSpecCompliantForm(thing) {
  return !!(thing && isFunction(thing.append) && thing[toStringTag] === "FormData" && thing[iterator]);
}
const toJSONObject = (obj) => {
  const stack = new Array(10);
  const visit = (source, i) => {
    if (isObject(source)) {
      if (stack.indexOf(source) >= 0) {
        return;
      }
      if (!("toJSON" in source)) {
        stack[i] = source;
        const target = isArray(source) ? [] : {};
        forEach(source, (value, key) => {
          const reducedValue = visit(value, i + 1);
          !isUndefined(reducedValue) && (target[key] = reducedValue);
        });
        stack[i] = void 0;
        return target;
      }
    }
    return source;
  };
  return visit(obj, 0);
};
const isAsyncFn = kindOfTest("AsyncFunction");
const isThenable = (thing) => thing && (isObject(thing) || isFunction(thing)) && isFunction(thing.then) && isFunction(thing.catch);
const _setImmediate = ((setImmediateSupported, postMessageSupported) => {
  if (setImmediateSupported) {
    return setImmediate;
  }
  return postMessageSupported ? ((token, callbacks) => {
    _global.addEventListener("message", ({ source, data }) => {
      if (source === _global && data === token) {
        callbacks.length && callbacks.shift()();
      }
    }, false);
    return (cb) => {
      callbacks.push(cb);
      _global.postMessage(token, "*");
    };
  })(`axios@${Math.random()}`, []) : (cb) => setTimeout(cb);
})(
  typeof setImmediate === "function",
  isFunction(_global.postMessage)
);
const asap = typeof queueMicrotask !== "undefined" ? queueMicrotask.bind(_global) : typeof process !== "undefined" && process.nextTick || _setImmediate;
const isIterable = (thing) => thing != null && isFunction(thing[iterator]);
const utils$1 = {
  isArray,
  isArrayBuffer,
  isBuffer,
  isFormData,
  isArrayBufferView,
  isString,
  isNumber,
  isBoolean,
  isObject,
  isPlainObject,
  isReadableStream,
  isRequest,
  isResponse,
  isHeaders,
  isUndefined,
  isDate,
  isFile,
  isBlob,
  isRegExp,
  isFunction,
  isStream,
  isURLSearchParams,
  isTypedArray,
  isFileList,
  forEach,
  merge,
  extend,
  trim,
  stripBOM,
  inherits,
  toFlatObject,
  kindOf,
  kindOfTest,
  endsWith,
  toArray,
  forEachEntry,
  matchAll,
  isHTMLForm,
  hasOwnProperty,
  hasOwnProp: hasOwnProperty,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors,
  freezeMethods,
  toObjectSet,
  toCamelCase,
  noop,
  toFiniteNumber,
  findKey,
  global: _global,
  isContextDefined,
  isSpecCompliantForm,
  toJSONObject,
  isAsyncFn,
  isThenable,
  setImmediate: _setImmediate,
  asap,
  isIterable
};
function AxiosError$1(message, code, config, request, response) {
  Error.call(this);
  if (Error.captureStackTrace) {
    Error.captureStackTrace(this, this.constructor);
  } else {
    this.stack = new Error().stack;
  }
  this.message = message;
  this.name = "AxiosError";
  code && (this.code = code);
  config && (this.config = config);
  request && (this.request = request);
  if (response) {
    this.response = response;
    this.status = response.status ? response.status : null;
  }
}
utils$1.inherits(AxiosError$1, Error, {
  toJSON: function toJSON() {
    return {
      // Standard
      message: this.message,
      name: this.name,
      // Microsoft
      description: this.description,
      number: this.number,
      // Mozilla
      fileName: this.fileName,
      lineNumber: this.lineNumber,
      columnNumber: this.columnNumber,
      stack: this.stack,
      // Axios
      config: utils$1.toJSONObject(this.config),
      code: this.code,
      status: this.status
    };
  }
});
const prototype$1 = AxiosError$1.prototype;
const descriptors = {};
[
  "ERR_BAD_OPTION_VALUE",
  "ERR_BAD_OPTION",
  "ECONNABORTED",
  "ETIMEDOUT",
  "ERR_NETWORK",
  "ERR_FR_TOO_MANY_REDIRECTS",
  "ERR_DEPRECATED",
  "ERR_BAD_RESPONSE",
  "ERR_BAD_REQUEST",
  "ERR_CANCELED",
  "ERR_NOT_SUPPORT",
  "ERR_INVALID_URL"
  // eslint-disable-next-line func-names
].forEach((code) => {
  descriptors[code] = { value: code };
});
Object.defineProperties(AxiosError$1, descriptors);
Object.defineProperty(prototype$1, "isAxiosError", { value: true });
AxiosError$1.from = (error, code, config, request, response, customProps) => {
  const axiosError = Object.create(prototype$1);
  utils$1.toFlatObject(error, axiosError, function filter2(obj) {
    return obj !== Error.prototype;
  }, (prop) => {
    return prop !== "isAxiosError";
  });
  AxiosError$1.call(axiosError, error.message, code, config, request, response);
  axiosError.cause = error;
  axiosError.name = error.name;
  customProps && Object.assign(axiosError, customProps);
  return axiosError;
};
const httpAdapter = null;
function isVisitable(thing) {
  return utils$1.isPlainObject(thing) || utils$1.isArray(thing);
}
function removeBrackets(key) {
  return utils$1.endsWith(key, "[]") ? key.slice(0, -2) : key;
}
function renderKey(path, key, dots) {
  if (!path) return key;
  return path.concat(key).map(function each(token, i) {
    token = removeBrackets(token);
    return !dots && i ? "[" + token + "]" : token;
  }).join(dots ? "." : "");
}
function isFlatArray(arr) {
  return utils$1.isArray(arr) && !arr.some(isVisitable);
}
const predicates = utils$1.toFlatObject(utils$1, {}, null, function filter(prop) {
  return /^is[A-Z]/.test(prop);
});
function toFormData$1(obj, formData, options) {
  if (!utils$1.isObject(obj)) {
    throw new TypeError("target must be an object");
  }
  formData = formData || new FormData();
  options = utils$1.toFlatObject(options, {
    metaTokens: true,
    dots: false,
    indexes: false
  }, false, function defined(option, source) {
    return !utils$1.isUndefined(source[option]);
  });
  const metaTokens = options.metaTokens;
  const visitor = options.visitor || defaultVisitor;
  const dots = options.dots;
  const indexes = options.indexes;
  const _Blob = options.Blob || typeof Blob !== "undefined" && Blob;
  const useBlob = _Blob && utils$1.isSpecCompliantForm(formData);
  if (!utils$1.isFunction(visitor)) {
    throw new TypeError("visitor must be a function");
  }
  function convertValue(value) {
    if (value === null) return "";
    if (utils$1.isDate(value)) {
      return value.toISOString();
    }
    if (utils$1.isBoolean(value)) {
      return value.toString();
    }
    if (!useBlob && utils$1.isBlob(value)) {
      throw new AxiosError$1("Blob is not supported. Use a Buffer instead.");
    }
    if (utils$1.isArrayBuffer(value) || utils$1.isTypedArray(value)) {
      return useBlob && typeof Blob === "function" ? new Blob([value]) : Buffer.from(value);
    }
    return value;
  }
  function defaultVisitor(value, key, path) {
    let arr = value;
    if (value && !path && typeof value === "object") {
      if (utils$1.endsWith(key, "{}")) {
        key = metaTokens ? key : key.slice(0, -2);
        value = JSON.stringify(value);
      } else if (utils$1.isArray(value) && isFlatArray(value) || (utils$1.isFileList(value) || utils$1.endsWith(key, "[]")) && (arr = utils$1.toArray(value))) {
        key = removeBrackets(key);
        arr.forEach(function each(el, index) {
          !(utils$1.isUndefined(el) || el === null) && formData.append(
            // eslint-disable-next-line no-nested-ternary
            indexes === true ? renderKey([key], index, dots) : indexes === null ? key : key + "[]",
            convertValue(el)
          );
        });
        return false;
      }
    }
    if (isVisitable(value)) {
      return true;
    }
    formData.append(renderKey(path, key, dots), convertValue(value));
    return false;
  }
  const stack = [];
  const exposedHelpers = Object.assign(predicates, {
    defaultVisitor,
    convertValue,
    isVisitable
  });
  function build(value, path) {
    if (utils$1.isUndefined(value)) return;
    if (stack.indexOf(value) !== -1) {
      throw Error("Circular reference detected in " + path.join("."));
    }
    stack.push(value);
    utils$1.forEach(value, function each(el, key) {
      const result = !(utils$1.isUndefined(el) || el === null) && visitor.call(
        formData,
        el,
        utils$1.isString(key) ? key.trim() : key,
        path,
        exposedHelpers
      );
      if (result === true) {
        build(el, path ? path.concat(key) : [key]);
      }
    });
    stack.pop();
  }
  if (!utils$1.isObject(obj)) {
    throw new TypeError("data must be an object");
  }
  build(obj);
  return formData;
}
function encode$1(str) {
  const charMap = {
    "!": "%21",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "~": "%7E",
    "%20": "+",
    "%00": "\0"
  };
  return encodeURIComponent(str).replace(/[!'()~]|%20|%00/g, function replacer(match) {
    return charMap[match];
  });
}
function AxiosURLSearchParams(params, options) {
  this._pairs = [];
  params && toFormData$1(params, this, options);
}
const prototype = AxiosURLSearchParams.prototype;
prototype.append = function append(name, value) {
  this._pairs.push([name, value]);
};
prototype.toString = function toString2(encoder) {
  const _encode = encoder ? function(value) {
    return encoder.call(this, value, encode$1);
  } : encode$1;
  return this._pairs.map(function each(pair) {
    return _encode(pair[0]) + "=" + _encode(pair[1]);
  }, "").join("&");
};
function encode(val) {
  return encodeURIComponent(val).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+").replace(/%5B/gi, "[").replace(/%5D/gi, "]");
}
function buildURL(url, params, options) {
  if (!params) {
    return url;
  }
  const _encode = options && options.encode || encode;
  if (utils$1.isFunction(options)) {
    options = {
      serialize: options
    };
  }
  const serializeFn = options && options.serialize;
  let serializedParams;
  if (serializeFn) {
    serializedParams = serializeFn(params, options);
  } else {
    serializedParams = utils$1.isURLSearchParams(params) ? params.toString() : new AxiosURLSearchParams(params, options).toString(_encode);
  }
  if (serializedParams) {
    const hashmarkIndex = url.indexOf("#");
    if (hashmarkIndex !== -1) {
      url = url.slice(0, hashmarkIndex);
    }
    url += (url.indexOf("?") === -1 ? "?" : "&") + serializedParams;
  }
  return url;
}
class InterceptorManager {
  constructor() {
    this.handlers = [];
  }
  /**
   * Add a new interceptor to the stack
   *
   * @param {Function} fulfilled The function to handle `then` for a `Promise`
   * @param {Function} rejected The function to handle `reject` for a `Promise`
   *
   * @return {Number} An ID used to remove interceptor later
   */
  use(fulfilled, rejected, options) {
    this.handlers.push({
      fulfilled,
      rejected,
      synchronous: options ? options.synchronous : false,
      runWhen: options ? options.runWhen : null
    });
    return this.handlers.length - 1;
  }
  /**
   * Remove an interceptor from the stack
   *
   * @param {Number} id The ID that was returned by `use`
   *
   * @returns {Boolean} `true` if the interceptor was removed, `false` otherwise
   */
  eject(id) {
    if (this.handlers[id]) {
      this.handlers[id] = null;
    }
  }
  /**
   * Clear all interceptors from the stack
   *
   * @returns {void}
   */
  clear() {
    if (this.handlers) {
      this.handlers = [];
    }
  }
  /**
   * Iterate over all the registered interceptors
   *
   * This method is particularly useful for skipping over any
   * interceptors that may have become `null` calling `eject`.
   *
   * @param {Function} fn The function to call for each interceptor
   *
   * @returns {void}
   */
  forEach(fn) {
    utils$1.forEach(this.handlers, function forEachHandler(h) {
      if (h !== null) {
        fn(h);
      }
    });
  }
}
const transitionalDefaults = {
  silentJSONParsing: true,
  forcedJSONParsing: true,
  clarifyTimeoutError: false
};
const URLSearchParams$1 = typeof URLSearchParams !== "undefined" ? URLSearchParams : AxiosURLSearchParams;
const FormData$1 = typeof FormData !== "undefined" ? FormData : null;
const Blob$1 = typeof Blob !== "undefined" ? Blob : null;
const platform$1 = {
  isBrowser: true,
  classes: {
    URLSearchParams: URLSearchParams$1,
    FormData: FormData$1,
    Blob: Blob$1
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
};
const hasBrowserEnv = typeof window !== "undefined" && typeof document !== "undefined";
const _navigator = typeof navigator === "object" && navigator || void 0;
const hasStandardBrowserEnv = hasBrowserEnv && (!_navigator || ["ReactNative", "NativeScript", "NS"].indexOf(_navigator.product) < 0);
const hasStandardBrowserWebWorkerEnv = (() => {
  return typeof WorkerGlobalScope !== "undefined" && // eslint-disable-next-line no-undef
  self instanceof WorkerGlobalScope && typeof self.importScripts === "function";
})();
const origin = hasBrowserEnv && window.location.href || "http://localhost";
const utils = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv,
  hasStandardBrowserEnv,
  hasStandardBrowserWebWorkerEnv,
  navigator: _navigator,
  origin
}, Symbol.toStringTag, { value: "Module" }));
const platform = {
  ...utils,
  ...platform$1
};
function toURLEncodedForm(data, options) {
  return toFormData$1(data, new platform.classes.URLSearchParams(), Object.assign({
    visitor: function(value, key, path, helpers) {
      if (platform.isNode && utils$1.isBuffer(value)) {
        this.append(key, value.toString("base64"));
        return false;
      }
      return helpers.defaultVisitor.apply(this, arguments);
    }
  }, options));
}
function parsePropPath(name) {
  return utils$1.matchAll(/\w+|\[(\w*)]/g, name).map((match) => {
    return match[0] === "[]" ? "" : match[1] || match[0];
  });
}
function arrayToObject(arr) {
  const obj = {};
  const keys = Object.keys(arr);
  let i;
  const len = keys.length;
  let key;
  for (i = 0; i < len; i++) {
    key = keys[i];
    obj[key] = arr[key];
  }
  return obj;
}
function formDataToJSON(formData) {
  function buildPath(path, value, target, index) {
    let name = path[index++];
    if (name === "__proto__") return true;
    const isNumericKey = Number.isFinite(+name);
    const isLast = index >= path.length;
    name = !name && utils$1.isArray(target) ? target.length : name;
    if (isLast) {
      if (utils$1.hasOwnProp(target, name)) {
        target[name] = [target[name], value];
      } else {
        target[name] = value;
      }
      return !isNumericKey;
    }
    if (!target[name] || !utils$1.isObject(target[name])) {
      target[name] = [];
    }
    const result = buildPath(path, value, target[name], index);
    if (result && utils$1.isArray(target[name])) {
      target[name] = arrayToObject(target[name]);
    }
    return !isNumericKey;
  }
  if (utils$1.isFormData(formData) && utils$1.isFunction(formData.entries)) {
    const obj = {};
    utils$1.forEachEntry(formData, (name, value) => {
      buildPath(parsePropPath(name), value, obj, 0);
    });
    return obj;
  }
  return null;
}
function stringifySafely(rawValue, parser, encoder) {
  if (utils$1.isString(rawValue)) {
    try {
      (parser || JSON.parse)(rawValue);
      return utils$1.trim(rawValue);
    } catch (e) {
      if (e.name !== "SyntaxError") {
        throw e;
      }
    }
  }
  return (encoder || JSON.stringify)(rawValue);
}
const defaults = {
  transitional: transitionalDefaults,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [function transformRequest(data, headers) {
    const contentType = headers.getContentType() || "";
    const hasJSONContentType = contentType.indexOf("application/json") > -1;
    const isObjectPayload = utils$1.isObject(data);
    if (isObjectPayload && utils$1.isHTMLForm(data)) {
      data = new FormData(data);
    }
    const isFormData2 = utils$1.isFormData(data);
    if (isFormData2) {
      return hasJSONContentType ? JSON.stringify(formDataToJSON(data)) : data;
    }
    if (utils$1.isArrayBuffer(data) || utils$1.isBuffer(data) || utils$1.isStream(data) || utils$1.isFile(data) || utils$1.isBlob(data) || utils$1.isReadableStream(data)) {
      return data;
    }
    if (utils$1.isArrayBufferView(data)) {
      return data.buffer;
    }
    if (utils$1.isURLSearchParams(data)) {
      headers.setContentType("application/x-www-form-urlencoded;charset=utf-8", false);
      return data.toString();
    }
    let isFileList2;
    if (isObjectPayload) {
      if (contentType.indexOf("application/x-www-form-urlencoded") > -1) {
        return toURLEncodedForm(data, this.formSerializer).toString();
      }
      if ((isFileList2 = utils$1.isFileList(data)) || contentType.indexOf("multipart/form-data") > -1) {
        const _FormData = this.env && this.env.FormData;
        return toFormData$1(
          isFileList2 ? { "files[]": data } : data,
          _FormData && new _FormData(),
          this.formSerializer
        );
      }
    }
    if (isObjectPayload || hasJSONContentType) {
      headers.setContentType("application/json", false);
      return stringifySafely(data);
    }
    return data;
  }],
  transformResponse: [function transformResponse(data) {
    const transitional2 = this.transitional || defaults.transitional;
    const forcedJSONParsing = transitional2 && transitional2.forcedJSONParsing;
    const JSONRequested = this.responseType === "json";
    if (utils$1.isResponse(data) || utils$1.isReadableStream(data)) {
      return data;
    }
    if (data && utils$1.isString(data) && (forcedJSONParsing && !this.responseType || JSONRequested)) {
      const silentJSONParsing = transitional2 && transitional2.silentJSONParsing;
      const strictJSONParsing = !silentJSONParsing && JSONRequested;
      try {
        return JSON.parse(data);
      } catch (e) {
        if (strictJSONParsing) {
          if (e.name === "SyntaxError") {
            throw AxiosError$1.from(e, AxiosError$1.ERR_BAD_RESPONSE, this, null, this.response);
          }
          throw e;
        }
      }
    }
    return data;
  }],
  /**
   * A timeout in milliseconds to abort a request. If set to 0 (default) a
   * timeout is not created.
   */
  timeout: 0,
  xsrfCookieName: "XSRF-TOKEN",
  xsrfHeaderName: "X-XSRF-TOKEN",
  maxContentLength: -1,
  maxBodyLength: -1,
  env: {
    FormData: platform.classes.FormData,
    Blob: platform.classes.Blob
  },
  validateStatus: function validateStatus(status) {
    return status >= 200 && status < 300;
  },
  headers: {
    common: {
      "Accept": "application/json, text/plain, */*",
      "Content-Type": void 0
    }
  }
};
utils$1.forEach(["delete", "get", "head", "post", "put", "patch"], (method) => {
  defaults.headers[method] = {};
});
const ignoreDuplicateOf = utils$1.toObjectSet([
  "age",
  "authorization",
  "content-length",
  "content-type",
  "etag",
  "expires",
  "from",
  "host",
  "if-modified-since",
  "if-unmodified-since",
  "last-modified",
  "location",
  "max-forwards",
  "proxy-authorization",
  "referer",
  "retry-after",
  "user-agent"
]);
const parseHeaders = (rawHeaders) => {
  const parsed = {};
  let key;
  let val;
  let i;
  rawHeaders && rawHeaders.split("\n").forEach(function parser(line) {
    i = line.indexOf(":");
    key = line.substring(0, i).trim().toLowerCase();
    val = line.substring(i + 1).trim();
    if (!key || parsed[key] && ignoreDuplicateOf[key]) {
      return;
    }
    if (key === "set-cookie") {
      if (parsed[key]) {
        parsed[key].push(val);
      } else {
        parsed[key] = [val];
      }
    } else {
      parsed[key] = parsed[key] ? parsed[key] + ", " + val : val;
    }
  });
  return parsed;
};
const $internals = Symbol("internals");
function normalizeHeader(header) {
  return header && String(header).trim().toLowerCase();
}
function normalizeValue(value) {
  if (value === false || value == null) {
    return value;
  }
  return utils$1.isArray(value) ? value.map(normalizeValue) : String(value);
}
function parseTokens(str) {
  const tokens = /* @__PURE__ */ Object.create(null);
  const tokensRE = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let match;
  while (match = tokensRE.exec(str)) {
    tokens[match[1]] = match[2];
  }
  return tokens;
}
const isValidHeaderName = (str) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(str.trim());
function matchHeaderValue(context, value, header, filter2, isHeaderNameFilter) {
  if (utils$1.isFunction(filter2)) {
    return filter2.call(this, value, header);
  }
  if (isHeaderNameFilter) {
    value = header;
  }
  if (!utils$1.isString(value)) return;
  if (utils$1.isString(filter2)) {
    return value.indexOf(filter2) !== -1;
  }
  if (utils$1.isRegExp(filter2)) {
    return filter2.test(value);
  }
}
function formatHeader(header) {
  return header.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (w, char, str) => {
    return char.toUpperCase() + str;
  });
}
function buildAccessors(obj, header) {
  const accessorName = utils$1.toCamelCase(" " + header);
  ["get", "set", "has"].forEach((methodName) => {
    Object.defineProperty(obj, methodName + accessorName, {
      value: function(arg1, arg2, arg3) {
        return this[methodName].call(this, header, arg1, arg2, arg3);
      },
      configurable: true
    });
  });
}
let AxiosHeaders$1 = class AxiosHeaders {
  constructor(headers) {
    headers && this.set(headers);
  }
  set(header, valueOrRewrite, rewrite) {
    const self2 = this;
    function setHeader(_value, _header, _rewrite) {
      const lHeader = normalizeHeader(_header);
      if (!lHeader) {
        throw new Error("header name must be a non-empty string");
      }
      const key = utils$1.findKey(self2, lHeader);
      if (!key || self2[key] === void 0 || _rewrite === true || _rewrite === void 0 && self2[key] !== false) {
        self2[key || _header] = normalizeValue(_value);
      }
    }
    const setHeaders = (headers, _rewrite) => utils$1.forEach(headers, (_value, _header) => setHeader(_value, _header, _rewrite));
    if (utils$1.isPlainObject(header) || header instanceof this.constructor) {
      setHeaders(header, valueOrRewrite);
    } else if (utils$1.isString(header) && (header = header.trim()) && !isValidHeaderName(header)) {
      setHeaders(parseHeaders(header), valueOrRewrite);
    } else if (utils$1.isObject(header) && utils$1.isIterable(header)) {
      let obj = {}, dest, key;
      for (const entry of header) {
        if (!utils$1.isArray(entry)) {
          throw TypeError("Object iterator must return a key-value pair");
        }
        obj[key = entry[0]] = (dest = obj[key]) ? utils$1.isArray(dest) ? [...dest, entry[1]] : [dest, entry[1]] : entry[1];
      }
      setHeaders(obj, valueOrRewrite);
    } else {
      header != null && setHeader(valueOrRewrite, header, rewrite);
    }
    return this;
  }
  get(header, parser) {
    header = normalizeHeader(header);
    if (header) {
      const key = utils$1.findKey(this, header);
      if (key) {
        const value = this[key];
        if (!parser) {
          return value;
        }
        if (parser === true) {
          return parseTokens(value);
        }
        if (utils$1.isFunction(parser)) {
          return parser.call(this, value, key);
        }
        if (utils$1.isRegExp(parser)) {
          return parser.exec(value);
        }
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(header, matcher) {
    header = normalizeHeader(header);
    if (header) {
      const key = utils$1.findKey(this, header);
      return !!(key && this[key] !== void 0 && (!matcher || matchHeaderValue(this, this[key], key, matcher)));
    }
    return false;
  }
  delete(header, matcher) {
    const self2 = this;
    let deleted = false;
    function deleteHeader(_header) {
      _header = normalizeHeader(_header);
      if (_header) {
        const key = utils$1.findKey(self2, _header);
        if (key && (!matcher || matchHeaderValue(self2, self2[key], key, matcher))) {
          delete self2[key];
          deleted = true;
        }
      }
    }
    if (utils$1.isArray(header)) {
      header.forEach(deleteHeader);
    } else {
      deleteHeader(header);
    }
    return deleted;
  }
  clear(matcher) {
    const keys = Object.keys(this);
    let i = keys.length;
    let deleted = false;
    while (i--) {
      const key = keys[i];
      if (!matcher || matchHeaderValue(this, this[key], key, matcher, true)) {
        delete this[key];
        deleted = true;
      }
    }
    return deleted;
  }
  normalize(format) {
    const self2 = this;
    const headers = {};
    utils$1.forEach(this, (value, header) => {
      const key = utils$1.findKey(headers, header);
      if (key) {
        self2[key] = normalizeValue(value);
        delete self2[header];
        return;
      }
      const normalized = format ? formatHeader(header) : String(header).trim();
      if (normalized !== header) {
        delete self2[header];
      }
      self2[normalized] = normalizeValue(value);
      headers[normalized] = true;
    });
    return this;
  }
  concat(...targets) {
    return this.constructor.concat(this, ...targets);
  }
  toJSON(asStrings) {
    const obj = /* @__PURE__ */ Object.create(null);
    utils$1.forEach(this, (value, header) => {
      value != null && value !== false && (obj[header] = asStrings && utils$1.isArray(value) ? value.join(", ") : value);
    });
    return obj;
  }
  [Symbol.iterator]() {
    return Object.entries(this.toJSON())[Symbol.iterator]();
  }
  toString() {
    return Object.entries(this.toJSON()).map(([header, value]) => header + ": " + value).join("\n");
  }
  getSetCookie() {
    return this.get("set-cookie") || [];
  }
  get [Symbol.toStringTag]() {
    return "AxiosHeaders";
  }
  static from(thing) {
    return thing instanceof this ? thing : new this(thing);
  }
  static concat(first, ...targets) {
    const computed2 = new this(first);
    targets.forEach((target) => computed2.set(target));
    return computed2;
  }
  static accessor(header) {
    const internals = this[$internals] = this[$internals] = {
      accessors: {}
    };
    const accessors = internals.accessors;
    const prototype2 = this.prototype;
    function defineAccessor(_header) {
      const lHeader = normalizeHeader(_header);
      if (!accessors[lHeader]) {
        buildAccessors(prototype2, _header);
        accessors[lHeader] = true;
      }
    }
    utils$1.isArray(header) ? header.forEach(defineAccessor) : defineAccessor(header);
    return this;
  }
};
AxiosHeaders$1.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
utils$1.reduceDescriptors(AxiosHeaders$1.prototype, ({ value }, key) => {
  let mapped = key[0].toUpperCase() + key.slice(1);
  return {
    get: () => value,
    set(headerValue) {
      this[mapped] = headerValue;
    }
  };
});
utils$1.freezeMethods(AxiosHeaders$1);
function transformData(fns, response) {
  const config = this || defaults;
  const context = response || config;
  const headers = AxiosHeaders$1.from(context.headers);
  let data = context.data;
  utils$1.forEach(fns, function transform(fn) {
    data = fn.call(config, data, headers.normalize(), response ? response.status : void 0);
  });
  headers.normalize();
  return data;
}
function isCancel$1(value) {
  return !!(value && value.__CANCEL__);
}
function CanceledError$1(message, config, request) {
  AxiosError$1.call(this, message == null ? "canceled" : message, AxiosError$1.ERR_CANCELED, config, request);
  this.name = "CanceledError";
}
utils$1.inherits(CanceledError$1, AxiosError$1, {
  __CANCEL__: true
});
function settle(resolve, reject, response) {
  const validateStatus2 = response.config.validateStatus;
  if (!response.status || !validateStatus2 || validateStatus2(response.status)) {
    resolve(response);
  } else {
    reject(new AxiosError$1(
      "Request failed with status code " + response.status,
      [AxiosError$1.ERR_BAD_REQUEST, AxiosError$1.ERR_BAD_RESPONSE][Math.floor(response.status / 100) - 4],
      response.config,
      response.request,
      response
    ));
  }
}
function parseProtocol(url) {
  const match = /^([-+\w]{1,25})(:?\/\/|:)/.exec(url);
  return match && match[1] || "";
}
function speedometer(samplesCount, min) {
  samplesCount = samplesCount || 10;
  const bytes = new Array(samplesCount);
  const timestamps = new Array(samplesCount);
  let head = 0;
  let tail = 0;
  let firstSampleTS;
  min = min !== void 0 ? min : 1e3;
  return function push(chunkLength) {
    const now = Date.now();
    const startedAt = timestamps[tail];
    if (!firstSampleTS) {
      firstSampleTS = now;
    }
    bytes[head] = chunkLength;
    timestamps[head] = now;
    let i = tail;
    let bytesCount = 0;
    while (i !== head) {
      bytesCount += bytes[i++];
      i = i % samplesCount;
    }
    head = (head + 1) % samplesCount;
    if (head === tail) {
      tail = (tail + 1) % samplesCount;
    }
    if (now - firstSampleTS < min) {
      return;
    }
    const passed = startedAt && now - startedAt;
    return passed ? Math.round(bytesCount * 1e3 / passed) : void 0;
  };
}
function throttle(fn, freq) {
  let timestamp = 0;
  let threshold = 1e3 / freq;
  let lastArgs;
  let timer;
  const invoke = (args, now = Date.now()) => {
    timestamp = now;
    lastArgs = null;
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    fn.apply(null, args);
  };
  const throttled = (...args) => {
    const now = Date.now();
    const passed = now - timestamp;
    if (passed >= threshold) {
      invoke(args, now);
    } else {
      lastArgs = args;
      if (!timer) {
        timer = setTimeout(() => {
          timer = null;
          invoke(lastArgs);
        }, threshold - passed);
      }
    }
  };
  const flush = () => lastArgs && invoke(lastArgs);
  return [throttled, flush];
}
const progressEventReducer = (listener, isDownloadStream, freq = 3) => {
  let bytesNotified = 0;
  const _speedometer = speedometer(50, 250);
  return throttle((e) => {
    const loaded = e.loaded;
    const total = e.lengthComputable ? e.total : void 0;
    const progressBytes = loaded - bytesNotified;
    const rate = _speedometer(progressBytes);
    const inRange = loaded <= total;
    bytesNotified = loaded;
    const data = {
      loaded,
      total,
      progress: total ? loaded / total : void 0,
      bytes: progressBytes,
      rate: rate ? rate : void 0,
      estimated: rate && total && inRange ? (total - loaded) / rate : void 0,
      event: e,
      lengthComputable: total != null,
      [isDownloadStream ? "download" : "upload"]: true
    };
    listener(data);
  }, freq);
};
const progressEventDecorator = (total, throttled) => {
  const lengthComputable = total != null;
  return [(loaded) => throttled[0]({
    lengthComputable,
    total,
    loaded
  }), throttled[1]];
};
const asyncDecorator = (fn) => (...args) => utils$1.asap(() => fn(...args));
const isURLSameOrigin = platform.hasStandardBrowserEnv ? /* @__PURE__ */ ((origin2, isMSIE) => (url) => {
  url = new URL(url, platform.origin);
  return origin2.protocol === url.protocol && origin2.host === url.host && (isMSIE || origin2.port === url.port);
})(
  new URL(platform.origin),
  platform.navigator && /(msie|trident)/i.test(platform.navigator.userAgent)
) : () => true;
const cookies = platform.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(name, value, expires, path, domain, secure) {
      const cookie = [name + "=" + encodeURIComponent(value)];
      utils$1.isNumber(expires) && cookie.push("expires=" + new Date(expires).toGMTString());
      utils$1.isString(path) && cookie.push("path=" + path);
      utils$1.isString(domain) && cookie.push("domain=" + domain);
      secure === true && cookie.push("secure");
      document.cookie = cookie.join("; ");
    },
    read(name) {
      const match = document.cookie.match(new RegExp("(^|;\\s*)(" + name + ")=([^;]*)"));
      return match ? decodeURIComponent(match[3]) : null;
    },
    remove(name) {
      this.write(name, "", Date.now() - 864e5);
    }
  }
) : (
  // Non-standard browser env (web workers, react-native) lack needed support.
  {
    write() {
    },
    read() {
      return null;
    },
    remove() {
    }
  }
);
function isAbsoluteURL(url) {
  return /^([a-z][a-z\d+\-.]*:)?\/\//i.test(url);
}
function combineURLs(baseURL, relativeURL) {
  return relativeURL ? baseURL.replace(/\/?\/$/, "") + "/" + relativeURL.replace(/^\/+/, "") : baseURL;
}
function buildFullPath(baseURL, requestedURL, allowAbsoluteUrls) {
  let isRelativeUrl = !isAbsoluteURL(requestedURL);
  if (baseURL && (isRelativeUrl || allowAbsoluteUrls == false)) {
    return combineURLs(baseURL, requestedURL);
  }
  return requestedURL;
}
const headersToObject = (thing) => thing instanceof AxiosHeaders$1 ? { ...thing } : thing;
function mergeConfig$1(config1, config2) {
  config2 = config2 || {};
  const config = {};
  function getMergedValue(target, source, prop, caseless) {
    if (utils$1.isPlainObject(target) && utils$1.isPlainObject(source)) {
      return utils$1.merge.call({ caseless }, target, source);
    } else if (utils$1.isPlainObject(source)) {
      return utils$1.merge({}, source);
    } else if (utils$1.isArray(source)) {
      return source.slice();
    }
    return source;
  }
  function mergeDeepProperties(a, b, prop, caseless) {
    if (!utils$1.isUndefined(b)) {
      return getMergedValue(a, b, prop, caseless);
    } else if (!utils$1.isUndefined(a)) {
      return getMergedValue(void 0, a, prop, caseless);
    }
  }
  function valueFromConfig2(a, b) {
    if (!utils$1.isUndefined(b)) {
      return getMergedValue(void 0, b);
    }
  }
  function defaultToConfig2(a, b) {
    if (!utils$1.isUndefined(b)) {
      return getMergedValue(void 0, b);
    } else if (!utils$1.isUndefined(a)) {
      return getMergedValue(void 0, a);
    }
  }
  function mergeDirectKeys(a, b, prop) {
    if (prop in config2) {
      return getMergedValue(a, b);
    } else if (prop in config1) {
      return getMergedValue(void 0, a);
    }
  }
  const mergeMap = {
    url: valueFromConfig2,
    method: valueFromConfig2,
    data: valueFromConfig2,
    baseURL: defaultToConfig2,
    transformRequest: defaultToConfig2,
    transformResponse: defaultToConfig2,
    paramsSerializer: defaultToConfig2,
    timeout: defaultToConfig2,
    timeoutMessage: defaultToConfig2,
    withCredentials: defaultToConfig2,
    withXSRFToken: defaultToConfig2,
    adapter: defaultToConfig2,
    responseType: defaultToConfig2,
    xsrfCookieName: defaultToConfig2,
    xsrfHeaderName: defaultToConfig2,
    onUploadProgress: defaultToConfig2,
    onDownloadProgress: defaultToConfig2,
    decompress: defaultToConfig2,
    maxContentLength: defaultToConfig2,
    maxBodyLength: defaultToConfig2,
    beforeRedirect: defaultToConfig2,
    transport: defaultToConfig2,
    httpAgent: defaultToConfig2,
    httpsAgent: defaultToConfig2,
    cancelToken: defaultToConfig2,
    socketPath: defaultToConfig2,
    responseEncoding: defaultToConfig2,
    validateStatus: mergeDirectKeys,
    headers: (a, b, prop) => mergeDeepProperties(headersToObject(a), headersToObject(b), prop, true)
  };
  utils$1.forEach(Object.keys(Object.assign({}, config1, config2)), function computeConfigValue(prop) {
    const merge2 = mergeMap[prop] || mergeDeepProperties;
    const configValue = merge2(config1[prop], config2[prop], prop);
    utils$1.isUndefined(configValue) && merge2 !== mergeDirectKeys || (config[prop] = configValue);
  });
  return config;
}
const resolveConfig = (config) => {
  const newConfig = mergeConfig$1({}, config);
  let { data, withXSRFToken, xsrfHeaderName, xsrfCookieName, headers, auth } = newConfig;
  newConfig.headers = headers = AxiosHeaders$1.from(headers);
  newConfig.url = buildURL(buildFullPath(newConfig.baseURL, newConfig.url, newConfig.allowAbsoluteUrls), config.params, config.paramsSerializer);
  if (auth) {
    headers.set(
      "Authorization",
      "Basic " + btoa((auth.username || "") + ":" + (auth.password ? unescape(encodeURIComponent(auth.password)) : ""))
    );
  }
  let contentType;
  if (utils$1.isFormData(data)) {
    if (platform.hasStandardBrowserEnv || platform.hasStandardBrowserWebWorkerEnv) {
      headers.setContentType(void 0);
    } else if ((contentType = headers.getContentType()) !== false) {
      const [type, ...tokens] = contentType ? contentType.split(";").map((token) => token.trim()).filter(Boolean) : [];
      headers.setContentType([type || "multipart/form-data", ...tokens].join("; "));
    }
  }
  if (platform.hasStandardBrowserEnv) {
    withXSRFToken && utils$1.isFunction(withXSRFToken) && (withXSRFToken = withXSRFToken(newConfig));
    if (withXSRFToken || withXSRFToken !== false && isURLSameOrigin(newConfig.url)) {
      const xsrfValue = xsrfHeaderName && xsrfCookieName && cookies.read(xsrfCookieName);
      if (xsrfValue) {
        headers.set(xsrfHeaderName, xsrfValue);
      }
    }
  }
  return newConfig;
};
const isXHRAdapterSupported = typeof XMLHttpRequest !== "undefined";
const xhrAdapter = isXHRAdapterSupported && function(config) {
  return new Promise(function dispatchXhrRequest(resolve, reject) {
    const _config = resolveConfig(config);
    let requestData = _config.data;
    const requestHeaders = AxiosHeaders$1.from(_config.headers).normalize();
    let { responseType, onUploadProgress, onDownloadProgress } = _config;
    let onCanceled;
    let uploadThrottled, downloadThrottled;
    let flushUpload, flushDownload;
    function done() {
      flushUpload && flushUpload();
      flushDownload && flushDownload();
      _config.cancelToken && _config.cancelToken.unsubscribe(onCanceled);
      _config.signal && _config.signal.removeEventListener("abort", onCanceled);
    }
    let request = new XMLHttpRequest();
    request.open(_config.method.toUpperCase(), _config.url, true);
    request.timeout = _config.timeout;
    function onloadend() {
      if (!request) {
        return;
      }
      const responseHeaders = AxiosHeaders$1.from(
        "getAllResponseHeaders" in request && request.getAllResponseHeaders()
      );
      const responseData = !responseType || responseType === "text" || responseType === "json" ? request.responseText : request.response;
      const response = {
        data: responseData,
        status: request.status,
        statusText: request.statusText,
        headers: responseHeaders,
        config,
        request
      };
      settle(function _resolve(value) {
        resolve(value);
        done();
      }, function _reject(err) {
        reject(err);
        done();
      }, response);
      request = null;
    }
    if ("onloadend" in request) {
      request.onloadend = onloadend;
    } else {
      request.onreadystatechange = function handleLoad() {
        if (!request || request.readyState !== 4) {
          return;
        }
        if (request.status === 0 && !(request.responseURL && request.responseURL.indexOf("file:") === 0)) {
          return;
        }
        setTimeout(onloadend);
      };
    }
    request.onabort = function handleAbort() {
      if (!request) {
        return;
      }
      reject(new AxiosError$1("Request aborted", AxiosError$1.ECONNABORTED, config, request));
      request = null;
    };
    request.onerror = function handleError() {
      reject(new AxiosError$1("Network Error", AxiosError$1.ERR_NETWORK, config, request));
      request = null;
    };
    request.ontimeout = function handleTimeout() {
      let timeoutErrorMessage = _config.timeout ? "timeout of " + _config.timeout + "ms exceeded" : "timeout exceeded";
      const transitional2 = _config.transitional || transitionalDefaults;
      if (_config.timeoutErrorMessage) {
        timeoutErrorMessage = _config.timeoutErrorMessage;
      }
      reject(new AxiosError$1(
        timeoutErrorMessage,
        transitional2.clarifyTimeoutError ? AxiosError$1.ETIMEDOUT : AxiosError$1.ECONNABORTED,
        config,
        request
      ));
      request = null;
    };
    requestData === void 0 && requestHeaders.setContentType(null);
    if ("setRequestHeader" in request) {
      utils$1.forEach(requestHeaders.toJSON(), function setRequestHeader(val, key) {
        request.setRequestHeader(key, val);
      });
    }
    if (!utils$1.isUndefined(_config.withCredentials)) {
      request.withCredentials = !!_config.withCredentials;
    }
    if (responseType && responseType !== "json") {
      request.responseType = _config.responseType;
    }
    if (onDownloadProgress) {
      [downloadThrottled, flushDownload] = progressEventReducer(onDownloadProgress, true);
      request.addEventListener("progress", downloadThrottled);
    }
    if (onUploadProgress && request.upload) {
      [uploadThrottled, flushUpload] = progressEventReducer(onUploadProgress);
      request.upload.addEventListener("progress", uploadThrottled);
      request.upload.addEventListener("loadend", flushUpload);
    }
    if (_config.cancelToken || _config.signal) {
      onCanceled = (cancel) => {
        if (!request) {
          return;
        }
        reject(!cancel || cancel.type ? new CanceledError$1(null, config, request) : cancel);
        request.abort();
        request = null;
      };
      _config.cancelToken && _config.cancelToken.subscribe(onCanceled);
      if (_config.signal) {
        _config.signal.aborted ? onCanceled() : _config.signal.addEventListener("abort", onCanceled);
      }
    }
    const protocol = parseProtocol(_config.url);
    if (protocol && platform.protocols.indexOf(protocol) === -1) {
      reject(new AxiosError$1("Unsupported protocol " + protocol + ":", AxiosError$1.ERR_BAD_REQUEST, config));
      return;
    }
    request.send(requestData || null);
  });
};
const composeSignals = (signals, timeout) => {
  const { length } = signals = signals ? signals.filter(Boolean) : [];
  if (timeout || length) {
    let controller = new AbortController();
    let aborted;
    const onabort = function(reason) {
      if (!aborted) {
        aborted = true;
        unsubscribe();
        const err = reason instanceof Error ? reason : this.reason;
        controller.abort(err instanceof AxiosError$1 ? err : new CanceledError$1(err instanceof Error ? err.message : err));
      }
    };
    let timer = timeout && setTimeout(() => {
      timer = null;
      onabort(new AxiosError$1(`timeout ${timeout} of ms exceeded`, AxiosError$1.ETIMEDOUT));
    }, timeout);
    const unsubscribe = () => {
      if (signals) {
        timer && clearTimeout(timer);
        timer = null;
        signals.forEach((signal2) => {
          signal2.unsubscribe ? signal2.unsubscribe(onabort) : signal2.removeEventListener("abort", onabort);
        });
        signals = null;
      }
    };
    signals.forEach((signal2) => signal2.addEventListener("abort", onabort));
    const { signal } = controller;
    signal.unsubscribe = () => utils$1.asap(unsubscribe);
    return signal;
  }
};
const streamChunk = function* (chunk, chunkSize) {
  let len = chunk.byteLength;
  if (len < chunkSize) {
    yield chunk;
    return;
  }
  let pos = 0;
  let end;
  while (pos < len) {
    end = pos + chunkSize;
    yield chunk.slice(pos, end);
    pos = end;
  }
};
const readBytes = async function* (iterable, chunkSize) {
  for await (const chunk of readStream(iterable)) {
    yield* streamChunk(chunk, chunkSize);
  }
};
const readStream = async function* (stream) {
  if (stream[Symbol.asyncIterator]) {
    yield* stream;
    return;
  }
  const reader = stream.getReader();
  try {
    for (; ; ) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      yield value;
    }
  } finally {
    await reader.cancel();
  }
};
const trackStream = (stream, chunkSize, onProgress, onFinish) => {
  const iterator2 = readBytes(stream, chunkSize);
  let bytes = 0;
  let done;
  let _onFinish = (e) => {
    if (!done) {
      done = true;
      onFinish && onFinish(e);
    }
  };
  return new ReadableStream({
    async pull(controller) {
      try {
        const { done: done2, value } = await iterator2.next();
        if (done2) {
          _onFinish();
          controller.close();
          return;
        }
        let len = value.byteLength;
        if (onProgress) {
          let loadedBytes = bytes += len;
          onProgress(loadedBytes);
        }
        controller.enqueue(new Uint8Array(value));
      } catch (err) {
        _onFinish(err);
        throw err;
      }
    },
    cancel(reason) {
      _onFinish(reason);
      return iterator2.return();
    }
  }, {
    highWaterMark: 2
  });
};
const isFetchSupported = typeof fetch === "function" && typeof Request === "function" && typeof Response === "function";
const isReadableStreamSupported = isFetchSupported && typeof ReadableStream === "function";
const encodeText = isFetchSupported && (typeof TextEncoder === "function" ? /* @__PURE__ */ ((encoder) => (str) => encoder.encode(str))(new TextEncoder()) : async (str) => new Uint8Array(await new Response(str).arrayBuffer()));
const test = (fn, ...args) => {
  try {
    return !!fn(...args);
  } catch (e) {
    return false;
  }
};
const supportsRequestStream = isReadableStreamSupported && test(() => {
  let duplexAccessed = false;
  const hasContentType = new Request(platform.origin, {
    body: new ReadableStream(),
    method: "POST",
    get duplex() {
      duplexAccessed = true;
      return "half";
    }
  }).headers.has("Content-Type");
  return duplexAccessed && !hasContentType;
});
const DEFAULT_CHUNK_SIZE = 64 * 1024;
const supportsResponseStream = isReadableStreamSupported && test(() => utils$1.isReadableStream(new Response("").body));
const resolvers = {
  stream: supportsResponseStream && ((res) => res.body)
};
isFetchSupported && ((res) => {
  ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((type) => {
    !resolvers[type] && (resolvers[type] = utils$1.isFunction(res[type]) ? (res2) => res2[type]() : (_, config) => {
      throw new AxiosError$1(`Response type '${type}' is not supported`, AxiosError$1.ERR_NOT_SUPPORT, config);
    });
  });
})(new Response());
const getBodyLength = async (body) => {
  if (body == null) {
    return 0;
  }
  if (utils$1.isBlob(body)) {
    return body.size;
  }
  if (utils$1.isSpecCompliantForm(body)) {
    const _request = new Request(platform.origin, {
      method: "POST",
      body
    });
    return (await _request.arrayBuffer()).byteLength;
  }
  if (utils$1.isArrayBufferView(body) || utils$1.isArrayBuffer(body)) {
    return body.byteLength;
  }
  if (utils$1.isURLSearchParams(body)) {
    body = body + "";
  }
  if (utils$1.isString(body)) {
    return (await encodeText(body)).byteLength;
  }
};
const resolveBodyLength = async (headers, body) => {
  const length = utils$1.toFiniteNumber(headers.getContentLength());
  return length == null ? getBodyLength(body) : length;
};
const fetchAdapter = isFetchSupported && (async (config) => {
  let {
    url,
    method,
    data,
    signal,
    cancelToken,
    timeout,
    onDownloadProgress,
    onUploadProgress,
    responseType,
    headers,
    withCredentials = "same-origin",
    fetchOptions
  } = resolveConfig(config);
  responseType = responseType ? (responseType + "").toLowerCase() : "text";
  let composedSignal = composeSignals([signal, cancelToken && cancelToken.toAbortSignal()], timeout);
  let request;
  const unsubscribe = composedSignal && composedSignal.unsubscribe && (() => {
    composedSignal.unsubscribe();
  });
  let requestContentLength;
  try {
    if (onUploadProgress && supportsRequestStream && method !== "get" && method !== "head" && (requestContentLength = await resolveBodyLength(headers, data)) !== 0) {
      let _request = new Request(url, {
        method: "POST",
        body: data,
        duplex: "half"
      });
      let contentTypeHeader;
      if (utils$1.isFormData(data) && (contentTypeHeader = _request.headers.get("content-type"))) {
        headers.setContentType(contentTypeHeader);
      }
      if (_request.body) {
        const [onProgress, flush] = progressEventDecorator(
          requestContentLength,
          progressEventReducer(asyncDecorator(onUploadProgress))
        );
        data = trackStream(_request.body, DEFAULT_CHUNK_SIZE, onProgress, flush);
      }
    }
    if (!utils$1.isString(withCredentials)) {
      withCredentials = withCredentials ? "include" : "omit";
    }
    const isCredentialsSupported = "credentials" in Request.prototype;
    request = new Request(url, {
      ...fetchOptions,
      signal: composedSignal,
      method: method.toUpperCase(),
      headers: headers.normalize().toJSON(),
      body: data,
      duplex: "half",
      credentials: isCredentialsSupported ? withCredentials : void 0
    });
    let response = await fetch(request, fetchOptions);
    const isStreamResponse = supportsResponseStream && (responseType === "stream" || responseType === "response");
    if (supportsResponseStream && (onDownloadProgress || isStreamResponse && unsubscribe)) {
      const options = {};
      ["status", "statusText", "headers"].forEach((prop) => {
        options[prop] = response[prop];
      });
      const responseContentLength = utils$1.toFiniteNumber(response.headers.get("content-length"));
      const [onProgress, flush] = onDownloadProgress && progressEventDecorator(
        responseContentLength,
        progressEventReducer(asyncDecorator(onDownloadProgress), true)
      ) || [];
      response = new Response(
        trackStream(response.body, DEFAULT_CHUNK_SIZE, onProgress, () => {
          flush && flush();
          unsubscribe && unsubscribe();
        }),
        options
      );
    }
    responseType = responseType || "text";
    let responseData = await resolvers[utils$1.findKey(resolvers, responseType) || "text"](response, config);
    !isStreamResponse && unsubscribe && unsubscribe();
    return await new Promise((resolve, reject) => {
      settle(resolve, reject, {
        data: responseData,
        headers: AxiosHeaders$1.from(response.headers),
        status: response.status,
        statusText: response.statusText,
        config,
        request
      });
    });
  } catch (err) {
    unsubscribe && unsubscribe();
    if (err && err.name === "TypeError" && /Load failed|fetch/i.test(err.message)) {
      throw Object.assign(
        new AxiosError$1("Network Error", AxiosError$1.ERR_NETWORK, config, request),
        {
          cause: err.cause || err
        }
      );
    }
    throw AxiosError$1.from(err, err && err.code, config, request);
  }
});
const knownAdapters = {
  http: httpAdapter,
  xhr: xhrAdapter,
  fetch: fetchAdapter
};
utils$1.forEach(knownAdapters, (fn, value) => {
  if (fn) {
    try {
      Object.defineProperty(fn, "name", { value });
    } catch (e) {
    }
    Object.defineProperty(fn, "adapterName", { value });
  }
});
const renderReason = (reason) => `- ${reason}`;
const isResolvedHandle = (adapter) => utils$1.isFunction(adapter) || adapter === null || adapter === false;
const adapters = {
  getAdapter: (adapters2) => {
    adapters2 = utils$1.isArray(adapters2) ? adapters2 : [adapters2];
    const { length } = adapters2;
    let nameOrAdapter;
    let adapter;
    const rejectedReasons = {};
    for (let i = 0; i < length; i++) {
      nameOrAdapter = adapters2[i];
      let id;
      adapter = nameOrAdapter;
      if (!isResolvedHandle(nameOrAdapter)) {
        adapter = knownAdapters[(id = String(nameOrAdapter)).toLowerCase()];
        if (adapter === void 0) {
          throw new AxiosError$1(`Unknown adapter '${id}'`);
        }
      }
      if (adapter) {
        break;
      }
      rejectedReasons[id || "#" + i] = adapter;
    }
    if (!adapter) {
      const reasons = Object.entries(rejectedReasons).map(
        ([id, state]) => `adapter ${id} ` + (state === false ? "is not supported by the environment" : "is not available in the build")
      );
      let s = length ? reasons.length > 1 ? "since :\n" + reasons.map(renderReason).join("\n") : " " + renderReason(reasons[0]) : "as no adapter specified";
      throw new AxiosError$1(
        `There is no suitable adapter to dispatch the request ` + s,
        "ERR_NOT_SUPPORT"
      );
    }
    return adapter;
  },
  adapters: knownAdapters
};
function throwIfCancellationRequested(config) {
  if (config.cancelToken) {
    config.cancelToken.throwIfRequested();
  }
  if (config.signal && config.signal.aborted) {
    throw new CanceledError$1(null, config);
  }
}
function dispatchRequest(config) {
  throwIfCancellationRequested(config);
  config.headers = AxiosHeaders$1.from(config.headers);
  config.data = transformData.call(
    config,
    config.transformRequest
  );
  if (["post", "put", "patch"].indexOf(config.method) !== -1) {
    config.headers.setContentType("application/x-www-form-urlencoded", false);
  }
  const adapter = adapters.getAdapter(config.adapter || defaults.adapter);
  return adapter(config).then(function onAdapterResolution(response) {
    throwIfCancellationRequested(config);
    response.data = transformData.call(
      config,
      config.transformResponse,
      response
    );
    response.headers = AxiosHeaders$1.from(response.headers);
    return response;
  }, function onAdapterRejection(reason) {
    if (!isCancel$1(reason)) {
      throwIfCancellationRequested(config);
      if (reason && reason.response) {
        reason.response.data = transformData.call(
          config,
          config.transformResponse,
          reason.response
        );
        reason.response.headers = AxiosHeaders$1.from(reason.response.headers);
      }
    }
    return Promise.reject(reason);
  });
}
const VERSION$1 = "1.10.0";
const validators$1 = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((type, i) => {
  validators$1[type] = function validator2(thing) {
    return typeof thing === type || "a" + (i < 1 ? "n " : " ") + type;
  };
});
const deprecatedWarnings = {};
validators$1.transitional = function transitional(validator2, version, message) {
  function formatMessage(opt, desc) {
    return "[Axios v" + VERSION$1 + "] Transitional option '" + opt + "'" + desc + (message ? ". " + message : "");
  }
  return (value, opt, opts) => {
    if (validator2 === false) {
      throw new AxiosError$1(
        formatMessage(opt, " has been removed" + (version ? " in " + version : "")),
        AxiosError$1.ERR_DEPRECATED
      );
    }
    if (version && !deprecatedWarnings[opt]) {
      deprecatedWarnings[opt] = true;
      console.warn(
        formatMessage(
          opt,
          " has been deprecated since v" + version + " and will be removed in the near future"
        )
      );
    }
    return validator2 ? validator2(value, opt, opts) : true;
  };
};
validators$1.spelling = function spelling(correctSpelling) {
  return (value, opt) => {
    console.warn(`${opt} is likely a misspelling of ${correctSpelling}`);
    return true;
  };
};
function assertOptions(options, schema, allowUnknown) {
  if (typeof options !== "object") {
    throw new AxiosError$1("options must be an object", AxiosError$1.ERR_BAD_OPTION_VALUE);
  }
  const keys = Object.keys(options);
  let i = keys.length;
  while (i-- > 0) {
    const opt = keys[i];
    const validator2 = schema[opt];
    if (validator2) {
      const value = options[opt];
      const result = value === void 0 || validator2(value, opt, options);
      if (result !== true) {
        throw new AxiosError$1("option " + opt + " must be " + result, AxiosError$1.ERR_BAD_OPTION_VALUE);
      }
      continue;
    }
    if (allowUnknown !== true) {
      throw new AxiosError$1("Unknown option " + opt, AxiosError$1.ERR_BAD_OPTION);
    }
  }
}
const validator = {
  assertOptions,
  validators: validators$1
};
const validators = validator.validators;
let Axios$1 = class Axios {
  constructor(instanceConfig) {
    this.defaults = instanceConfig || {};
    this.interceptors = {
      request: new InterceptorManager(),
      response: new InterceptorManager()
    };
  }
  /**
   * Dispatch a request
   *
   * @param {String|Object} configOrUrl The config specific for this request (merged with this.defaults)
   * @param {?Object} config
   *
   * @returns {Promise} The Promise to be fulfilled
   */
  async request(configOrUrl, config) {
    try {
      return await this._request(configOrUrl, config);
    } catch (err) {
      if (err instanceof Error) {
        let dummy = {};
        Error.captureStackTrace ? Error.captureStackTrace(dummy) : dummy = new Error();
        const stack = dummy.stack ? dummy.stack.replace(/^.+\n/, "") : "";
        try {
          if (!err.stack) {
            err.stack = stack;
          } else if (stack && !String(err.stack).endsWith(stack.replace(/^.+\n.+\n/, ""))) {
            err.stack += "\n" + stack;
          }
        } catch (e) {
        }
      }
      throw err;
    }
  }
  _request(configOrUrl, config) {
    if (typeof configOrUrl === "string") {
      config = config || {};
      config.url = configOrUrl;
    } else {
      config = configOrUrl || {};
    }
    config = mergeConfig$1(this.defaults, config);
    const { transitional: transitional2, paramsSerializer, headers } = config;
    if (transitional2 !== void 0) {
      validator.assertOptions(transitional2, {
        silentJSONParsing: validators.transitional(validators.boolean),
        forcedJSONParsing: validators.transitional(validators.boolean),
        clarifyTimeoutError: validators.transitional(validators.boolean)
      }, false);
    }
    if (paramsSerializer != null) {
      if (utils$1.isFunction(paramsSerializer)) {
        config.paramsSerializer = {
          serialize: paramsSerializer
        };
      } else {
        validator.assertOptions(paramsSerializer, {
          encode: validators.function,
          serialize: validators.function
        }, true);
      }
    }
    if (config.allowAbsoluteUrls !== void 0) ;
    else if (this.defaults.allowAbsoluteUrls !== void 0) {
      config.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls;
    } else {
      config.allowAbsoluteUrls = true;
    }
    validator.assertOptions(config, {
      baseUrl: validators.spelling("baseURL"),
      withXsrfToken: validators.spelling("withXSRFToken")
    }, true);
    config.method = (config.method || this.defaults.method || "get").toLowerCase();
    let contextHeaders = headers && utils$1.merge(
      headers.common,
      headers[config.method]
    );
    headers && utils$1.forEach(
      ["delete", "get", "head", "post", "put", "patch", "common"],
      (method) => {
        delete headers[method];
      }
    );
    config.headers = AxiosHeaders$1.concat(contextHeaders, headers);
    const requestInterceptorChain = [];
    let synchronousRequestInterceptors = true;
    this.interceptors.request.forEach(function unshiftRequestInterceptors(interceptor) {
      if (typeof interceptor.runWhen === "function" && interceptor.runWhen(config) === false) {
        return;
      }
      synchronousRequestInterceptors = synchronousRequestInterceptors && interceptor.synchronous;
      requestInterceptorChain.unshift(interceptor.fulfilled, interceptor.rejected);
    });
    const responseInterceptorChain = [];
    this.interceptors.response.forEach(function pushResponseInterceptors(interceptor) {
      responseInterceptorChain.push(interceptor.fulfilled, interceptor.rejected);
    });
    let promise;
    let i = 0;
    let len;
    if (!synchronousRequestInterceptors) {
      const chain = [dispatchRequest.bind(this), void 0];
      chain.unshift.apply(chain, requestInterceptorChain);
      chain.push.apply(chain, responseInterceptorChain);
      len = chain.length;
      promise = Promise.resolve(config);
      while (i < len) {
        promise = promise.then(chain[i++], chain[i++]);
      }
      return promise;
    }
    len = requestInterceptorChain.length;
    let newConfig = config;
    i = 0;
    while (i < len) {
      const onFulfilled = requestInterceptorChain[i++];
      const onRejected = requestInterceptorChain[i++];
      try {
        newConfig = onFulfilled(newConfig);
      } catch (error) {
        onRejected.call(this, error);
        break;
      }
    }
    try {
      promise = dispatchRequest.call(this, newConfig);
    } catch (error) {
      return Promise.reject(error);
    }
    i = 0;
    len = responseInterceptorChain.length;
    while (i < len) {
      promise = promise.then(responseInterceptorChain[i++], responseInterceptorChain[i++]);
    }
    return promise;
  }
  getUri(config) {
    config = mergeConfig$1(this.defaults, config);
    const fullPath = buildFullPath(config.baseURL, config.url, config.allowAbsoluteUrls);
    return buildURL(fullPath, config.params, config.paramsSerializer);
  }
};
utils$1.forEach(["delete", "get", "head", "options"], function forEachMethodNoData(method) {
  Axios$1.prototype[method] = function(url, config) {
    return this.request(mergeConfig$1(config || {}, {
      method,
      url,
      data: (config || {}).data
    }));
  };
});
utils$1.forEach(["post", "put", "patch"], function forEachMethodWithData(method) {
  function generateHTTPMethod(isForm) {
    return function httpMethod(url, data, config) {
      return this.request(mergeConfig$1(config || {}, {
        method,
        headers: isForm ? {
          "Content-Type": "multipart/form-data"
        } : {},
        url,
        data
      }));
    };
  }
  Axios$1.prototype[method] = generateHTTPMethod();
  Axios$1.prototype[method + "Form"] = generateHTTPMethod(true);
});
let CancelToken$1 = class CancelToken {
  constructor(executor) {
    if (typeof executor !== "function") {
      throw new TypeError("executor must be a function.");
    }
    let resolvePromise;
    this.promise = new Promise(function promiseExecutor(resolve) {
      resolvePromise = resolve;
    });
    const token = this;
    this.promise.then((cancel) => {
      if (!token._listeners) return;
      let i = token._listeners.length;
      while (i-- > 0) {
        token._listeners[i](cancel);
      }
      token._listeners = null;
    });
    this.promise.then = (onfulfilled) => {
      let _resolve;
      const promise = new Promise((resolve) => {
        token.subscribe(resolve);
        _resolve = resolve;
      }).then(onfulfilled);
      promise.cancel = function reject() {
        token.unsubscribe(_resolve);
      };
      return promise;
    };
    executor(function cancel(message, config, request) {
      if (token.reason) {
        return;
      }
      token.reason = new CanceledError$1(message, config, request);
      resolvePromise(token.reason);
    });
  }
  /**
   * Throws a `CanceledError` if cancellation has been requested.
   */
  throwIfRequested() {
    if (this.reason) {
      throw this.reason;
    }
  }
  /**
   * Subscribe to the cancel signal
   */
  subscribe(listener) {
    if (this.reason) {
      listener(this.reason);
      return;
    }
    if (this._listeners) {
      this._listeners.push(listener);
    } else {
      this._listeners = [listener];
    }
  }
  /**
   * Unsubscribe from the cancel signal
   */
  unsubscribe(listener) {
    if (!this._listeners) {
      return;
    }
    const index = this._listeners.indexOf(listener);
    if (index !== -1) {
      this._listeners.splice(index, 1);
    }
  }
  toAbortSignal() {
    const controller = new AbortController();
    const abort = (err) => {
      controller.abort(err);
    };
    this.subscribe(abort);
    controller.signal.unsubscribe = () => this.unsubscribe(abort);
    return controller.signal;
  }
  /**
   * Returns an object that contains a new `CancelToken` and a function that, when called,
   * cancels the `CancelToken`.
   */
  static source() {
    let cancel;
    const token = new CancelToken(function executor(c) {
      cancel = c;
    });
    return {
      token,
      cancel
    };
  }
};
function spread$1(callback) {
  return function wrap(arr) {
    return callback.apply(null, arr);
  };
}
function isAxiosError$1(payload) {
  return utils$1.isObject(payload) && payload.isAxiosError === true;
}
const HttpStatusCode$1 = {
  Continue: 100,
  SwitchingProtocols: 101,
  Processing: 102,
  EarlyHints: 103,
  Ok: 200,
  Created: 201,
  Accepted: 202,
  NonAuthoritativeInformation: 203,
  NoContent: 204,
  ResetContent: 205,
  PartialContent: 206,
  MultiStatus: 207,
  AlreadyReported: 208,
  ImUsed: 226,
  MultipleChoices: 300,
  MovedPermanently: 301,
  Found: 302,
  SeeOther: 303,
  NotModified: 304,
  UseProxy: 305,
  Unused: 306,
  TemporaryRedirect: 307,
  PermanentRedirect: 308,
  BadRequest: 400,
  Unauthorized: 401,
  PaymentRequired: 402,
  Forbidden: 403,
  NotFound: 404,
  MethodNotAllowed: 405,
  NotAcceptable: 406,
  ProxyAuthenticationRequired: 407,
  RequestTimeout: 408,
  Conflict: 409,
  Gone: 410,
  LengthRequired: 411,
  PreconditionFailed: 412,
  PayloadTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  UnprocessableEntity: 422,
  Locked: 423,
  FailedDependency: 424,
  TooEarly: 425,
  UpgradeRequired: 426,
  PreconditionRequired: 428,
  TooManyRequests: 429,
  RequestHeaderFieldsTooLarge: 431,
  UnavailableForLegalReasons: 451,
  InternalServerError: 500,
  NotImplemented: 501,
  BadGateway: 502,
  ServiceUnavailable: 503,
  GatewayTimeout: 504,
  HttpVersionNotSupported: 505,
  VariantAlsoNegotiates: 506,
  InsufficientStorage: 507,
  LoopDetected: 508,
  NotExtended: 510,
  NetworkAuthenticationRequired: 511
};
Object.entries(HttpStatusCode$1).forEach(([key, value]) => {
  HttpStatusCode$1[value] = key;
});
function createInstance(defaultConfig) {
  const context = new Axios$1(defaultConfig);
  const instance = bind(Axios$1.prototype.request, context);
  utils$1.extend(instance, Axios$1.prototype, context, { allOwnKeys: true });
  utils$1.extend(instance, context, null, { allOwnKeys: true });
  instance.create = function create(instanceConfig) {
    return createInstance(mergeConfig$1(defaultConfig, instanceConfig));
  };
  return instance;
}
const axios = createInstance(defaults);
axios.Axios = Axios$1;
axios.CanceledError = CanceledError$1;
axios.CancelToken = CancelToken$1;
axios.isCancel = isCancel$1;
axios.VERSION = VERSION$1;
axios.toFormData = toFormData$1;
axios.AxiosError = AxiosError$1;
axios.Cancel = axios.CanceledError;
axios.all = function all(promises) {
  return Promise.all(promises);
};
axios.spread = spread$1;
axios.isAxiosError = isAxiosError$1;
axios.mergeConfig = mergeConfig$1;
axios.AxiosHeaders = AxiosHeaders$1;
axios.formToJSON = (thing) => formDataToJSON(utils$1.isHTMLForm(thing) ? new FormData(thing) : thing);
axios.getAdapter = adapters.getAdapter;
axios.HttpStatusCode = HttpStatusCode$1;
axios.default = axios;
const {
  Axios: Axios2,
  AxiosError,
  CanceledError,
  isCancel,
  CancelToken: CancelToken2,
  VERSION,
  all: all2,
  Cancel,
  isAxiosError,
  spread,
  toFormData,
  AxiosHeaders: AxiosHeaders2,
  HttpStatusCode,
  formToJSON,
  getAdapter,
  mergeConfig
} = axios;
/*!
 * pinia v3.0.3
 * (c) 2025 Eduardo San Martin Morote
 * @license MIT
 */
const piniaSymbol = (
  /* istanbul ignore next */
  Symbol()
);
var MutationType;
(function(MutationType2) {
  MutationType2["direct"] = "direct";
  MutationType2["patchObject"] = "patch object";
  MutationType2["patchFunction"] = "patch function";
})(MutationType || (MutationType = {}));
function createPinia() {
  const scope = effectScope(true);
  const state = scope.run(() => ref({}));
  let _p = [];
  let toBeInstalled = [];
  const pinia2 = markRaw({
    install(app2) {
      pinia2._a = app2;
      app2.provide(piniaSymbol, pinia2);
      app2.config.globalProperties.$pinia = pinia2;
      toBeInstalled.forEach((plugin) => _p.push(plugin));
      toBeInstalled = [];
    },
    use(plugin) {
      if (!this._a) {
        toBeInstalled.push(plugin);
      } else {
        _p.push(plugin);
      }
      return this;
    },
    _p,
    // it's actually undefined here
    // @ts-expect-error
    _a: null,
    _e: scope,
    _s: /* @__PURE__ */ new Map(),
    state
  });
  return pinia2;
}
const isLoading = ref(false);
const loadingMessage = ref("");
const loadingProgress = ref(0);
const loadingErrors = ref([]);
const activeLoaders = /* @__PURE__ */ new Set();
function createLoader(id, { message = "Loading...", progress = 0 } = {}) {
  if (activeLoaders.has(id)) {
    console.warn(`Loader with id "${id}" already exists`);
  }
  activeLoaders.add(id);
  isLoading.value = true;
  loadingMessage.value = message;
  loadingProgress.value = progress;
  return {
    /**
     * Update the loading state
     * @param {Object} update - Update object
     * @param {string} [update.message] - New loading message
     * @param {number} [update.progress] - New progress value (0-100)
     */
    update({ message: message2, progress: progress2 }) {
      if (message2 !== void 0) loadingMessage.value = message2;
      if (progress2 !== void 0) loadingProgress.value = Math.max(0, Math.min(100, progress2));
    },
    /**
     * Complete the loading state
     */
    complete() {
      loadingProgress.value = 100;
      this.remove();
    },
    /**
     * Report an error
     * @param {Error|string} error - Error object or message
     */
    error(error) {
      const errorObj = typeof error === "string" ? new Error(error) : error;
      loadingErrors.value = [...loadingErrors.value, errorObj];
      this.remove();
    },
    /**
     * Remove this loader
     */
    remove() {
      activeLoaders.delete(id);
      if (activeLoaders.size === 0) {
        resetLoadingState();
      } else {
        const lastLoader = Array.from(activeLoaders).pop();
        loadingMessage.value = lastLoader || "Loading...";
      }
    }
  };
}
function resetLoadingState() {
  isLoading.value = false;
  loadingMessage.value = "";
  loadingProgress.value = 0;
  activeLoaders.clear();
}
function useLoadingState() {
  return {
    isLoading: readonly(isLoading),
    message: readonly(loadingMessage),
    progress: readonly(loadingProgress),
    errors: readonly(loadingErrors),
    hasErrors: loadingErrors.value.length > 0
  };
}
var bootstrap_bundle_min$1 = { exports: {} };
/*!
  * Bootstrap v5.3.7 (https://getbootstrap.com/)
  * Copyright 2011-2025 The Bootstrap Authors (https://github.com/twbs/bootstrap/graphs/contributors)
  * Licensed under MIT (https://github.com/twbs/bootstrap/blob/main/LICENSE)
  */
var bootstrap_bundle_min = bootstrap_bundle_min$1.exports;
var hasRequiredBootstrap_bundle_min;
function requireBootstrap_bundle_min() {
  if (hasRequiredBootstrap_bundle_min) return bootstrap_bundle_min$1.exports;
  hasRequiredBootstrap_bundle_min = 1;
  (function(module, exports) {
    !function(t, e) {
      module.exports = e();
    }(bootstrap_bundle_min, function() {
      const t = /* @__PURE__ */ new Map(), e = { set(e2, i2, n2) {
        t.has(e2) || t.set(e2, /* @__PURE__ */ new Map());
        const s2 = t.get(e2);
        s2.has(i2) || 0 === s2.size ? s2.set(i2, n2) : console.error(`Bootstrap doesn't allow more than one instance per element. Bound instance: ${Array.from(s2.keys())[0]}.`);
      }, get: (e2, i2) => t.has(e2) && t.get(e2).get(i2) || null, remove(e2, i2) {
        if (!t.has(e2)) return;
        const n2 = t.get(e2);
        n2.delete(i2), 0 === n2.size && t.delete(e2);
      } }, i = "transitionend", n = (t2) => (t2 && window.CSS && window.CSS.escape && (t2 = t2.replace(/#([^\s"#']+)/g, (t3, e2) => `#${CSS.escape(e2)}`)), t2), s = (t2) => {
        t2.dispatchEvent(new Event(i));
      }, o = (t2) => !(!t2 || "object" != typeof t2) && (void 0 !== t2.jquery && (t2 = t2[0]), void 0 !== t2.nodeType), r = (t2) => o(t2) ? t2.jquery ? t2[0] : t2 : "string" == typeof t2 && t2.length > 0 ? document.querySelector(n(t2)) : null, a = (t2) => {
        if (!o(t2) || 0 === t2.getClientRects().length) return false;
        const e2 = "visible" === getComputedStyle(t2).getPropertyValue("visibility"), i2 = t2.closest("details:not([open])");
        if (!i2) return e2;
        if (i2 !== t2) {
          const e3 = t2.closest("summary");
          if (e3 && e3.parentNode !== i2) return false;
          if (null === e3) return false;
        }
        return e2;
      }, l = (t2) => !t2 || t2.nodeType !== Node.ELEMENT_NODE || !!t2.classList.contains("disabled") || (void 0 !== t2.disabled ? t2.disabled : t2.hasAttribute("disabled") && "false" !== t2.getAttribute("disabled")), c = (t2) => {
        if (!document.documentElement.attachShadow) return null;
        if ("function" == typeof t2.getRootNode) {
          const e2 = t2.getRootNode();
          return e2 instanceof ShadowRoot ? e2 : null;
        }
        return t2 instanceof ShadowRoot ? t2 : t2.parentNode ? c(t2.parentNode) : null;
      }, h = () => {
      }, d = (t2) => {
        t2.offsetHeight;
      }, u = () => window.jQuery && !document.body.hasAttribute("data-bs-no-jquery") ? window.jQuery : null, f = [], p = () => "rtl" === document.documentElement.dir, m = (t2) => {
        var e2;
        e2 = () => {
          const e3 = u();
          if (e3) {
            const i2 = t2.NAME, n2 = e3.fn[i2];
            e3.fn[i2] = t2.jQueryInterface, e3.fn[i2].Constructor = t2, e3.fn[i2].noConflict = () => (e3.fn[i2] = n2, t2.jQueryInterface);
          }
        }, "loading" === document.readyState ? (f.length || document.addEventListener("DOMContentLoaded", () => {
          for (const t3 of f) t3();
        }), f.push(e2)) : e2();
      }, g = (t2, e2 = [], i2 = t2) => "function" == typeof t2 ? t2.call(...e2) : i2, _ = (t2, e2, n2 = true) => {
        if (!n2) return void g(t2);
        const o2 = ((t3) => {
          if (!t3) return 0;
          let { transitionDuration: e3, transitionDelay: i2 } = window.getComputedStyle(t3);
          const n3 = Number.parseFloat(e3), s2 = Number.parseFloat(i2);
          return n3 || s2 ? (e3 = e3.split(",")[0], i2 = i2.split(",")[0], 1e3 * (Number.parseFloat(e3) + Number.parseFloat(i2))) : 0;
        })(e2) + 5;
        let r2 = false;
        const a2 = ({ target: n3 }) => {
          n3 === e2 && (r2 = true, e2.removeEventListener(i, a2), g(t2));
        };
        e2.addEventListener(i, a2), setTimeout(() => {
          r2 || s(e2);
        }, o2);
      }, b = (t2, e2, i2, n2) => {
        const s2 = t2.length;
        let o2 = t2.indexOf(e2);
        return -1 === o2 ? !i2 && n2 ? t2[s2 - 1] : t2[0] : (o2 += i2 ? 1 : -1, n2 && (o2 = (o2 + s2) % s2), t2[Math.max(0, Math.min(o2, s2 - 1))]);
      }, v = /[^.]*(?=\..*)\.|.*/, y = /\..*/, w = /::\d+$/, A = {};
      let E = 1;
      const T = { mouseenter: "mouseover", mouseleave: "mouseout" }, C = /* @__PURE__ */ new Set(["click", "dblclick", "mouseup", "mousedown", "contextmenu", "mousewheel", "DOMMouseScroll", "mouseover", "mouseout", "mousemove", "selectstart", "selectend", "keydown", "keypress", "keyup", "orientationchange", "touchstart", "touchmove", "touchend", "touchcancel", "pointerdown", "pointermove", "pointerup", "pointerleave", "pointercancel", "gesturestart", "gesturechange", "gestureend", "focus", "blur", "change", "reset", "select", "submit", "focusin", "focusout", "load", "unload", "beforeunload", "resize", "move", "DOMContentLoaded", "readystatechange", "error", "abort", "scroll"]);
      function O(t2, e2) {
        return e2 && `${e2}::${E++}` || t2.uidEvent || E++;
      }
      function x(t2) {
        const e2 = O(t2);
        return t2.uidEvent = e2, A[e2] = A[e2] || {}, A[e2];
      }
      function k(t2, e2, i2 = null) {
        return Object.values(t2).find((t3) => t3.callable === e2 && t3.delegationSelector === i2);
      }
      function L(t2, e2, i2) {
        const n2 = "string" == typeof e2, s2 = n2 ? i2 : e2 || i2;
        let o2 = I(t2);
        return C.has(o2) || (o2 = t2), [n2, s2, o2];
      }
      function S(t2, e2, i2, n2, s2) {
        if ("string" != typeof e2 || !t2) return;
        let [o2, r2, a2] = L(e2, i2, n2);
        if (e2 in T) {
          const t3 = (t4) => function(e3) {
            if (!e3.relatedTarget || e3.relatedTarget !== e3.delegateTarget && !e3.delegateTarget.contains(e3.relatedTarget)) return t4.call(this, e3);
          };
          r2 = t3(r2);
        }
        const l2 = x(t2), c2 = l2[a2] || (l2[a2] = {}), h2 = k(c2, r2, o2 ? i2 : null);
        if (h2) return void (h2.oneOff = h2.oneOff && s2);
        const d2 = O(r2, e2.replace(v, "")), u2 = o2 ? /* @__PURE__ */ function(t3, e3, i3) {
          return function n3(s3) {
            const o3 = t3.querySelectorAll(e3);
            for (let { target: r3 } = s3; r3 && r3 !== this; r3 = r3.parentNode) for (const a3 of o3) if (a3 === r3) return P(s3, { delegateTarget: r3 }), n3.oneOff && N.off(t3, s3.type, e3, i3), i3.apply(r3, [s3]);
          };
        }(t2, i2, r2) : /* @__PURE__ */ function(t3, e3) {
          return function i3(n3) {
            return P(n3, { delegateTarget: t3 }), i3.oneOff && N.off(t3, n3.type, e3), e3.apply(t3, [n3]);
          };
        }(t2, r2);
        u2.delegationSelector = o2 ? i2 : null, u2.callable = r2, u2.oneOff = s2, u2.uidEvent = d2, c2[d2] = u2, t2.addEventListener(a2, u2, o2);
      }
      function D(t2, e2, i2, n2, s2) {
        const o2 = k(e2[i2], n2, s2);
        o2 && (t2.removeEventListener(i2, o2, Boolean(s2)), delete e2[i2][o2.uidEvent]);
      }
      function $(t2, e2, i2, n2) {
        const s2 = e2[i2] || {};
        for (const [o2, r2] of Object.entries(s2)) o2.includes(n2) && D(t2, e2, i2, r2.callable, r2.delegationSelector);
      }
      function I(t2) {
        return t2 = t2.replace(y, ""), T[t2] || t2;
      }
      const N = { on(t2, e2, i2, n2) {
        S(t2, e2, i2, n2, false);
      }, one(t2, e2, i2, n2) {
        S(t2, e2, i2, n2, true);
      }, off(t2, e2, i2, n2) {
        if ("string" != typeof e2 || !t2) return;
        const [s2, o2, r2] = L(e2, i2, n2), a2 = r2 !== e2, l2 = x(t2), c2 = l2[r2] || {}, h2 = e2.startsWith(".");
        if (void 0 === o2) {
          if (h2) for (const i3 of Object.keys(l2)) $(t2, l2, i3, e2.slice(1));
          for (const [i3, n3] of Object.entries(c2)) {
            const s3 = i3.replace(w, "");
            a2 && !e2.includes(s3) || D(t2, l2, r2, n3.callable, n3.delegationSelector);
          }
        } else {
          if (!Object.keys(c2).length) return;
          D(t2, l2, r2, o2, s2 ? i2 : null);
        }
      }, trigger(t2, e2, i2) {
        if ("string" != typeof e2 || !t2) return null;
        const n2 = u();
        let s2 = null, o2 = true, r2 = true, a2 = false;
        e2 !== I(e2) && n2 && (s2 = n2.Event(e2, i2), n2(t2).trigger(s2), o2 = !s2.isPropagationStopped(), r2 = !s2.isImmediatePropagationStopped(), a2 = s2.isDefaultPrevented());
        const l2 = P(new Event(e2, { bubbles: o2, cancelable: true }), i2);
        return a2 && l2.preventDefault(), r2 && t2.dispatchEvent(l2), l2.defaultPrevented && s2 && s2.preventDefault(), l2;
      } };
      function P(t2, e2 = {}) {
        for (const [i2, n2] of Object.entries(e2)) try {
          t2[i2] = n2;
        } catch (e3) {
          Object.defineProperty(t2, i2, { configurable: true, get: () => n2 });
        }
        return t2;
      }
      function j(t2) {
        if ("true" === t2) return true;
        if ("false" === t2) return false;
        if (t2 === Number(t2).toString()) return Number(t2);
        if ("" === t2 || "null" === t2) return null;
        if ("string" != typeof t2) return t2;
        try {
          return JSON.parse(decodeURIComponent(t2));
        } catch (e2) {
          return t2;
        }
      }
      function M(t2) {
        return t2.replace(/[A-Z]/g, (t3) => `-${t3.toLowerCase()}`);
      }
      const F = { setDataAttribute(t2, e2, i2) {
        t2.setAttribute(`data-bs-${M(e2)}`, i2);
      }, removeDataAttribute(t2, e2) {
        t2.removeAttribute(`data-bs-${M(e2)}`);
      }, getDataAttributes(t2) {
        if (!t2) return {};
        const e2 = {}, i2 = Object.keys(t2.dataset).filter((t3) => t3.startsWith("bs") && !t3.startsWith("bsConfig"));
        for (const n2 of i2) {
          let i3 = n2.replace(/^bs/, "");
          i3 = i3.charAt(0).toLowerCase() + i3.slice(1), e2[i3] = j(t2.dataset[n2]);
        }
        return e2;
      }, getDataAttribute: (t2, e2) => j(t2.getAttribute(`data-bs-${M(e2)}`)) };
      class H {
        static get Default() {
          return {};
        }
        static get DefaultType() {
          return {};
        }
        static get NAME() {
          throw new Error('You have to implement the static method "NAME", for each component!');
        }
        _getConfig(t2) {
          return t2 = this._mergeConfigObj(t2), t2 = this._configAfterMerge(t2), this._typeCheckConfig(t2), t2;
        }
        _configAfterMerge(t2) {
          return t2;
        }
        _mergeConfigObj(t2, e2) {
          const i2 = o(e2) ? F.getDataAttribute(e2, "config") : {};
          return { ...this.constructor.Default, ..."object" == typeof i2 ? i2 : {}, ...o(e2) ? F.getDataAttributes(e2) : {}, ..."object" == typeof t2 ? t2 : {} };
        }
        _typeCheckConfig(t2, e2 = this.constructor.DefaultType) {
          for (const [n2, s2] of Object.entries(e2)) {
            const e3 = t2[n2], r2 = o(e3) ? "element" : null == (i2 = e3) ? `${i2}` : Object.prototype.toString.call(i2).match(/\s([a-z]+)/i)[1].toLowerCase();
            if (!new RegExp(s2).test(r2)) throw new TypeError(`${this.constructor.NAME.toUpperCase()}: Option "${n2}" provided type "${r2}" but expected type "${s2}".`);
          }
          var i2;
        }
      }
      class W extends H {
        constructor(t2, i2) {
          super(), (t2 = r(t2)) && (this._element = t2, this._config = this._getConfig(i2), e.set(this._element, this.constructor.DATA_KEY, this));
        }
        dispose() {
          e.remove(this._element, this.constructor.DATA_KEY), N.off(this._element, this.constructor.EVENT_KEY);
          for (const t2 of Object.getOwnPropertyNames(this)) this[t2] = null;
        }
        _queueCallback(t2, e2, i2 = true) {
          _(t2, e2, i2);
        }
        _getConfig(t2) {
          return t2 = this._mergeConfigObj(t2, this._element), t2 = this._configAfterMerge(t2), this._typeCheckConfig(t2), t2;
        }
        static getInstance(t2) {
          return e.get(r(t2), this.DATA_KEY);
        }
        static getOrCreateInstance(t2, e2 = {}) {
          return this.getInstance(t2) || new this(t2, "object" == typeof e2 ? e2 : null);
        }
        static get VERSION() {
          return "5.3.7";
        }
        static get DATA_KEY() {
          return `bs.${this.NAME}`;
        }
        static get EVENT_KEY() {
          return `.${this.DATA_KEY}`;
        }
        static eventName(t2) {
          return `${t2}${this.EVENT_KEY}`;
        }
      }
      const B = (t2) => {
        let e2 = t2.getAttribute("data-bs-target");
        if (!e2 || "#" === e2) {
          let i2 = t2.getAttribute("href");
          if (!i2 || !i2.includes("#") && !i2.startsWith(".")) return null;
          i2.includes("#") && !i2.startsWith("#") && (i2 = `#${i2.split("#")[1]}`), e2 = i2 && "#" !== i2 ? i2.trim() : null;
        }
        return e2 ? e2.split(",").map((t3) => n(t3)).join(",") : null;
      }, z = { find: (t2, e2 = document.documentElement) => [].concat(...Element.prototype.querySelectorAll.call(e2, t2)), findOne: (t2, e2 = document.documentElement) => Element.prototype.querySelector.call(e2, t2), children: (t2, e2) => [].concat(...t2.children).filter((t3) => t3.matches(e2)), parents(t2, e2) {
        const i2 = [];
        let n2 = t2.parentNode.closest(e2);
        for (; n2; ) i2.push(n2), n2 = n2.parentNode.closest(e2);
        return i2;
      }, prev(t2, e2) {
        let i2 = t2.previousElementSibling;
        for (; i2; ) {
          if (i2.matches(e2)) return [i2];
          i2 = i2.previousElementSibling;
        }
        return [];
      }, next(t2, e2) {
        let i2 = t2.nextElementSibling;
        for (; i2; ) {
          if (i2.matches(e2)) return [i2];
          i2 = i2.nextElementSibling;
        }
        return [];
      }, focusableChildren(t2) {
        const e2 = ["a", "button", "input", "textarea", "select", "details", "[tabindex]", '[contenteditable="true"]'].map((t3) => `${t3}:not([tabindex^="-"])`).join(",");
        return this.find(e2, t2).filter((t3) => !l(t3) && a(t3));
      }, getSelectorFromElement(t2) {
        const e2 = B(t2);
        return e2 && z.findOne(e2) ? e2 : null;
      }, getElementFromSelector(t2) {
        const e2 = B(t2);
        return e2 ? z.findOne(e2) : null;
      }, getMultipleElementsFromSelector(t2) {
        const e2 = B(t2);
        return e2 ? z.find(e2) : [];
      } }, R = (t2, e2 = "hide") => {
        const i2 = `click.dismiss${t2.EVENT_KEY}`, n2 = t2.NAME;
        N.on(document, i2, `[data-bs-dismiss="${n2}"]`, function(i3) {
          if (["A", "AREA"].includes(this.tagName) && i3.preventDefault(), l(this)) return;
          const s2 = z.getElementFromSelector(this) || this.closest(`.${n2}`);
          t2.getOrCreateInstance(s2)[e2]();
        });
      }, q = ".bs.alert", V = `close${q}`, K = `closed${q}`;
      class Q extends W {
        static get NAME() {
          return "alert";
        }
        close() {
          if (N.trigger(this._element, V).defaultPrevented) return;
          this._element.classList.remove("show");
          const t2 = this._element.classList.contains("fade");
          this._queueCallback(() => this._destroyElement(), this._element, t2);
        }
        _destroyElement() {
          this._element.remove(), N.trigger(this._element, K), this.dispose();
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Q.getOrCreateInstance(this);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2] || t2.startsWith("_") || "constructor" === t2) throw new TypeError(`No method named "${t2}"`);
              e2[t2](this);
            }
          });
        }
      }
      R(Q, "close"), m(Q);
      const X = '[data-bs-toggle="button"]';
      class Y extends W {
        static get NAME() {
          return "button";
        }
        toggle() {
          this._element.setAttribute("aria-pressed", this._element.classList.toggle("active"));
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Y.getOrCreateInstance(this);
            "toggle" === t2 && e2[t2]();
          });
        }
      }
      N.on(document, "click.bs.button.data-api", X, (t2) => {
        t2.preventDefault();
        const e2 = t2.target.closest(X);
        Y.getOrCreateInstance(e2).toggle();
      }), m(Y);
      const U = ".bs.swipe", G = `touchstart${U}`, J = `touchmove${U}`, Z = `touchend${U}`, tt = `pointerdown${U}`, et = `pointerup${U}`, it = { endCallback: null, leftCallback: null, rightCallback: null }, nt = { endCallback: "(function|null)", leftCallback: "(function|null)", rightCallback: "(function|null)" };
      class st extends H {
        constructor(t2, e2) {
          super(), this._element = t2, t2 && st.isSupported() && (this._config = this._getConfig(e2), this._deltaX = 0, this._supportPointerEvents = Boolean(window.PointerEvent), this._initEvents());
        }
        static get Default() {
          return it;
        }
        static get DefaultType() {
          return nt;
        }
        static get NAME() {
          return "swipe";
        }
        dispose() {
          N.off(this._element, U);
        }
        _start(t2) {
          this._supportPointerEvents ? this._eventIsPointerPenTouch(t2) && (this._deltaX = t2.clientX) : this._deltaX = t2.touches[0].clientX;
        }
        _end(t2) {
          this._eventIsPointerPenTouch(t2) && (this._deltaX = t2.clientX - this._deltaX), this._handleSwipe(), g(this._config.endCallback);
        }
        _move(t2) {
          this._deltaX = t2.touches && t2.touches.length > 1 ? 0 : t2.touches[0].clientX - this._deltaX;
        }
        _handleSwipe() {
          const t2 = Math.abs(this._deltaX);
          if (t2 <= 40) return;
          const e2 = t2 / this._deltaX;
          this._deltaX = 0, e2 && g(e2 > 0 ? this._config.rightCallback : this._config.leftCallback);
        }
        _initEvents() {
          this._supportPointerEvents ? (N.on(this._element, tt, (t2) => this._start(t2)), N.on(this._element, et, (t2) => this._end(t2)), this._element.classList.add("pointer-event")) : (N.on(this._element, G, (t2) => this._start(t2)), N.on(this._element, J, (t2) => this._move(t2)), N.on(this._element, Z, (t2) => this._end(t2)));
        }
        _eventIsPointerPenTouch(t2) {
          return this._supportPointerEvents && ("pen" === t2.pointerType || "touch" === t2.pointerType);
        }
        static isSupported() {
          return "ontouchstart" in document.documentElement || navigator.maxTouchPoints > 0;
        }
      }
      const ot = ".bs.carousel", rt = ".data-api", at = "ArrowLeft", lt = "ArrowRight", ct = "next", ht = "prev", dt = "left", ut = "right", ft = `slide${ot}`, pt = `slid${ot}`, mt = `keydown${ot}`, gt = `mouseenter${ot}`, _t = `mouseleave${ot}`, bt = `dragstart${ot}`, vt = `load${ot}${rt}`, yt = `click${ot}${rt}`, wt = "carousel", At = "active", Et = ".active", Tt = ".carousel-item", Ct = Et + Tt, Ot = { [at]: ut, [lt]: dt }, xt = { interval: 5e3, keyboard: true, pause: "hover", ride: false, touch: true, wrap: true }, kt = { interval: "(number|boolean)", keyboard: "boolean", pause: "(string|boolean)", ride: "(boolean|string)", touch: "boolean", wrap: "boolean" };
      class Lt extends W {
        constructor(t2, e2) {
          super(t2, e2), this._interval = null, this._activeElement = null, this._isSliding = false, this.touchTimeout = null, this._swipeHelper = null, this._indicatorsElement = z.findOne(".carousel-indicators", this._element), this._addEventListeners(), this._config.ride === wt && this.cycle();
        }
        static get Default() {
          return xt;
        }
        static get DefaultType() {
          return kt;
        }
        static get NAME() {
          return "carousel";
        }
        next() {
          this._slide(ct);
        }
        nextWhenVisible() {
          !document.hidden && a(this._element) && this.next();
        }
        prev() {
          this._slide(ht);
        }
        pause() {
          this._isSliding && s(this._element), this._clearInterval();
        }
        cycle() {
          this._clearInterval(), this._updateInterval(), this._interval = setInterval(() => this.nextWhenVisible(), this._config.interval);
        }
        _maybeEnableCycle() {
          this._config.ride && (this._isSliding ? N.one(this._element, pt, () => this.cycle()) : this.cycle());
        }
        to(t2) {
          const e2 = this._getItems();
          if (t2 > e2.length - 1 || t2 < 0) return;
          if (this._isSliding) return void N.one(this._element, pt, () => this.to(t2));
          const i2 = this._getItemIndex(this._getActive());
          if (i2 === t2) return;
          const n2 = t2 > i2 ? ct : ht;
          this._slide(n2, e2[t2]);
        }
        dispose() {
          this._swipeHelper && this._swipeHelper.dispose(), super.dispose();
        }
        _configAfterMerge(t2) {
          return t2.defaultInterval = t2.interval, t2;
        }
        _addEventListeners() {
          this._config.keyboard && N.on(this._element, mt, (t2) => this._keydown(t2)), "hover" === this._config.pause && (N.on(this._element, gt, () => this.pause()), N.on(this._element, _t, () => this._maybeEnableCycle())), this._config.touch && st.isSupported() && this._addTouchEventListeners();
        }
        _addTouchEventListeners() {
          for (const t3 of z.find(".carousel-item img", this._element)) N.on(t3, bt, (t4) => t4.preventDefault());
          const t2 = { leftCallback: () => this._slide(this._directionToOrder(dt)), rightCallback: () => this._slide(this._directionToOrder(ut)), endCallback: () => {
            "hover" === this._config.pause && (this.pause(), this.touchTimeout && clearTimeout(this.touchTimeout), this.touchTimeout = setTimeout(() => this._maybeEnableCycle(), 500 + this._config.interval));
          } };
          this._swipeHelper = new st(this._element, t2);
        }
        _keydown(t2) {
          if (/input|textarea/i.test(t2.target.tagName)) return;
          const e2 = Ot[t2.key];
          e2 && (t2.preventDefault(), this._slide(this._directionToOrder(e2)));
        }
        _getItemIndex(t2) {
          return this._getItems().indexOf(t2);
        }
        _setActiveIndicatorElement(t2) {
          if (!this._indicatorsElement) return;
          const e2 = z.findOne(Et, this._indicatorsElement);
          e2.classList.remove(At), e2.removeAttribute("aria-current");
          const i2 = z.findOne(`[data-bs-slide-to="${t2}"]`, this._indicatorsElement);
          i2 && (i2.classList.add(At), i2.setAttribute("aria-current", "true"));
        }
        _updateInterval() {
          const t2 = this._activeElement || this._getActive();
          if (!t2) return;
          const e2 = Number.parseInt(t2.getAttribute("data-bs-interval"), 10);
          this._config.interval = e2 || this._config.defaultInterval;
        }
        _slide(t2, e2 = null) {
          if (this._isSliding) return;
          const i2 = this._getActive(), n2 = t2 === ct, s2 = e2 || b(this._getItems(), i2, n2, this._config.wrap);
          if (s2 === i2) return;
          const o2 = this._getItemIndex(s2), r2 = (e3) => N.trigger(this._element, e3, { relatedTarget: s2, direction: this._orderToDirection(t2), from: this._getItemIndex(i2), to: o2 });
          if (r2(ft).defaultPrevented) return;
          if (!i2 || !s2) return;
          const a2 = Boolean(this._interval);
          this.pause(), this._isSliding = true, this._setActiveIndicatorElement(o2), this._activeElement = s2;
          const l2 = n2 ? "carousel-item-start" : "carousel-item-end", c2 = n2 ? "carousel-item-next" : "carousel-item-prev";
          s2.classList.add(c2), d(s2), i2.classList.add(l2), s2.classList.add(l2), this._queueCallback(() => {
            s2.classList.remove(l2, c2), s2.classList.add(At), i2.classList.remove(At, c2, l2), this._isSliding = false, r2(pt);
          }, i2, this._isAnimated()), a2 && this.cycle();
        }
        _isAnimated() {
          return this._element.classList.contains("slide");
        }
        _getActive() {
          return z.findOne(Ct, this._element);
        }
        _getItems() {
          return z.find(Tt, this._element);
        }
        _clearInterval() {
          this._interval && (clearInterval(this._interval), this._interval = null);
        }
        _directionToOrder(t2) {
          return p() ? t2 === dt ? ht : ct : t2 === dt ? ct : ht;
        }
        _orderToDirection(t2) {
          return p() ? t2 === ht ? dt : ut : t2 === ht ? ut : dt;
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Lt.getOrCreateInstance(this, t2);
            if ("number" != typeof t2) {
              if ("string" == typeof t2) {
                if (void 0 === e2[t2] || t2.startsWith("_") || "constructor" === t2) throw new TypeError(`No method named "${t2}"`);
                e2[t2]();
              }
            } else e2.to(t2);
          });
        }
      }
      N.on(document, yt, "[data-bs-slide], [data-bs-slide-to]", function(t2) {
        const e2 = z.getElementFromSelector(this);
        if (!e2 || !e2.classList.contains(wt)) return;
        t2.preventDefault();
        const i2 = Lt.getOrCreateInstance(e2), n2 = this.getAttribute("data-bs-slide-to");
        return n2 ? (i2.to(n2), void i2._maybeEnableCycle()) : "next" === F.getDataAttribute(this, "slide") ? (i2.next(), void i2._maybeEnableCycle()) : (i2.prev(), void i2._maybeEnableCycle());
      }), N.on(window, vt, () => {
        const t2 = z.find('[data-bs-ride="carousel"]');
        for (const e2 of t2) Lt.getOrCreateInstance(e2);
      }), m(Lt);
      const St = ".bs.collapse", Dt = `show${St}`, $t = `shown${St}`, It = `hide${St}`, Nt = `hidden${St}`, Pt = `click${St}.data-api`, jt = "show", Mt = "collapse", Ft = "collapsing", Ht = `:scope .${Mt} .${Mt}`, Wt = '[data-bs-toggle="collapse"]', Bt = { parent: null, toggle: true }, zt = { parent: "(null|element)", toggle: "boolean" };
      class Rt extends W {
        constructor(t2, e2) {
          super(t2, e2), this._isTransitioning = false, this._triggerArray = [];
          const i2 = z.find(Wt);
          for (const t3 of i2) {
            const e3 = z.getSelectorFromElement(t3), i3 = z.find(e3).filter((t4) => t4 === this._element);
            null !== e3 && i3.length && this._triggerArray.push(t3);
          }
          this._initializeChildren(), this._config.parent || this._addAriaAndCollapsedClass(this._triggerArray, this._isShown()), this._config.toggle && this.toggle();
        }
        static get Default() {
          return Bt;
        }
        static get DefaultType() {
          return zt;
        }
        static get NAME() {
          return "collapse";
        }
        toggle() {
          this._isShown() ? this.hide() : this.show();
        }
        show() {
          if (this._isTransitioning || this._isShown()) return;
          let t2 = [];
          if (this._config.parent && (t2 = this._getFirstLevelChildren(".collapse.show, .collapse.collapsing").filter((t3) => t3 !== this._element).map((t3) => Rt.getOrCreateInstance(t3, { toggle: false }))), t2.length && t2[0]._isTransitioning) return;
          if (N.trigger(this._element, Dt).defaultPrevented) return;
          for (const e3 of t2) e3.hide();
          const e2 = this._getDimension();
          this._element.classList.remove(Mt), this._element.classList.add(Ft), this._element.style[e2] = 0, this._addAriaAndCollapsedClass(this._triggerArray, true), this._isTransitioning = true;
          const i2 = `scroll${e2[0].toUpperCase() + e2.slice(1)}`;
          this._queueCallback(() => {
            this._isTransitioning = false, this._element.classList.remove(Ft), this._element.classList.add(Mt, jt), this._element.style[e2] = "", N.trigger(this._element, $t);
          }, this._element, true), this._element.style[e2] = `${this._element[i2]}px`;
        }
        hide() {
          if (this._isTransitioning || !this._isShown()) return;
          if (N.trigger(this._element, It).defaultPrevented) return;
          const t2 = this._getDimension();
          this._element.style[t2] = `${this._element.getBoundingClientRect()[t2]}px`, d(this._element), this._element.classList.add(Ft), this._element.classList.remove(Mt, jt);
          for (const t3 of this._triggerArray) {
            const e2 = z.getElementFromSelector(t3);
            e2 && !this._isShown(e2) && this._addAriaAndCollapsedClass([t3], false);
          }
          this._isTransitioning = true, this._element.style[t2] = "", this._queueCallback(() => {
            this._isTransitioning = false, this._element.classList.remove(Ft), this._element.classList.add(Mt), N.trigger(this._element, Nt);
          }, this._element, true);
        }
        _isShown(t2 = this._element) {
          return t2.classList.contains(jt);
        }
        _configAfterMerge(t2) {
          return t2.toggle = Boolean(t2.toggle), t2.parent = r(t2.parent), t2;
        }
        _getDimension() {
          return this._element.classList.contains("collapse-horizontal") ? "width" : "height";
        }
        _initializeChildren() {
          if (!this._config.parent) return;
          const t2 = this._getFirstLevelChildren(Wt);
          for (const e2 of t2) {
            const t3 = z.getElementFromSelector(e2);
            t3 && this._addAriaAndCollapsedClass([e2], this._isShown(t3));
          }
        }
        _getFirstLevelChildren(t2) {
          const e2 = z.find(Ht, this._config.parent);
          return z.find(t2, this._config.parent).filter((t3) => !e2.includes(t3));
        }
        _addAriaAndCollapsedClass(t2, e2) {
          if (t2.length) for (const i2 of t2) i2.classList.toggle("collapsed", !e2), i2.setAttribute("aria-expanded", e2);
        }
        static jQueryInterface(t2) {
          const e2 = {};
          return "string" == typeof t2 && /show|hide/.test(t2) && (e2.toggle = false), this.each(function() {
            const i2 = Rt.getOrCreateInstance(this, e2);
            if ("string" == typeof t2) {
              if (void 0 === i2[t2]) throw new TypeError(`No method named "${t2}"`);
              i2[t2]();
            }
          });
        }
      }
      N.on(document, Pt, Wt, function(t2) {
        ("A" === t2.target.tagName || t2.delegateTarget && "A" === t2.delegateTarget.tagName) && t2.preventDefault();
        for (const t3 of z.getMultipleElementsFromSelector(this)) Rt.getOrCreateInstance(t3, { toggle: false }).toggle();
      }), m(Rt);
      var qt = "top", Vt = "bottom", Kt = "right", Qt = "left", Xt = "auto", Yt = [qt, Vt, Kt, Qt], Ut = "start", Gt = "end", Jt = "clippingParents", Zt = "viewport", te = "popper", ee = "reference", ie = Yt.reduce(function(t2, e2) {
        return t2.concat([e2 + "-" + Ut, e2 + "-" + Gt]);
      }, []), ne = [].concat(Yt, [Xt]).reduce(function(t2, e2) {
        return t2.concat([e2, e2 + "-" + Ut, e2 + "-" + Gt]);
      }, []), se = "beforeRead", oe = "read", re = "afterRead", ae = "beforeMain", le = "main", ce = "afterMain", he = "beforeWrite", de = "write", ue = "afterWrite", fe = [se, oe, re, ae, le, ce, he, de, ue];
      function pe(t2) {
        return t2 ? (t2.nodeName || "").toLowerCase() : null;
      }
      function me(t2) {
        if (null == t2) return window;
        if ("[object Window]" !== t2.toString()) {
          var e2 = t2.ownerDocument;
          return e2 && e2.defaultView || window;
        }
        return t2;
      }
      function ge(t2) {
        return t2 instanceof me(t2).Element || t2 instanceof Element;
      }
      function _e(t2) {
        return t2 instanceof me(t2).HTMLElement || t2 instanceof HTMLElement;
      }
      function be(t2) {
        return "undefined" != typeof ShadowRoot && (t2 instanceof me(t2).ShadowRoot || t2 instanceof ShadowRoot);
      }
      const ve = { name: "applyStyles", enabled: true, phase: "write", fn: function(t2) {
        var e2 = t2.state;
        Object.keys(e2.elements).forEach(function(t3) {
          var i2 = e2.styles[t3] || {}, n2 = e2.attributes[t3] || {}, s2 = e2.elements[t3];
          _e(s2) && pe(s2) && (Object.assign(s2.style, i2), Object.keys(n2).forEach(function(t4) {
            var e3 = n2[t4];
            false === e3 ? s2.removeAttribute(t4) : s2.setAttribute(t4, true === e3 ? "" : e3);
          }));
        });
      }, effect: function(t2) {
        var e2 = t2.state, i2 = { popper: { position: e2.options.strategy, left: "0", top: "0", margin: "0" }, arrow: { position: "absolute" }, reference: {} };
        return Object.assign(e2.elements.popper.style, i2.popper), e2.styles = i2, e2.elements.arrow && Object.assign(e2.elements.arrow.style, i2.arrow), function() {
          Object.keys(e2.elements).forEach(function(t3) {
            var n2 = e2.elements[t3], s2 = e2.attributes[t3] || {}, o2 = Object.keys(e2.styles.hasOwnProperty(t3) ? e2.styles[t3] : i2[t3]).reduce(function(t4, e3) {
              return t4[e3] = "", t4;
            }, {});
            _e(n2) && pe(n2) && (Object.assign(n2.style, o2), Object.keys(s2).forEach(function(t4) {
              n2.removeAttribute(t4);
            }));
          });
        };
      }, requires: ["computeStyles"] };
      function ye(t2) {
        return t2.split("-")[0];
      }
      var we = Math.max, Ae = Math.min, Ee = Math.round;
      function Te() {
        var t2 = navigator.userAgentData;
        return null != t2 && t2.brands && Array.isArray(t2.brands) ? t2.brands.map(function(t3) {
          return t3.brand + "/" + t3.version;
        }).join(" ") : navigator.userAgent;
      }
      function Ce() {
        return !/^((?!chrome|android).)*safari/i.test(Te());
      }
      function Oe(t2, e2, i2) {
        void 0 === e2 && (e2 = false), void 0 === i2 && (i2 = false);
        var n2 = t2.getBoundingClientRect(), s2 = 1, o2 = 1;
        e2 && _e(t2) && (s2 = t2.offsetWidth > 0 && Ee(n2.width) / t2.offsetWidth || 1, o2 = t2.offsetHeight > 0 && Ee(n2.height) / t2.offsetHeight || 1);
        var r2 = (ge(t2) ? me(t2) : window).visualViewport, a2 = !Ce() && i2, l2 = (n2.left + (a2 && r2 ? r2.offsetLeft : 0)) / s2, c2 = (n2.top + (a2 && r2 ? r2.offsetTop : 0)) / o2, h2 = n2.width / s2, d2 = n2.height / o2;
        return { width: h2, height: d2, top: c2, right: l2 + h2, bottom: c2 + d2, left: l2, x: l2, y: c2 };
      }
      function xe(t2) {
        var e2 = Oe(t2), i2 = t2.offsetWidth, n2 = t2.offsetHeight;
        return Math.abs(e2.width - i2) <= 1 && (i2 = e2.width), Math.abs(e2.height - n2) <= 1 && (n2 = e2.height), { x: t2.offsetLeft, y: t2.offsetTop, width: i2, height: n2 };
      }
      function ke(t2, e2) {
        var i2 = e2.getRootNode && e2.getRootNode();
        if (t2.contains(e2)) return true;
        if (i2 && be(i2)) {
          var n2 = e2;
          do {
            if (n2 && t2.isSameNode(n2)) return true;
            n2 = n2.parentNode || n2.host;
          } while (n2);
        }
        return false;
      }
      function Le(t2) {
        return me(t2).getComputedStyle(t2);
      }
      function Se(t2) {
        return ["table", "td", "th"].indexOf(pe(t2)) >= 0;
      }
      function De(t2) {
        return ((ge(t2) ? t2.ownerDocument : t2.document) || window.document).documentElement;
      }
      function $e(t2) {
        return "html" === pe(t2) ? t2 : t2.assignedSlot || t2.parentNode || (be(t2) ? t2.host : null) || De(t2);
      }
      function Ie(t2) {
        return _e(t2) && "fixed" !== Le(t2).position ? t2.offsetParent : null;
      }
      function Ne(t2) {
        for (var e2 = me(t2), i2 = Ie(t2); i2 && Se(i2) && "static" === Le(i2).position; ) i2 = Ie(i2);
        return i2 && ("html" === pe(i2) || "body" === pe(i2) && "static" === Le(i2).position) ? e2 : i2 || function(t3) {
          var e3 = /firefox/i.test(Te());
          if (/Trident/i.test(Te()) && _e(t3) && "fixed" === Le(t3).position) return null;
          var i3 = $e(t3);
          for (be(i3) && (i3 = i3.host); _e(i3) && ["html", "body"].indexOf(pe(i3)) < 0; ) {
            var n2 = Le(i3);
            if ("none" !== n2.transform || "none" !== n2.perspective || "paint" === n2.contain || -1 !== ["transform", "perspective"].indexOf(n2.willChange) || e3 && "filter" === n2.willChange || e3 && n2.filter && "none" !== n2.filter) return i3;
            i3 = i3.parentNode;
          }
          return null;
        }(t2) || e2;
      }
      function Pe(t2) {
        return ["top", "bottom"].indexOf(t2) >= 0 ? "x" : "y";
      }
      function je(t2, e2, i2) {
        return we(t2, Ae(e2, i2));
      }
      function Me(t2) {
        return Object.assign({}, { top: 0, right: 0, bottom: 0, left: 0 }, t2);
      }
      function Fe(t2, e2) {
        return e2.reduce(function(e3, i2) {
          return e3[i2] = t2, e3;
        }, {});
      }
      const He = { name: "arrow", enabled: true, phase: "main", fn: function(t2) {
        var e2, i2 = t2.state, n2 = t2.name, s2 = t2.options, o2 = i2.elements.arrow, r2 = i2.modifiersData.popperOffsets, a2 = ye(i2.placement), l2 = Pe(a2), c2 = [Qt, Kt].indexOf(a2) >= 0 ? "height" : "width";
        if (o2 && r2) {
          var h2 = function(t3, e3) {
            return Me("number" != typeof (t3 = "function" == typeof t3 ? t3(Object.assign({}, e3.rects, { placement: e3.placement })) : t3) ? t3 : Fe(t3, Yt));
          }(s2.padding, i2), d2 = xe(o2), u2 = "y" === l2 ? qt : Qt, f2 = "y" === l2 ? Vt : Kt, p2 = i2.rects.reference[c2] + i2.rects.reference[l2] - r2[l2] - i2.rects.popper[c2], m2 = r2[l2] - i2.rects.reference[l2], g2 = Ne(o2), _2 = g2 ? "y" === l2 ? g2.clientHeight || 0 : g2.clientWidth || 0 : 0, b2 = p2 / 2 - m2 / 2, v2 = h2[u2], y2 = _2 - d2[c2] - h2[f2], w2 = _2 / 2 - d2[c2] / 2 + b2, A2 = je(v2, w2, y2), E2 = l2;
          i2.modifiersData[n2] = ((e2 = {})[E2] = A2, e2.centerOffset = A2 - w2, e2);
        }
      }, effect: function(t2) {
        var e2 = t2.state, i2 = t2.options.element, n2 = void 0 === i2 ? "[data-popper-arrow]" : i2;
        null != n2 && ("string" != typeof n2 || (n2 = e2.elements.popper.querySelector(n2))) && ke(e2.elements.popper, n2) && (e2.elements.arrow = n2);
      }, requires: ["popperOffsets"], requiresIfExists: ["preventOverflow"] };
      function We(t2) {
        return t2.split("-")[1];
      }
      var Be = { top: "auto", right: "auto", bottom: "auto", left: "auto" };
      function ze(t2) {
        var e2, i2 = t2.popper, n2 = t2.popperRect, s2 = t2.placement, o2 = t2.variation, r2 = t2.offsets, a2 = t2.position, l2 = t2.gpuAcceleration, c2 = t2.adaptive, h2 = t2.roundOffsets, d2 = t2.isFixed, u2 = r2.x, f2 = void 0 === u2 ? 0 : u2, p2 = r2.y, m2 = void 0 === p2 ? 0 : p2, g2 = "function" == typeof h2 ? h2({ x: f2, y: m2 }) : { x: f2, y: m2 };
        f2 = g2.x, m2 = g2.y;
        var _2 = r2.hasOwnProperty("x"), b2 = r2.hasOwnProperty("y"), v2 = Qt, y2 = qt, w2 = window;
        if (c2) {
          var A2 = Ne(i2), E2 = "clientHeight", T2 = "clientWidth";
          A2 === me(i2) && "static" !== Le(A2 = De(i2)).position && "absolute" === a2 && (E2 = "scrollHeight", T2 = "scrollWidth"), (s2 === qt || (s2 === Qt || s2 === Kt) && o2 === Gt) && (y2 = Vt, m2 -= (d2 && A2 === w2 && w2.visualViewport ? w2.visualViewport.height : A2[E2]) - n2.height, m2 *= l2 ? 1 : -1), s2 !== Qt && (s2 !== qt && s2 !== Vt || o2 !== Gt) || (v2 = Kt, f2 -= (d2 && A2 === w2 && w2.visualViewport ? w2.visualViewport.width : A2[T2]) - n2.width, f2 *= l2 ? 1 : -1);
        }
        var C2, O2 = Object.assign({ position: a2 }, c2 && Be), x2 = true === h2 ? function(t3, e3) {
          var i3 = t3.x, n3 = t3.y, s3 = e3.devicePixelRatio || 1;
          return { x: Ee(i3 * s3) / s3 || 0, y: Ee(n3 * s3) / s3 || 0 };
        }({ x: f2, y: m2 }, me(i2)) : { x: f2, y: m2 };
        return f2 = x2.x, m2 = x2.y, l2 ? Object.assign({}, O2, ((C2 = {})[y2] = b2 ? "0" : "", C2[v2] = _2 ? "0" : "", C2.transform = (w2.devicePixelRatio || 1) <= 1 ? "translate(" + f2 + "px, " + m2 + "px)" : "translate3d(" + f2 + "px, " + m2 + "px, 0)", C2)) : Object.assign({}, O2, ((e2 = {})[y2] = b2 ? m2 + "px" : "", e2[v2] = _2 ? f2 + "px" : "", e2.transform = "", e2));
      }
      const Re = { name: "computeStyles", enabled: true, phase: "beforeWrite", fn: function(t2) {
        var e2 = t2.state, i2 = t2.options, n2 = i2.gpuAcceleration, s2 = void 0 === n2 || n2, o2 = i2.adaptive, r2 = void 0 === o2 || o2, a2 = i2.roundOffsets, l2 = void 0 === a2 || a2, c2 = { placement: ye(e2.placement), variation: We(e2.placement), popper: e2.elements.popper, popperRect: e2.rects.popper, gpuAcceleration: s2, isFixed: "fixed" === e2.options.strategy };
        null != e2.modifiersData.popperOffsets && (e2.styles.popper = Object.assign({}, e2.styles.popper, ze(Object.assign({}, c2, { offsets: e2.modifiersData.popperOffsets, position: e2.options.strategy, adaptive: r2, roundOffsets: l2 })))), null != e2.modifiersData.arrow && (e2.styles.arrow = Object.assign({}, e2.styles.arrow, ze(Object.assign({}, c2, { offsets: e2.modifiersData.arrow, position: "absolute", adaptive: false, roundOffsets: l2 })))), e2.attributes.popper = Object.assign({}, e2.attributes.popper, { "data-popper-placement": e2.placement });
      }, data: {} };
      var qe = { passive: true };
      const Ve = { name: "eventListeners", enabled: true, phase: "write", fn: function() {
      }, effect: function(t2) {
        var e2 = t2.state, i2 = t2.instance, n2 = t2.options, s2 = n2.scroll, o2 = void 0 === s2 || s2, r2 = n2.resize, a2 = void 0 === r2 || r2, l2 = me(e2.elements.popper), c2 = [].concat(e2.scrollParents.reference, e2.scrollParents.popper);
        return o2 && c2.forEach(function(t3) {
          t3.addEventListener("scroll", i2.update, qe);
        }), a2 && l2.addEventListener("resize", i2.update, qe), function() {
          o2 && c2.forEach(function(t3) {
            t3.removeEventListener("scroll", i2.update, qe);
          }), a2 && l2.removeEventListener("resize", i2.update, qe);
        };
      }, data: {} };
      var Ke = { left: "right", right: "left", bottom: "top", top: "bottom" };
      function Qe(t2) {
        return t2.replace(/left|right|bottom|top/g, function(t3) {
          return Ke[t3];
        });
      }
      var Xe = { start: "end", end: "start" };
      function Ye(t2) {
        return t2.replace(/start|end/g, function(t3) {
          return Xe[t3];
        });
      }
      function Ue(t2) {
        var e2 = me(t2);
        return { scrollLeft: e2.pageXOffset, scrollTop: e2.pageYOffset };
      }
      function Ge(t2) {
        return Oe(De(t2)).left + Ue(t2).scrollLeft;
      }
      function Je(t2) {
        var e2 = Le(t2), i2 = e2.overflow, n2 = e2.overflowX, s2 = e2.overflowY;
        return /auto|scroll|overlay|hidden/.test(i2 + s2 + n2);
      }
      function Ze(t2) {
        return ["html", "body", "#document"].indexOf(pe(t2)) >= 0 ? t2.ownerDocument.body : _e(t2) && Je(t2) ? t2 : Ze($e(t2));
      }
      function ti(t2, e2) {
        var i2;
        void 0 === e2 && (e2 = []);
        var n2 = Ze(t2), s2 = n2 === (null == (i2 = t2.ownerDocument) ? void 0 : i2.body), o2 = me(n2), r2 = s2 ? [o2].concat(o2.visualViewport || [], Je(n2) ? n2 : []) : n2, a2 = e2.concat(r2);
        return s2 ? a2 : a2.concat(ti($e(r2)));
      }
      function ei(t2) {
        return Object.assign({}, t2, { left: t2.x, top: t2.y, right: t2.x + t2.width, bottom: t2.y + t2.height });
      }
      function ii(t2, e2, i2) {
        return e2 === Zt ? ei(function(t3, e3) {
          var i3 = me(t3), n2 = De(t3), s2 = i3.visualViewport, o2 = n2.clientWidth, r2 = n2.clientHeight, a2 = 0, l2 = 0;
          if (s2) {
            o2 = s2.width, r2 = s2.height;
            var c2 = Ce();
            (c2 || !c2 && "fixed" === e3) && (a2 = s2.offsetLeft, l2 = s2.offsetTop);
          }
          return { width: o2, height: r2, x: a2 + Ge(t3), y: l2 };
        }(t2, i2)) : ge(e2) ? function(t3, e3) {
          var i3 = Oe(t3, false, "fixed" === e3);
          return i3.top = i3.top + t3.clientTop, i3.left = i3.left + t3.clientLeft, i3.bottom = i3.top + t3.clientHeight, i3.right = i3.left + t3.clientWidth, i3.width = t3.clientWidth, i3.height = t3.clientHeight, i3.x = i3.left, i3.y = i3.top, i3;
        }(e2, i2) : ei(function(t3) {
          var e3, i3 = De(t3), n2 = Ue(t3), s2 = null == (e3 = t3.ownerDocument) ? void 0 : e3.body, o2 = we(i3.scrollWidth, i3.clientWidth, s2 ? s2.scrollWidth : 0, s2 ? s2.clientWidth : 0), r2 = we(i3.scrollHeight, i3.clientHeight, s2 ? s2.scrollHeight : 0, s2 ? s2.clientHeight : 0), a2 = -n2.scrollLeft + Ge(t3), l2 = -n2.scrollTop;
          return "rtl" === Le(s2 || i3).direction && (a2 += we(i3.clientWidth, s2 ? s2.clientWidth : 0) - o2), { width: o2, height: r2, x: a2, y: l2 };
        }(De(t2)));
      }
      function ni(t2) {
        var e2, i2 = t2.reference, n2 = t2.element, s2 = t2.placement, o2 = s2 ? ye(s2) : null, r2 = s2 ? We(s2) : null, a2 = i2.x + i2.width / 2 - n2.width / 2, l2 = i2.y + i2.height / 2 - n2.height / 2;
        switch (o2) {
          case qt:
            e2 = { x: a2, y: i2.y - n2.height };
            break;
          case Vt:
            e2 = { x: a2, y: i2.y + i2.height };
            break;
          case Kt:
            e2 = { x: i2.x + i2.width, y: l2 };
            break;
          case Qt:
            e2 = { x: i2.x - n2.width, y: l2 };
            break;
          default:
            e2 = { x: i2.x, y: i2.y };
        }
        var c2 = o2 ? Pe(o2) : null;
        if (null != c2) {
          var h2 = "y" === c2 ? "height" : "width";
          switch (r2) {
            case Ut:
              e2[c2] = e2[c2] - (i2[h2] / 2 - n2[h2] / 2);
              break;
            case Gt:
              e2[c2] = e2[c2] + (i2[h2] / 2 - n2[h2] / 2);
          }
        }
        return e2;
      }
      function si(t2, e2) {
        void 0 === e2 && (e2 = {});
        var i2 = e2, n2 = i2.placement, s2 = void 0 === n2 ? t2.placement : n2, o2 = i2.strategy, r2 = void 0 === o2 ? t2.strategy : o2, a2 = i2.boundary, l2 = void 0 === a2 ? Jt : a2, c2 = i2.rootBoundary, h2 = void 0 === c2 ? Zt : c2, d2 = i2.elementContext, u2 = void 0 === d2 ? te : d2, f2 = i2.altBoundary, p2 = void 0 !== f2 && f2, m2 = i2.padding, g2 = void 0 === m2 ? 0 : m2, _2 = Me("number" != typeof g2 ? g2 : Fe(g2, Yt)), b2 = u2 === te ? ee : te, v2 = t2.rects.popper, y2 = t2.elements[p2 ? b2 : u2], w2 = function(t3, e3, i3, n3) {
          var s3 = "clippingParents" === e3 ? function(t4) {
            var e4 = ti($e(t4)), i4 = ["absolute", "fixed"].indexOf(Le(t4).position) >= 0 && _e(t4) ? Ne(t4) : t4;
            return ge(i4) ? e4.filter(function(t5) {
              return ge(t5) && ke(t5, i4) && "body" !== pe(t5);
            }) : [];
          }(t3) : [].concat(e3), o3 = [].concat(s3, [i3]), r3 = o3[0], a3 = o3.reduce(function(e4, i4) {
            var s4 = ii(t3, i4, n3);
            return e4.top = we(s4.top, e4.top), e4.right = Ae(s4.right, e4.right), e4.bottom = Ae(s4.bottom, e4.bottom), e4.left = we(s4.left, e4.left), e4;
          }, ii(t3, r3, n3));
          return a3.width = a3.right - a3.left, a3.height = a3.bottom - a3.top, a3.x = a3.left, a3.y = a3.top, a3;
        }(ge(y2) ? y2 : y2.contextElement || De(t2.elements.popper), l2, h2, r2), A2 = Oe(t2.elements.reference), E2 = ni({ reference: A2, element: v2, placement: s2 }), T2 = ei(Object.assign({}, v2, E2)), C2 = u2 === te ? T2 : A2, O2 = { top: w2.top - C2.top + _2.top, bottom: C2.bottom - w2.bottom + _2.bottom, left: w2.left - C2.left + _2.left, right: C2.right - w2.right + _2.right }, x2 = t2.modifiersData.offset;
        if (u2 === te && x2) {
          var k2 = x2[s2];
          Object.keys(O2).forEach(function(t3) {
            var e3 = [Kt, Vt].indexOf(t3) >= 0 ? 1 : -1, i3 = [qt, Vt].indexOf(t3) >= 0 ? "y" : "x";
            O2[t3] += k2[i3] * e3;
          });
        }
        return O2;
      }
      function oi(t2, e2) {
        void 0 === e2 && (e2 = {});
        var i2 = e2, n2 = i2.placement, s2 = i2.boundary, o2 = i2.rootBoundary, r2 = i2.padding, a2 = i2.flipVariations, l2 = i2.allowedAutoPlacements, c2 = void 0 === l2 ? ne : l2, h2 = We(n2), d2 = h2 ? a2 ? ie : ie.filter(function(t3) {
          return We(t3) === h2;
        }) : Yt, u2 = d2.filter(function(t3) {
          return c2.indexOf(t3) >= 0;
        });
        0 === u2.length && (u2 = d2);
        var f2 = u2.reduce(function(e3, i3) {
          return e3[i3] = si(t2, { placement: i3, boundary: s2, rootBoundary: o2, padding: r2 })[ye(i3)], e3;
        }, {});
        return Object.keys(f2).sort(function(t3, e3) {
          return f2[t3] - f2[e3];
        });
      }
      const ri = { name: "flip", enabled: true, phase: "main", fn: function(t2) {
        var e2 = t2.state, i2 = t2.options, n2 = t2.name;
        if (!e2.modifiersData[n2]._skip) {
          for (var s2 = i2.mainAxis, o2 = void 0 === s2 || s2, r2 = i2.altAxis, a2 = void 0 === r2 || r2, l2 = i2.fallbackPlacements, c2 = i2.padding, h2 = i2.boundary, d2 = i2.rootBoundary, u2 = i2.altBoundary, f2 = i2.flipVariations, p2 = void 0 === f2 || f2, m2 = i2.allowedAutoPlacements, g2 = e2.options.placement, _2 = ye(g2), b2 = l2 || (_2 !== g2 && p2 ? function(t3) {
            if (ye(t3) === Xt) return [];
            var e3 = Qe(t3);
            return [Ye(t3), e3, Ye(e3)];
          }(g2) : [Qe(g2)]), v2 = [g2].concat(b2).reduce(function(t3, i3) {
            return t3.concat(ye(i3) === Xt ? oi(e2, { placement: i3, boundary: h2, rootBoundary: d2, padding: c2, flipVariations: p2, allowedAutoPlacements: m2 }) : i3);
          }, []), y2 = e2.rects.reference, w2 = e2.rects.popper, A2 = /* @__PURE__ */ new Map(), E2 = true, T2 = v2[0], C2 = 0; C2 < v2.length; C2++) {
            var O2 = v2[C2], x2 = ye(O2), k2 = We(O2) === Ut, L2 = [qt, Vt].indexOf(x2) >= 0, S2 = L2 ? "width" : "height", D2 = si(e2, { placement: O2, boundary: h2, rootBoundary: d2, altBoundary: u2, padding: c2 }), $2 = L2 ? k2 ? Kt : Qt : k2 ? Vt : qt;
            y2[S2] > w2[S2] && ($2 = Qe($2));
            var I2 = Qe($2), N2 = [];
            if (o2 && N2.push(D2[x2] <= 0), a2 && N2.push(D2[$2] <= 0, D2[I2] <= 0), N2.every(function(t3) {
              return t3;
            })) {
              T2 = O2, E2 = false;
              break;
            }
            A2.set(O2, N2);
          }
          if (E2) for (var P2 = function(t3) {
            var e3 = v2.find(function(e4) {
              var i3 = A2.get(e4);
              if (i3) return i3.slice(0, t3).every(function(t4) {
                return t4;
              });
            });
            if (e3) return T2 = e3, "break";
          }, j2 = p2 ? 3 : 1; j2 > 0 && "break" !== P2(j2); j2--) ;
          e2.placement !== T2 && (e2.modifiersData[n2]._skip = true, e2.placement = T2, e2.reset = true);
        }
      }, requiresIfExists: ["offset"], data: { _skip: false } };
      function ai(t2, e2, i2) {
        return void 0 === i2 && (i2 = { x: 0, y: 0 }), { top: t2.top - e2.height - i2.y, right: t2.right - e2.width + i2.x, bottom: t2.bottom - e2.height + i2.y, left: t2.left - e2.width - i2.x };
      }
      function li(t2) {
        return [qt, Kt, Vt, Qt].some(function(e2) {
          return t2[e2] >= 0;
        });
      }
      const ci = { name: "hide", enabled: true, phase: "main", requiresIfExists: ["preventOverflow"], fn: function(t2) {
        var e2 = t2.state, i2 = t2.name, n2 = e2.rects.reference, s2 = e2.rects.popper, o2 = e2.modifiersData.preventOverflow, r2 = si(e2, { elementContext: "reference" }), a2 = si(e2, { altBoundary: true }), l2 = ai(r2, n2), c2 = ai(a2, s2, o2), h2 = li(l2), d2 = li(c2);
        e2.modifiersData[i2] = { referenceClippingOffsets: l2, popperEscapeOffsets: c2, isReferenceHidden: h2, hasPopperEscaped: d2 }, e2.attributes.popper = Object.assign({}, e2.attributes.popper, { "data-popper-reference-hidden": h2, "data-popper-escaped": d2 });
      } }, hi = { name: "offset", enabled: true, phase: "main", requires: ["popperOffsets"], fn: function(t2) {
        var e2 = t2.state, i2 = t2.options, n2 = t2.name, s2 = i2.offset, o2 = void 0 === s2 ? [0, 0] : s2, r2 = ne.reduce(function(t3, i3) {
          return t3[i3] = function(t4, e3, i4) {
            var n3 = ye(t4), s3 = [Qt, qt].indexOf(n3) >= 0 ? -1 : 1, o3 = "function" == typeof i4 ? i4(Object.assign({}, e3, { placement: t4 })) : i4, r3 = o3[0], a3 = o3[1];
            return r3 = r3 || 0, a3 = (a3 || 0) * s3, [Qt, Kt].indexOf(n3) >= 0 ? { x: a3, y: r3 } : { x: r3, y: a3 };
          }(i3, e2.rects, o2), t3;
        }, {}), a2 = r2[e2.placement], l2 = a2.x, c2 = a2.y;
        null != e2.modifiersData.popperOffsets && (e2.modifiersData.popperOffsets.x += l2, e2.modifiersData.popperOffsets.y += c2), e2.modifiersData[n2] = r2;
      } }, di = { name: "popperOffsets", enabled: true, phase: "read", fn: function(t2) {
        var e2 = t2.state, i2 = t2.name;
        e2.modifiersData[i2] = ni({ reference: e2.rects.reference, element: e2.rects.popper, placement: e2.placement });
      }, data: {} }, ui = { name: "preventOverflow", enabled: true, phase: "main", fn: function(t2) {
        var e2 = t2.state, i2 = t2.options, n2 = t2.name, s2 = i2.mainAxis, o2 = void 0 === s2 || s2, r2 = i2.altAxis, a2 = void 0 !== r2 && r2, l2 = i2.boundary, c2 = i2.rootBoundary, h2 = i2.altBoundary, d2 = i2.padding, u2 = i2.tether, f2 = void 0 === u2 || u2, p2 = i2.tetherOffset, m2 = void 0 === p2 ? 0 : p2, g2 = si(e2, { boundary: l2, rootBoundary: c2, padding: d2, altBoundary: h2 }), _2 = ye(e2.placement), b2 = We(e2.placement), v2 = !b2, y2 = Pe(_2), w2 = "x" === y2 ? "y" : "x", A2 = e2.modifiersData.popperOffsets, E2 = e2.rects.reference, T2 = e2.rects.popper, C2 = "function" == typeof m2 ? m2(Object.assign({}, e2.rects, { placement: e2.placement })) : m2, O2 = "number" == typeof C2 ? { mainAxis: C2, altAxis: C2 } : Object.assign({ mainAxis: 0, altAxis: 0 }, C2), x2 = e2.modifiersData.offset ? e2.modifiersData.offset[e2.placement] : null, k2 = { x: 0, y: 0 };
        if (A2) {
          if (o2) {
            var L2, S2 = "y" === y2 ? qt : Qt, D2 = "y" === y2 ? Vt : Kt, $2 = "y" === y2 ? "height" : "width", I2 = A2[y2], N2 = I2 + g2[S2], P2 = I2 - g2[D2], j2 = f2 ? -T2[$2] / 2 : 0, M2 = b2 === Ut ? E2[$2] : T2[$2], F2 = b2 === Ut ? -T2[$2] : -E2[$2], H2 = e2.elements.arrow, W2 = f2 && H2 ? xe(H2) : { width: 0, height: 0 }, B2 = e2.modifiersData["arrow#persistent"] ? e2.modifiersData["arrow#persistent"].padding : { top: 0, right: 0, bottom: 0, left: 0 }, z2 = B2[S2], R2 = B2[D2], q2 = je(0, E2[$2], W2[$2]), V2 = v2 ? E2[$2] / 2 - j2 - q2 - z2 - O2.mainAxis : M2 - q2 - z2 - O2.mainAxis, K2 = v2 ? -E2[$2] / 2 + j2 + q2 + R2 + O2.mainAxis : F2 + q2 + R2 + O2.mainAxis, Q2 = e2.elements.arrow && Ne(e2.elements.arrow), X2 = Q2 ? "y" === y2 ? Q2.clientTop || 0 : Q2.clientLeft || 0 : 0, Y2 = null != (L2 = null == x2 ? void 0 : x2[y2]) ? L2 : 0, U2 = I2 + K2 - Y2, G2 = je(f2 ? Ae(N2, I2 + V2 - Y2 - X2) : N2, I2, f2 ? we(P2, U2) : P2);
            A2[y2] = G2, k2[y2] = G2 - I2;
          }
          if (a2) {
            var J2, Z2 = "x" === y2 ? qt : Qt, tt2 = "x" === y2 ? Vt : Kt, et2 = A2[w2], it2 = "y" === w2 ? "height" : "width", nt2 = et2 + g2[Z2], st2 = et2 - g2[tt2], ot2 = -1 !== [qt, Qt].indexOf(_2), rt2 = null != (J2 = null == x2 ? void 0 : x2[w2]) ? J2 : 0, at2 = ot2 ? nt2 : et2 - E2[it2] - T2[it2] - rt2 + O2.altAxis, lt2 = ot2 ? et2 + E2[it2] + T2[it2] - rt2 - O2.altAxis : st2, ct2 = f2 && ot2 ? function(t3, e3, i3) {
              var n3 = je(t3, e3, i3);
              return n3 > i3 ? i3 : n3;
            }(at2, et2, lt2) : je(f2 ? at2 : nt2, et2, f2 ? lt2 : st2);
            A2[w2] = ct2, k2[w2] = ct2 - et2;
          }
          e2.modifiersData[n2] = k2;
        }
      }, requiresIfExists: ["offset"] };
      function fi(t2, e2, i2) {
        void 0 === i2 && (i2 = false);
        var n2, s2, o2 = _e(e2), r2 = _e(e2) && function(t3) {
          var e3 = t3.getBoundingClientRect(), i3 = Ee(e3.width) / t3.offsetWidth || 1, n3 = Ee(e3.height) / t3.offsetHeight || 1;
          return 1 !== i3 || 1 !== n3;
        }(e2), a2 = De(e2), l2 = Oe(t2, r2, i2), c2 = { scrollLeft: 0, scrollTop: 0 }, h2 = { x: 0, y: 0 };
        return (o2 || !o2 && !i2) && (("body" !== pe(e2) || Je(a2)) && (c2 = (n2 = e2) !== me(n2) && _e(n2) ? { scrollLeft: (s2 = n2).scrollLeft, scrollTop: s2.scrollTop } : Ue(n2)), _e(e2) ? ((h2 = Oe(e2, true)).x += e2.clientLeft, h2.y += e2.clientTop) : a2 && (h2.x = Ge(a2))), { x: l2.left + c2.scrollLeft - h2.x, y: l2.top + c2.scrollTop - h2.y, width: l2.width, height: l2.height };
      }
      function pi(t2) {
        var e2 = /* @__PURE__ */ new Map(), i2 = /* @__PURE__ */ new Set(), n2 = [];
        function s2(t3) {
          i2.add(t3.name), [].concat(t3.requires || [], t3.requiresIfExists || []).forEach(function(t4) {
            if (!i2.has(t4)) {
              var n3 = e2.get(t4);
              n3 && s2(n3);
            }
          }), n2.push(t3);
        }
        return t2.forEach(function(t3) {
          e2.set(t3.name, t3);
        }), t2.forEach(function(t3) {
          i2.has(t3.name) || s2(t3);
        }), n2;
      }
      var mi = { placement: "bottom", modifiers: [], strategy: "absolute" };
      function gi() {
        for (var t2 = arguments.length, e2 = new Array(t2), i2 = 0; i2 < t2; i2++) e2[i2] = arguments[i2];
        return !e2.some(function(t3) {
          return !(t3 && "function" == typeof t3.getBoundingClientRect);
        });
      }
      function _i(t2) {
        void 0 === t2 && (t2 = {});
        var e2 = t2, i2 = e2.defaultModifiers, n2 = void 0 === i2 ? [] : i2, s2 = e2.defaultOptions, o2 = void 0 === s2 ? mi : s2;
        return function(t3, e3, i3) {
          void 0 === i3 && (i3 = o2);
          var s3, r2, a2 = { placement: "bottom", orderedModifiers: [], options: Object.assign({}, mi, o2), modifiersData: {}, elements: { reference: t3, popper: e3 }, attributes: {}, styles: {} }, l2 = [], c2 = false, h2 = { state: a2, setOptions: function(i4) {
            var s4 = "function" == typeof i4 ? i4(a2.options) : i4;
            d2(), a2.options = Object.assign({}, o2, a2.options, s4), a2.scrollParents = { reference: ge(t3) ? ti(t3) : t3.contextElement ? ti(t3.contextElement) : [], popper: ti(e3) };
            var r3, c3, u2 = function(t4) {
              var e4 = pi(t4);
              return fe.reduce(function(t5, i5) {
                return t5.concat(e4.filter(function(t6) {
                  return t6.phase === i5;
                }));
              }, []);
            }((r3 = [].concat(n2, a2.options.modifiers), c3 = r3.reduce(function(t4, e4) {
              var i5 = t4[e4.name];
              return t4[e4.name] = i5 ? Object.assign({}, i5, e4, { options: Object.assign({}, i5.options, e4.options), data: Object.assign({}, i5.data, e4.data) }) : e4, t4;
            }, {}), Object.keys(c3).map(function(t4) {
              return c3[t4];
            })));
            return a2.orderedModifiers = u2.filter(function(t4) {
              return t4.enabled;
            }), a2.orderedModifiers.forEach(function(t4) {
              var e4 = t4.name, i5 = t4.options, n3 = void 0 === i5 ? {} : i5, s5 = t4.effect;
              if ("function" == typeof s5) {
                var o3 = s5({ state: a2, name: e4, instance: h2, options: n3 });
                l2.push(o3 || function() {
                });
              }
            }), h2.update();
          }, forceUpdate: function() {
            if (!c2) {
              var t4 = a2.elements, e4 = t4.reference, i4 = t4.popper;
              if (gi(e4, i4)) {
                a2.rects = { reference: fi(e4, Ne(i4), "fixed" === a2.options.strategy), popper: xe(i4) }, a2.reset = false, a2.placement = a2.options.placement, a2.orderedModifiers.forEach(function(t5) {
                  return a2.modifiersData[t5.name] = Object.assign({}, t5.data);
                });
                for (var n3 = 0; n3 < a2.orderedModifiers.length; n3++) if (true !== a2.reset) {
                  var s4 = a2.orderedModifiers[n3], o3 = s4.fn, r3 = s4.options, l3 = void 0 === r3 ? {} : r3, d3 = s4.name;
                  "function" == typeof o3 && (a2 = o3({ state: a2, options: l3, name: d3, instance: h2 }) || a2);
                } else a2.reset = false, n3 = -1;
              }
            }
          }, update: (s3 = function() {
            return new Promise(function(t4) {
              h2.forceUpdate(), t4(a2);
            });
          }, function() {
            return r2 || (r2 = new Promise(function(t4) {
              Promise.resolve().then(function() {
                r2 = void 0, t4(s3());
              });
            })), r2;
          }), destroy: function() {
            d2(), c2 = true;
          } };
          if (!gi(t3, e3)) return h2;
          function d2() {
            l2.forEach(function(t4) {
              return t4();
            }), l2 = [];
          }
          return h2.setOptions(i3).then(function(t4) {
            !c2 && i3.onFirstUpdate && i3.onFirstUpdate(t4);
          }), h2;
        };
      }
      var bi = _i(), vi = _i({ defaultModifiers: [Ve, di, Re, ve] }), yi = _i({ defaultModifiers: [Ve, di, Re, ve, hi, ri, ui, He, ci] });
      const wi = Object.freeze(Object.defineProperty({ __proto__: null, afterMain: ce, afterRead: re, afterWrite: ue, applyStyles: ve, arrow: He, auto: Xt, basePlacements: Yt, beforeMain: ae, beforeRead: se, beforeWrite: he, bottom: Vt, clippingParents: Jt, computeStyles: Re, createPopper: yi, createPopperBase: bi, createPopperLite: vi, detectOverflow: si, end: Gt, eventListeners: Ve, flip: ri, hide: ci, left: Qt, main: le, modifierPhases: fe, offset: hi, placements: ne, popper: te, popperGenerator: _i, popperOffsets: di, preventOverflow: ui, read: oe, reference: ee, right: Kt, start: Ut, top: qt, variationPlacements: ie, viewport: Zt, write: de }, Symbol.toStringTag, { value: "Module" })), Ai = "dropdown", Ei = ".bs.dropdown", Ti = ".data-api", Ci = "ArrowUp", Oi = "ArrowDown", xi = `hide${Ei}`, ki = `hidden${Ei}`, Li = `show${Ei}`, Si = `shown${Ei}`, Di = `click${Ei}${Ti}`, $i = `keydown${Ei}${Ti}`, Ii = `keyup${Ei}${Ti}`, Ni = "show", Pi = '[data-bs-toggle="dropdown"]:not(.disabled):not(:disabled)', ji = `${Pi}.${Ni}`, Mi = ".dropdown-menu", Fi = p() ? "top-end" : "top-start", Hi = p() ? "top-start" : "top-end", Wi = p() ? "bottom-end" : "bottom-start", Bi = p() ? "bottom-start" : "bottom-end", zi = p() ? "left-start" : "right-start", Ri = p() ? "right-start" : "left-start", qi = { autoClose: true, boundary: "clippingParents", display: "dynamic", offset: [0, 2], popperConfig: null, reference: "toggle" }, Vi = { autoClose: "(boolean|string)", boundary: "(string|element)", display: "string", offset: "(array|string|function)", popperConfig: "(null|object|function)", reference: "(string|element|object)" };
      class Ki extends W {
        constructor(t2, e2) {
          super(t2, e2), this._popper = null, this._parent = this._element.parentNode, this._menu = z.next(this._element, Mi)[0] || z.prev(this._element, Mi)[0] || z.findOne(Mi, this._parent), this._inNavbar = this._detectNavbar();
        }
        static get Default() {
          return qi;
        }
        static get DefaultType() {
          return Vi;
        }
        static get NAME() {
          return Ai;
        }
        toggle() {
          return this._isShown() ? this.hide() : this.show();
        }
        show() {
          if (l(this._element) || this._isShown()) return;
          const t2 = { relatedTarget: this._element };
          if (!N.trigger(this._element, Li, t2).defaultPrevented) {
            if (this._createPopper(), "ontouchstart" in document.documentElement && !this._parent.closest(".navbar-nav")) for (const t3 of [].concat(...document.body.children)) N.on(t3, "mouseover", h);
            this._element.focus(), this._element.setAttribute("aria-expanded", true), this._menu.classList.add(Ni), this._element.classList.add(Ni), N.trigger(this._element, Si, t2);
          }
        }
        hide() {
          if (l(this._element) || !this._isShown()) return;
          const t2 = { relatedTarget: this._element };
          this._completeHide(t2);
        }
        dispose() {
          this._popper && this._popper.destroy(), super.dispose();
        }
        update() {
          this._inNavbar = this._detectNavbar(), this._popper && this._popper.update();
        }
        _completeHide(t2) {
          if (!N.trigger(this._element, xi, t2).defaultPrevented) {
            if ("ontouchstart" in document.documentElement) for (const t3 of [].concat(...document.body.children)) N.off(t3, "mouseover", h);
            this._popper && this._popper.destroy(), this._menu.classList.remove(Ni), this._element.classList.remove(Ni), this._element.setAttribute("aria-expanded", "false"), F.removeDataAttribute(this._menu, "popper"), N.trigger(this._element, ki, t2), this._element.focus();
          }
        }
        _getConfig(t2) {
          if ("object" == typeof (t2 = super._getConfig(t2)).reference && !o(t2.reference) && "function" != typeof t2.reference.getBoundingClientRect) throw new TypeError(`${Ai.toUpperCase()}: Option "reference" provided type "object" without a required "getBoundingClientRect" method.`);
          return t2;
        }
        _createPopper() {
          if (void 0 === wi) throw new TypeError("Bootstrap's dropdowns require Popper (https://popper.js.org/docs/v2/)");
          let t2 = this._element;
          "parent" === this._config.reference ? t2 = this._parent : o(this._config.reference) ? t2 = r(this._config.reference) : "object" == typeof this._config.reference && (t2 = this._config.reference);
          const e2 = this._getPopperConfig();
          this._popper = yi(t2, this._menu, e2);
        }
        _isShown() {
          return this._menu.classList.contains(Ni);
        }
        _getPlacement() {
          const t2 = this._parent;
          if (t2.classList.contains("dropend")) return zi;
          if (t2.classList.contains("dropstart")) return Ri;
          if (t2.classList.contains("dropup-center")) return "top";
          if (t2.classList.contains("dropdown-center")) return "bottom";
          const e2 = "end" === getComputedStyle(this._menu).getPropertyValue("--bs-position").trim();
          return t2.classList.contains("dropup") ? e2 ? Hi : Fi : e2 ? Bi : Wi;
        }
        _detectNavbar() {
          return null !== this._element.closest(".navbar");
        }
        _getOffset() {
          const { offset: t2 } = this._config;
          return "string" == typeof t2 ? t2.split(",").map((t3) => Number.parseInt(t3, 10)) : "function" == typeof t2 ? (e2) => t2(e2, this._element) : t2;
        }
        _getPopperConfig() {
          const t2 = { placement: this._getPlacement(), modifiers: [{ name: "preventOverflow", options: { boundary: this._config.boundary } }, { name: "offset", options: { offset: this._getOffset() } }] };
          return (this._inNavbar || "static" === this._config.display) && (F.setDataAttribute(this._menu, "popper", "static"), t2.modifiers = [{ name: "applyStyles", enabled: false }]), { ...t2, ...g(this._config.popperConfig, [void 0, t2]) };
        }
        _selectMenuItem({ key: t2, target: e2 }) {
          const i2 = z.find(".dropdown-menu .dropdown-item:not(.disabled):not(:disabled)", this._menu).filter((t3) => a(t3));
          i2.length && b(i2, e2, t2 === Oi, !i2.includes(e2)).focus();
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Ki.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2]) throw new TypeError(`No method named "${t2}"`);
              e2[t2]();
            }
          });
        }
        static clearMenus(t2) {
          if (2 === t2.button || "keyup" === t2.type && "Tab" !== t2.key) return;
          const e2 = z.find(ji);
          for (const i2 of e2) {
            const e3 = Ki.getInstance(i2);
            if (!e3 || false === e3._config.autoClose) continue;
            const n2 = t2.composedPath(), s2 = n2.includes(e3._menu);
            if (n2.includes(e3._element) || "inside" === e3._config.autoClose && !s2 || "outside" === e3._config.autoClose && s2) continue;
            if (e3._menu.contains(t2.target) && ("keyup" === t2.type && "Tab" === t2.key || /input|select|option|textarea|form/i.test(t2.target.tagName))) continue;
            const o2 = { relatedTarget: e3._element };
            "click" === t2.type && (o2.clickEvent = t2), e3._completeHide(o2);
          }
        }
        static dataApiKeydownHandler(t2) {
          const e2 = /input|textarea/i.test(t2.target.tagName), i2 = "Escape" === t2.key, n2 = [Ci, Oi].includes(t2.key);
          if (!n2 && !i2) return;
          if (e2 && !i2) return;
          t2.preventDefault();
          const s2 = this.matches(Pi) ? this : z.prev(this, Pi)[0] || z.next(this, Pi)[0] || z.findOne(Pi, t2.delegateTarget.parentNode), o2 = Ki.getOrCreateInstance(s2);
          if (n2) return t2.stopPropagation(), o2.show(), void o2._selectMenuItem(t2);
          o2._isShown() && (t2.stopPropagation(), o2.hide(), s2.focus());
        }
      }
      N.on(document, $i, Pi, Ki.dataApiKeydownHandler), N.on(document, $i, Mi, Ki.dataApiKeydownHandler), N.on(document, Di, Ki.clearMenus), N.on(document, Ii, Ki.clearMenus), N.on(document, Di, Pi, function(t2) {
        t2.preventDefault(), Ki.getOrCreateInstance(this).toggle();
      }), m(Ki);
      const Qi = "backdrop", Xi = "show", Yi = `mousedown.bs.${Qi}`, Ui = { className: "modal-backdrop", clickCallback: null, isAnimated: false, isVisible: true, rootElement: "body" }, Gi = { className: "string", clickCallback: "(function|null)", isAnimated: "boolean", isVisible: "boolean", rootElement: "(element|string)" };
      class Ji extends H {
        constructor(t2) {
          super(), this._config = this._getConfig(t2), this._isAppended = false, this._element = null;
        }
        static get Default() {
          return Ui;
        }
        static get DefaultType() {
          return Gi;
        }
        static get NAME() {
          return Qi;
        }
        show(t2) {
          if (!this._config.isVisible) return void g(t2);
          this._append();
          const e2 = this._getElement();
          this._config.isAnimated && d(e2), e2.classList.add(Xi), this._emulateAnimation(() => {
            g(t2);
          });
        }
        hide(t2) {
          this._config.isVisible ? (this._getElement().classList.remove(Xi), this._emulateAnimation(() => {
            this.dispose(), g(t2);
          })) : g(t2);
        }
        dispose() {
          this._isAppended && (N.off(this._element, Yi), this._element.remove(), this._isAppended = false);
        }
        _getElement() {
          if (!this._element) {
            const t2 = document.createElement("div");
            t2.className = this._config.className, this._config.isAnimated && t2.classList.add("fade"), this._element = t2;
          }
          return this._element;
        }
        _configAfterMerge(t2) {
          return t2.rootElement = r(t2.rootElement), t2;
        }
        _append() {
          if (this._isAppended) return;
          const t2 = this._getElement();
          this._config.rootElement.append(t2), N.on(t2, Yi, () => {
            g(this._config.clickCallback);
          }), this._isAppended = true;
        }
        _emulateAnimation(t2) {
          _(t2, this._getElement(), this._config.isAnimated);
        }
      }
      const Zi = ".bs.focustrap", tn = `focusin${Zi}`, en = `keydown.tab${Zi}`, nn = "backward", sn = { autofocus: true, trapElement: null }, on = { autofocus: "boolean", trapElement: "element" };
      class rn extends H {
        constructor(t2) {
          super(), this._config = this._getConfig(t2), this._isActive = false, this._lastTabNavDirection = null;
        }
        static get Default() {
          return sn;
        }
        static get DefaultType() {
          return on;
        }
        static get NAME() {
          return "focustrap";
        }
        activate() {
          this._isActive || (this._config.autofocus && this._config.trapElement.focus(), N.off(document, Zi), N.on(document, tn, (t2) => this._handleFocusin(t2)), N.on(document, en, (t2) => this._handleKeydown(t2)), this._isActive = true);
        }
        deactivate() {
          this._isActive && (this._isActive = false, N.off(document, Zi));
        }
        _handleFocusin(t2) {
          const { trapElement: e2 } = this._config;
          if (t2.target === document || t2.target === e2 || e2.contains(t2.target)) return;
          const i2 = z.focusableChildren(e2);
          0 === i2.length ? e2.focus() : this._lastTabNavDirection === nn ? i2[i2.length - 1].focus() : i2[0].focus();
        }
        _handleKeydown(t2) {
          "Tab" === t2.key && (this._lastTabNavDirection = t2.shiftKey ? nn : "forward");
        }
      }
      const an = ".fixed-top, .fixed-bottom, .is-fixed, .sticky-top", ln = ".sticky-top", cn = "padding-right", hn = "margin-right";
      class dn {
        constructor() {
          this._element = document.body;
        }
        getWidth() {
          const t2 = document.documentElement.clientWidth;
          return Math.abs(window.innerWidth - t2);
        }
        hide() {
          const t2 = this.getWidth();
          this._disableOverFlow(), this._setElementAttributes(this._element, cn, (e2) => e2 + t2), this._setElementAttributes(an, cn, (e2) => e2 + t2), this._setElementAttributes(ln, hn, (e2) => e2 - t2);
        }
        reset() {
          this._resetElementAttributes(this._element, "overflow"), this._resetElementAttributes(this._element, cn), this._resetElementAttributes(an, cn), this._resetElementAttributes(ln, hn);
        }
        isOverflowing() {
          return this.getWidth() > 0;
        }
        _disableOverFlow() {
          this._saveInitialAttribute(this._element, "overflow"), this._element.style.overflow = "hidden";
        }
        _setElementAttributes(t2, e2, i2) {
          const n2 = this.getWidth();
          this._applyManipulationCallback(t2, (t3) => {
            if (t3 !== this._element && window.innerWidth > t3.clientWidth + n2) return;
            this._saveInitialAttribute(t3, e2);
            const s2 = window.getComputedStyle(t3).getPropertyValue(e2);
            t3.style.setProperty(e2, `${i2(Number.parseFloat(s2))}px`);
          });
        }
        _saveInitialAttribute(t2, e2) {
          const i2 = t2.style.getPropertyValue(e2);
          i2 && F.setDataAttribute(t2, e2, i2);
        }
        _resetElementAttributes(t2, e2) {
          this._applyManipulationCallback(t2, (t3) => {
            const i2 = F.getDataAttribute(t3, e2);
            null !== i2 ? (F.removeDataAttribute(t3, e2), t3.style.setProperty(e2, i2)) : t3.style.removeProperty(e2);
          });
        }
        _applyManipulationCallback(t2, e2) {
          if (o(t2)) e2(t2);
          else for (const i2 of z.find(t2, this._element)) e2(i2);
        }
      }
      const un = ".bs.modal", fn = `hide${un}`, pn = `hidePrevented${un}`, mn = `hidden${un}`, gn = `show${un}`, _n = `shown${un}`, bn = `resize${un}`, vn = `click.dismiss${un}`, yn = `mousedown.dismiss${un}`, wn = `keydown.dismiss${un}`, An = `click${un}.data-api`, En = "modal-open", Tn = "show", Cn = "modal-static", On = { backdrop: true, focus: true, keyboard: true }, xn = { backdrop: "(boolean|string)", focus: "boolean", keyboard: "boolean" };
      class kn extends W {
        constructor(t2, e2) {
          super(t2, e2), this._dialog = z.findOne(".modal-dialog", this._element), this._backdrop = this._initializeBackDrop(), this._focustrap = this._initializeFocusTrap(), this._isShown = false, this._isTransitioning = false, this._scrollBar = new dn(), this._addEventListeners();
        }
        static get Default() {
          return On;
        }
        static get DefaultType() {
          return xn;
        }
        static get NAME() {
          return "modal";
        }
        toggle(t2) {
          return this._isShown ? this.hide() : this.show(t2);
        }
        show(t2) {
          this._isShown || this._isTransitioning || N.trigger(this._element, gn, { relatedTarget: t2 }).defaultPrevented || (this._isShown = true, this._isTransitioning = true, this._scrollBar.hide(), document.body.classList.add(En), this._adjustDialog(), this._backdrop.show(() => this._showElement(t2)));
        }
        hide() {
          this._isShown && !this._isTransitioning && (N.trigger(this._element, fn).defaultPrevented || (this._isShown = false, this._isTransitioning = true, this._focustrap.deactivate(), this._element.classList.remove(Tn), this._queueCallback(() => this._hideModal(), this._element, this._isAnimated())));
        }
        dispose() {
          N.off(window, un), N.off(this._dialog, un), this._backdrop.dispose(), this._focustrap.deactivate(), super.dispose();
        }
        handleUpdate() {
          this._adjustDialog();
        }
        _initializeBackDrop() {
          return new Ji({ isVisible: Boolean(this._config.backdrop), isAnimated: this._isAnimated() });
        }
        _initializeFocusTrap() {
          return new rn({ trapElement: this._element });
        }
        _showElement(t2) {
          document.body.contains(this._element) || document.body.append(this._element), this._element.style.display = "block", this._element.removeAttribute("aria-hidden"), this._element.setAttribute("aria-modal", true), this._element.setAttribute("role", "dialog"), this._element.scrollTop = 0;
          const e2 = z.findOne(".modal-body", this._dialog);
          e2 && (e2.scrollTop = 0), d(this._element), this._element.classList.add(Tn), this._queueCallback(() => {
            this._config.focus && this._focustrap.activate(), this._isTransitioning = false, N.trigger(this._element, _n, { relatedTarget: t2 });
          }, this._dialog, this._isAnimated());
        }
        _addEventListeners() {
          N.on(this._element, wn, (t2) => {
            "Escape" === t2.key && (this._config.keyboard ? this.hide() : this._triggerBackdropTransition());
          }), N.on(window, bn, () => {
            this._isShown && !this._isTransitioning && this._adjustDialog();
          }), N.on(this._element, yn, (t2) => {
            N.one(this._element, vn, (e2) => {
              this._element === t2.target && this._element === e2.target && ("static" !== this._config.backdrop ? this._config.backdrop && this.hide() : this._triggerBackdropTransition());
            });
          });
        }
        _hideModal() {
          this._element.style.display = "none", this._element.setAttribute("aria-hidden", true), this._element.removeAttribute("aria-modal"), this._element.removeAttribute("role"), this._isTransitioning = false, this._backdrop.hide(() => {
            document.body.classList.remove(En), this._resetAdjustments(), this._scrollBar.reset(), N.trigger(this._element, mn);
          });
        }
        _isAnimated() {
          return this._element.classList.contains("fade");
        }
        _triggerBackdropTransition() {
          if (N.trigger(this._element, pn).defaultPrevented) return;
          const t2 = this._element.scrollHeight > document.documentElement.clientHeight, e2 = this._element.style.overflowY;
          "hidden" === e2 || this._element.classList.contains(Cn) || (t2 || (this._element.style.overflowY = "hidden"), this._element.classList.add(Cn), this._queueCallback(() => {
            this._element.classList.remove(Cn), this._queueCallback(() => {
              this._element.style.overflowY = e2;
            }, this._dialog);
          }, this._dialog), this._element.focus());
        }
        _adjustDialog() {
          const t2 = this._element.scrollHeight > document.documentElement.clientHeight, e2 = this._scrollBar.getWidth(), i2 = e2 > 0;
          if (i2 && !t2) {
            const t3 = p() ? "paddingLeft" : "paddingRight";
            this._element.style[t3] = `${e2}px`;
          }
          if (!i2 && t2) {
            const t3 = p() ? "paddingRight" : "paddingLeft";
            this._element.style[t3] = `${e2}px`;
          }
        }
        _resetAdjustments() {
          this._element.style.paddingLeft = "", this._element.style.paddingRight = "";
        }
        static jQueryInterface(t2, e2) {
          return this.each(function() {
            const i2 = kn.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === i2[t2]) throw new TypeError(`No method named "${t2}"`);
              i2[t2](e2);
            }
          });
        }
      }
      N.on(document, An, '[data-bs-toggle="modal"]', function(t2) {
        const e2 = z.getElementFromSelector(this);
        ["A", "AREA"].includes(this.tagName) && t2.preventDefault(), N.one(e2, gn, (t3) => {
          t3.defaultPrevented || N.one(e2, mn, () => {
            a(this) && this.focus();
          });
        });
        const i2 = z.findOne(".modal.show");
        i2 && kn.getInstance(i2).hide(), kn.getOrCreateInstance(e2).toggle(this);
      }), R(kn), m(kn);
      const Ln = ".bs.offcanvas", Sn = ".data-api", Dn = `load${Ln}${Sn}`, $n = "show", In = "showing", Nn = "hiding", Pn = ".offcanvas.show", jn = `show${Ln}`, Mn = `shown${Ln}`, Fn = `hide${Ln}`, Hn = `hidePrevented${Ln}`, Wn = `hidden${Ln}`, Bn = `resize${Ln}`, zn = `click${Ln}${Sn}`, Rn = `keydown.dismiss${Ln}`, qn = { backdrop: true, keyboard: true, scroll: false }, Vn = { backdrop: "(boolean|string)", keyboard: "boolean", scroll: "boolean" };
      class Kn extends W {
        constructor(t2, e2) {
          super(t2, e2), this._isShown = false, this._backdrop = this._initializeBackDrop(), this._focustrap = this._initializeFocusTrap(), this._addEventListeners();
        }
        static get Default() {
          return qn;
        }
        static get DefaultType() {
          return Vn;
        }
        static get NAME() {
          return "offcanvas";
        }
        toggle(t2) {
          return this._isShown ? this.hide() : this.show(t2);
        }
        show(t2) {
          this._isShown || N.trigger(this._element, jn, { relatedTarget: t2 }).defaultPrevented || (this._isShown = true, this._backdrop.show(), this._config.scroll || new dn().hide(), this._element.setAttribute("aria-modal", true), this._element.setAttribute("role", "dialog"), this._element.classList.add(In), this._queueCallback(() => {
            this._config.scroll && !this._config.backdrop || this._focustrap.activate(), this._element.classList.add($n), this._element.classList.remove(In), N.trigger(this._element, Mn, { relatedTarget: t2 });
          }, this._element, true));
        }
        hide() {
          this._isShown && (N.trigger(this._element, Fn).defaultPrevented || (this._focustrap.deactivate(), this._element.blur(), this._isShown = false, this._element.classList.add(Nn), this._backdrop.hide(), this._queueCallback(() => {
            this._element.classList.remove($n, Nn), this._element.removeAttribute("aria-modal"), this._element.removeAttribute("role"), this._config.scroll || new dn().reset(), N.trigger(this._element, Wn);
          }, this._element, true)));
        }
        dispose() {
          this._backdrop.dispose(), this._focustrap.deactivate(), super.dispose();
        }
        _initializeBackDrop() {
          const t2 = Boolean(this._config.backdrop);
          return new Ji({ className: "offcanvas-backdrop", isVisible: t2, isAnimated: true, rootElement: this._element.parentNode, clickCallback: t2 ? () => {
            "static" !== this._config.backdrop ? this.hide() : N.trigger(this._element, Hn);
          } : null });
        }
        _initializeFocusTrap() {
          return new rn({ trapElement: this._element });
        }
        _addEventListeners() {
          N.on(this._element, Rn, (t2) => {
            "Escape" === t2.key && (this._config.keyboard ? this.hide() : N.trigger(this._element, Hn));
          });
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Kn.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2] || t2.startsWith("_") || "constructor" === t2) throw new TypeError(`No method named "${t2}"`);
              e2[t2](this);
            }
          });
        }
      }
      N.on(document, zn, '[data-bs-toggle="offcanvas"]', function(t2) {
        const e2 = z.getElementFromSelector(this);
        if (["A", "AREA"].includes(this.tagName) && t2.preventDefault(), l(this)) return;
        N.one(e2, Wn, () => {
          a(this) && this.focus();
        });
        const i2 = z.findOne(Pn);
        i2 && i2 !== e2 && Kn.getInstance(i2).hide(), Kn.getOrCreateInstance(e2).toggle(this);
      }), N.on(window, Dn, () => {
        for (const t2 of z.find(Pn)) Kn.getOrCreateInstance(t2).show();
      }), N.on(window, Bn, () => {
        for (const t2 of z.find("[aria-modal][class*=show][class*=offcanvas-]")) "fixed" !== getComputedStyle(t2).position && Kn.getOrCreateInstance(t2).hide();
      }), R(Kn), m(Kn);
      const Qn = { "*": ["class", "dir", "id", "lang", "role", /^aria-[\w-]*$/i], a: ["target", "href", "title", "rel"], area: [], b: [], br: [], col: [], code: [], dd: [], div: [], dl: [], dt: [], em: [], hr: [], h1: [], h2: [], h3: [], h4: [], h5: [], h6: [], i: [], img: ["src", "srcset", "alt", "title", "width", "height"], li: [], ol: [], p: [], pre: [], s: [], small: [], span: [], sub: [], sup: [], strong: [], u: [], ul: [] }, Xn = /* @__PURE__ */ new Set(["background", "cite", "href", "itemtype", "longdesc", "poster", "src", "xlink:href"]), Yn = /^(?!javascript:)(?:[a-z0-9+.-]+:|[^&:/?#]*(?:[/?#]|$))/i, Un = (t2, e2) => {
        const i2 = t2.nodeName.toLowerCase();
        return e2.includes(i2) ? !Xn.has(i2) || Boolean(Yn.test(t2.nodeValue)) : e2.filter((t3) => t3 instanceof RegExp).some((t3) => t3.test(i2));
      }, Gn = { allowList: Qn, content: {}, extraClass: "", html: false, sanitize: true, sanitizeFn: null, template: "<div></div>" }, Jn = { allowList: "object", content: "object", extraClass: "(string|function)", html: "boolean", sanitize: "boolean", sanitizeFn: "(null|function)", template: "string" }, Zn = { entry: "(string|element|function|null)", selector: "(string|element)" };
      class ts extends H {
        constructor(t2) {
          super(), this._config = this._getConfig(t2);
        }
        static get Default() {
          return Gn;
        }
        static get DefaultType() {
          return Jn;
        }
        static get NAME() {
          return "TemplateFactory";
        }
        getContent() {
          return Object.values(this._config.content).map((t2) => this._resolvePossibleFunction(t2)).filter(Boolean);
        }
        hasContent() {
          return this.getContent().length > 0;
        }
        changeContent(t2) {
          return this._checkContent(t2), this._config.content = { ...this._config.content, ...t2 }, this;
        }
        toHtml() {
          const t2 = document.createElement("div");
          t2.innerHTML = this._maybeSanitize(this._config.template);
          for (const [e3, i3] of Object.entries(this._config.content)) this._setContent(t2, i3, e3);
          const e2 = t2.children[0], i2 = this._resolvePossibleFunction(this._config.extraClass);
          return i2 && e2.classList.add(...i2.split(" ")), e2;
        }
        _typeCheckConfig(t2) {
          super._typeCheckConfig(t2), this._checkContent(t2.content);
        }
        _checkContent(t2) {
          for (const [e2, i2] of Object.entries(t2)) super._typeCheckConfig({ selector: e2, entry: i2 }, Zn);
        }
        _setContent(t2, e2, i2) {
          const n2 = z.findOne(i2, t2);
          n2 && ((e2 = this._resolvePossibleFunction(e2)) ? o(e2) ? this._putElementInTemplate(r(e2), n2) : this._config.html ? n2.innerHTML = this._maybeSanitize(e2) : n2.textContent = e2 : n2.remove());
        }
        _maybeSanitize(t2) {
          return this._config.sanitize ? function(t3, e2, i2) {
            if (!t3.length) return t3;
            if (i2 && "function" == typeof i2) return i2(t3);
            const n2 = new window.DOMParser().parseFromString(t3, "text/html"), s2 = [].concat(...n2.body.querySelectorAll("*"));
            for (const t4 of s2) {
              const i3 = t4.nodeName.toLowerCase();
              if (!Object.keys(e2).includes(i3)) {
                t4.remove();
                continue;
              }
              const n3 = [].concat(...t4.attributes), s3 = [].concat(e2["*"] || [], e2[i3] || []);
              for (const e3 of n3) Un(e3, s3) || t4.removeAttribute(e3.nodeName);
            }
            return n2.body.innerHTML;
          }(t2, this._config.allowList, this._config.sanitizeFn) : t2;
        }
        _resolvePossibleFunction(t2) {
          return g(t2, [void 0, this]);
        }
        _putElementInTemplate(t2, e2) {
          if (this._config.html) return e2.innerHTML = "", void e2.append(t2);
          e2.textContent = t2.textContent;
        }
      }
      const es = /* @__PURE__ */ new Set(["sanitize", "allowList", "sanitizeFn"]), is = "fade", ns = "show", ss = ".tooltip-inner", os = ".modal", rs = "hide.bs.modal", as = "hover", ls = "focus", cs = "click", hs = { AUTO: "auto", TOP: "top", RIGHT: p() ? "left" : "right", BOTTOM: "bottom", LEFT: p() ? "right" : "left" }, ds = { allowList: Qn, animation: true, boundary: "clippingParents", container: false, customClass: "", delay: 0, fallbackPlacements: ["top", "right", "bottom", "left"], html: false, offset: [0, 6], placement: "top", popperConfig: null, sanitize: true, sanitizeFn: null, selector: false, template: '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>', title: "", trigger: "hover focus" }, us = { allowList: "object", animation: "boolean", boundary: "(string|element)", container: "(string|element|boolean)", customClass: "(string|function)", delay: "(number|object)", fallbackPlacements: "array", html: "boolean", offset: "(array|string|function)", placement: "(string|function)", popperConfig: "(null|object|function)", sanitize: "boolean", sanitizeFn: "(null|function)", selector: "(string|boolean)", template: "string", title: "(string|element|function)", trigger: "string" };
      class fs extends W {
        constructor(t2, e2) {
          if (void 0 === wi) throw new TypeError("Bootstrap's tooltips require Popper (https://popper.js.org/docs/v2/)");
          super(t2, e2), this._isEnabled = true, this._timeout = 0, this._isHovered = null, this._activeTrigger = {}, this._popper = null, this._templateFactory = null, this._newContent = null, this.tip = null, this._setListeners(), this._config.selector || this._fixTitle();
        }
        static get Default() {
          return ds;
        }
        static get DefaultType() {
          return us;
        }
        static get NAME() {
          return "tooltip";
        }
        enable() {
          this._isEnabled = true;
        }
        disable() {
          this._isEnabled = false;
        }
        toggleEnabled() {
          this._isEnabled = !this._isEnabled;
        }
        toggle() {
          this._isEnabled && (this._isShown() ? this._leave() : this._enter());
        }
        dispose() {
          clearTimeout(this._timeout), N.off(this._element.closest(os), rs, this._hideModalHandler), this._element.getAttribute("data-bs-original-title") && this._element.setAttribute("title", this._element.getAttribute("data-bs-original-title")), this._disposePopper(), super.dispose();
        }
        show() {
          if ("none" === this._element.style.display) throw new Error("Please use show on visible elements");
          if (!this._isWithContent() || !this._isEnabled) return;
          const t2 = N.trigger(this._element, this.constructor.eventName("show")), e2 = (c(this._element) || this._element.ownerDocument.documentElement).contains(this._element);
          if (t2.defaultPrevented || !e2) return;
          this._disposePopper();
          const i2 = this._getTipElement();
          this._element.setAttribute("aria-describedby", i2.getAttribute("id"));
          const { container: n2 } = this._config;
          if (this._element.ownerDocument.documentElement.contains(this.tip) || (n2.append(i2), N.trigger(this._element, this.constructor.eventName("inserted"))), this._popper = this._createPopper(i2), i2.classList.add(ns), "ontouchstart" in document.documentElement) for (const t3 of [].concat(...document.body.children)) N.on(t3, "mouseover", h);
          this._queueCallback(() => {
            N.trigger(this._element, this.constructor.eventName("shown")), false === this._isHovered && this._leave(), this._isHovered = false;
          }, this.tip, this._isAnimated());
        }
        hide() {
          if (this._isShown() && !N.trigger(this._element, this.constructor.eventName("hide")).defaultPrevented) {
            if (this._getTipElement().classList.remove(ns), "ontouchstart" in document.documentElement) for (const t2 of [].concat(...document.body.children)) N.off(t2, "mouseover", h);
            this._activeTrigger[cs] = false, this._activeTrigger[ls] = false, this._activeTrigger[as] = false, this._isHovered = null, this._queueCallback(() => {
              this._isWithActiveTrigger() || (this._isHovered || this._disposePopper(), this._element.removeAttribute("aria-describedby"), N.trigger(this._element, this.constructor.eventName("hidden")));
            }, this.tip, this._isAnimated());
          }
        }
        update() {
          this._popper && this._popper.update();
        }
        _isWithContent() {
          return Boolean(this._getTitle());
        }
        _getTipElement() {
          return this.tip || (this.tip = this._createTipElement(this._newContent || this._getContentForTemplate())), this.tip;
        }
        _createTipElement(t2) {
          const e2 = this._getTemplateFactory(t2).toHtml();
          if (!e2) return null;
          e2.classList.remove(is, ns), e2.classList.add(`bs-${this.constructor.NAME}-auto`);
          const i2 = ((t3) => {
            do {
              t3 += Math.floor(1e6 * Math.random());
            } while (document.getElementById(t3));
            return t3;
          })(this.constructor.NAME).toString();
          return e2.setAttribute("id", i2), this._isAnimated() && e2.classList.add(is), e2;
        }
        setContent(t2) {
          this._newContent = t2, this._isShown() && (this._disposePopper(), this.show());
        }
        _getTemplateFactory(t2) {
          return this._templateFactory ? this._templateFactory.changeContent(t2) : this._templateFactory = new ts({ ...this._config, content: t2, extraClass: this._resolvePossibleFunction(this._config.customClass) }), this._templateFactory;
        }
        _getContentForTemplate() {
          return { [ss]: this._getTitle() };
        }
        _getTitle() {
          return this._resolvePossibleFunction(this._config.title) || this._element.getAttribute("data-bs-original-title");
        }
        _initializeOnDelegatedTarget(t2) {
          return this.constructor.getOrCreateInstance(t2.delegateTarget, this._getDelegateConfig());
        }
        _isAnimated() {
          return this._config.animation || this.tip && this.tip.classList.contains(is);
        }
        _isShown() {
          return this.tip && this.tip.classList.contains(ns);
        }
        _createPopper(t2) {
          const e2 = g(this._config.placement, [this, t2, this._element]), i2 = hs[e2.toUpperCase()];
          return yi(this._element, t2, this._getPopperConfig(i2));
        }
        _getOffset() {
          const { offset: t2 } = this._config;
          return "string" == typeof t2 ? t2.split(",").map((t3) => Number.parseInt(t3, 10)) : "function" == typeof t2 ? (e2) => t2(e2, this._element) : t2;
        }
        _resolvePossibleFunction(t2) {
          return g(t2, [this._element, this._element]);
        }
        _getPopperConfig(t2) {
          const e2 = { placement: t2, modifiers: [{ name: "flip", options: { fallbackPlacements: this._config.fallbackPlacements } }, { name: "offset", options: { offset: this._getOffset() } }, { name: "preventOverflow", options: { boundary: this._config.boundary } }, { name: "arrow", options: { element: `.${this.constructor.NAME}-arrow` } }, { name: "preSetPlacement", enabled: true, phase: "beforeMain", fn: (t3) => {
            this._getTipElement().setAttribute("data-popper-placement", t3.state.placement);
          } }] };
          return { ...e2, ...g(this._config.popperConfig, [void 0, e2]) };
        }
        _setListeners() {
          const t2 = this._config.trigger.split(" ");
          for (const e2 of t2) if ("click" === e2) N.on(this._element, this.constructor.eventName("click"), this._config.selector, (t3) => {
            const e3 = this._initializeOnDelegatedTarget(t3);
            e3._activeTrigger[cs] = !(e3._isShown() && e3._activeTrigger[cs]), e3.toggle();
          });
          else if ("manual" !== e2) {
            const t3 = e2 === as ? this.constructor.eventName("mouseenter") : this.constructor.eventName("focusin"), i2 = e2 === as ? this.constructor.eventName("mouseleave") : this.constructor.eventName("focusout");
            N.on(this._element, t3, this._config.selector, (t4) => {
              const e3 = this._initializeOnDelegatedTarget(t4);
              e3._activeTrigger["focusin" === t4.type ? ls : as] = true, e3._enter();
            }), N.on(this._element, i2, this._config.selector, (t4) => {
              const e3 = this._initializeOnDelegatedTarget(t4);
              e3._activeTrigger["focusout" === t4.type ? ls : as] = e3._element.contains(t4.relatedTarget), e3._leave();
            });
          }
          this._hideModalHandler = () => {
            this._element && this.hide();
          }, N.on(this._element.closest(os), rs, this._hideModalHandler);
        }
        _fixTitle() {
          const t2 = this._element.getAttribute("title");
          t2 && (this._element.getAttribute("aria-label") || this._element.textContent.trim() || this._element.setAttribute("aria-label", t2), this._element.setAttribute("data-bs-original-title", t2), this._element.removeAttribute("title"));
        }
        _enter() {
          this._isShown() || this._isHovered ? this._isHovered = true : (this._isHovered = true, this._setTimeout(() => {
            this._isHovered && this.show();
          }, this._config.delay.show));
        }
        _leave() {
          this._isWithActiveTrigger() || (this._isHovered = false, this._setTimeout(() => {
            this._isHovered || this.hide();
          }, this._config.delay.hide));
        }
        _setTimeout(t2, e2) {
          clearTimeout(this._timeout), this._timeout = setTimeout(t2, e2);
        }
        _isWithActiveTrigger() {
          return Object.values(this._activeTrigger).includes(true);
        }
        _getConfig(t2) {
          const e2 = F.getDataAttributes(this._element);
          for (const t3 of Object.keys(e2)) es.has(t3) && delete e2[t3];
          return t2 = { ...e2, ..."object" == typeof t2 && t2 ? t2 : {} }, t2 = this._mergeConfigObj(t2), t2 = this._configAfterMerge(t2), this._typeCheckConfig(t2), t2;
        }
        _configAfterMerge(t2) {
          return t2.container = false === t2.container ? document.body : r(t2.container), "number" == typeof t2.delay && (t2.delay = { show: t2.delay, hide: t2.delay }), "number" == typeof t2.title && (t2.title = t2.title.toString()), "number" == typeof t2.content && (t2.content = t2.content.toString()), t2;
        }
        _getDelegateConfig() {
          const t2 = {};
          for (const [e2, i2] of Object.entries(this._config)) this.constructor.Default[e2] !== i2 && (t2[e2] = i2);
          return t2.selector = false, t2.trigger = "manual", t2;
        }
        _disposePopper() {
          this._popper && (this._popper.destroy(), this._popper = null), this.tip && (this.tip.remove(), this.tip = null);
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = fs.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2]) throw new TypeError(`No method named "${t2}"`);
              e2[t2]();
            }
          });
        }
      }
      m(fs);
      const ps = ".popover-header", ms = ".popover-body", gs = { ...fs.Default, content: "", offset: [0, 8], placement: "right", template: '<div class="popover" role="tooltip"><div class="popover-arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>', trigger: "click" }, _s = { ...fs.DefaultType, content: "(null|string|element|function)" };
      class bs extends fs {
        static get Default() {
          return gs;
        }
        static get DefaultType() {
          return _s;
        }
        static get NAME() {
          return "popover";
        }
        _isWithContent() {
          return this._getTitle() || this._getContent();
        }
        _getContentForTemplate() {
          return { [ps]: this._getTitle(), [ms]: this._getContent() };
        }
        _getContent() {
          return this._resolvePossibleFunction(this._config.content);
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = bs.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2]) throw new TypeError(`No method named "${t2}"`);
              e2[t2]();
            }
          });
        }
      }
      m(bs);
      const vs = ".bs.scrollspy", ys = `activate${vs}`, ws = `click${vs}`, As = `load${vs}.data-api`, Es = "active", Ts = "[href]", Cs = ".nav-link", Os = `${Cs}, .nav-item > ${Cs}, .list-group-item`, xs = { offset: null, rootMargin: "0px 0px -25%", smoothScroll: false, target: null, threshold: [0.1, 0.5, 1] }, ks = { offset: "(number|null)", rootMargin: "string", smoothScroll: "boolean", target: "element", threshold: "array" };
      class Ls extends W {
        constructor(t2, e2) {
          super(t2, e2), this._targetLinks = /* @__PURE__ */ new Map(), this._observableSections = /* @__PURE__ */ new Map(), this._rootElement = "visible" === getComputedStyle(this._element).overflowY ? null : this._element, this._activeTarget = null, this._observer = null, this._previousScrollData = { visibleEntryTop: 0, parentScrollTop: 0 }, this.refresh();
        }
        static get Default() {
          return xs;
        }
        static get DefaultType() {
          return ks;
        }
        static get NAME() {
          return "scrollspy";
        }
        refresh() {
          this._initializeTargetsAndObservables(), this._maybeEnableSmoothScroll(), this._observer ? this._observer.disconnect() : this._observer = this._getNewObserver();
          for (const t2 of this._observableSections.values()) this._observer.observe(t2);
        }
        dispose() {
          this._observer.disconnect(), super.dispose();
        }
        _configAfterMerge(t2) {
          return t2.target = r(t2.target) || document.body, t2.rootMargin = t2.offset ? `${t2.offset}px 0px -30%` : t2.rootMargin, "string" == typeof t2.threshold && (t2.threshold = t2.threshold.split(",").map((t3) => Number.parseFloat(t3))), t2;
        }
        _maybeEnableSmoothScroll() {
          this._config.smoothScroll && (N.off(this._config.target, ws), N.on(this._config.target, ws, Ts, (t2) => {
            const e2 = this._observableSections.get(t2.target.hash);
            if (e2) {
              t2.preventDefault();
              const i2 = this._rootElement || window, n2 = e2.offsetTop - this._element.offsetTop;
              if (i2.scrollTo) return void i2.scrollTo({ top: n2, behavior: "smooth" });
              i2.scrollTop = n2;
            }
          }));
        }
        _getNewObserver() {
          const t2 = { root: this._rootElement, threshold: this._config.threshold, rootMargin: this._config.rootMargin };
          return new IntersectionObserver((t3) => this._observerCallback(t3), t2);
        }
        _observerCallback(t2) {
          const e2 = (t3) => this._targetLinks.get(`#${t3.target.id}`), i2 = (t3) => {
            this._previousScrollData.visibleEntryTop = t3.target.offsetTop, this._process(e2(t3));
          }, n2 = (this._rootElement || document.documentElement).scrollTop, s2 = n2 >= this._previousScrollData.parentScrollTop;
          this._previousScrollData.parentScrollTop = n2;
          for (const o2 of t2) {
            if (!o2.isIntersecting) {
              this._activeTarget = null, this._clearActiveClass(e2(o2));
              continue;
            }
            const t3 = o2.target.offsetTop >= this._previousScrollData.visibleEntryTop;
            if (s2 && t3) {
              if (i2(o2), !n2) return;
            } else s2 || t3 || i2(o2);
          }
        }
        _initializeTargetsAndObservables() {
          this._targetLinks = /* @__PURE__ */ new Map(), this._observableSections = /* @__PURE__ */ new Map();
          const t2 = z.find(Ts, this._config.target);
          for (const e2 of t2) {
            if (!e2.hash || l(e2)) continue;
            const t3 = z.findOne(decodeURI(e2.hash), this._element);
            a(t3) && (this._targetLinks.set(decodeURI(e2.hash), e2), this._observableSections.set(e2.hash, t3));
          }
        }
        _process(t2) {
          this._activeTarget !== t2 && (this._clearActiveClass(this._config.target), this._activeTarget = t2, t2.classList.add(Es), this._activateParents(t2), N.trigger(this._element, ys, { relatedTarget: t2 }));
        }
        _activateParents(t2) {
          if (t2.classList.contains("dropdown-item")) z.findOne(".dropdown-toggle", t2.closest(".dropdown")).classList.add(Es);
          else for (const e2 of z.parents(t2, ".nav, .list-group")) for (const t3 of z.prev(e2, Os)) t3.classList.add(Es);
        }
        _clearActiveClass(t2) {
          t2.classList.remove(Es);
          const e2 = z.find(`${Ts}.${Es}`, t2);
          for (const t3 of e2) t3.classList.remove(Es);
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Ls.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2] || t2.startsWith("_") || "constructor" === t2) throw new TypeError(`No method named "${t2}"`);
              e2[t2]();
            }
          });
        }
      }
      N.on(window, As, () => {
        for (const t2 of z.find('[data-bs-spy="scroll"]')) Ls.getOrCreateInstance(t2);
      }), m(Ls);
      const Ss = ".bs.tab", Ds = `hide${Ss}`, $s = `hidden${Ss}`, Is = `show${Ss}`, Ns = `shown${Ss}`, Ps = `click${Ss}`, js = `keydown${Ss}`, Ms = `load${Ss}`, Fs = "ArrowLeft", Hs = "ArrowRight", Ws = "ArrowUp", Bs = "ArrowDown", zs = "Home", Rs = "End", qs = "active", Vs = "fade", Ks = "show", Qs = ".dropdown-toggle", Xs = `:not(${Qs})`, Ys = '[data-bs-toggle="tab"], [data-bs-toggle="pill"], [data-bs-toggle="list"]', Us = `.nav-link${Xs}, .list-group-item${Xs}, [role="tab"]${Xs}, ${Ys}`, Gs = `.${qs}[data-bs-toggle="tab"], .${qs}[data-bs-toggle="pill"], .${qs}[data-bs-toggle="list"]`;
      class Js extends W {
        constructor(t2) {
          super(t2), this._parent = this._element.closest('.list-group, .nav, [role="tablist"]'), this._parent && (this._setInitialAttributes(this._parent, this._getChildren()), N.on(this._element, js, (t3) => this._keydown(t3)));
        }
        static get NAME() {
          return "tab";
        }
        show() {
          const t2 = this._element;
          if (this._elemIsActive(t2)) return;
          const e2 = this._getActiveElem(), i2 = e2 ? N.trigger(e2, Ds, { relatedTarget: t2 }) : null;
          N.trigger(t2, Is, { relatedTarget: e2 }).defaultPrevented || i2 && i2.defaultPrevented || (this._deactivate(e2, t2), this._activate(t2, e2));
        }
        _activate(t2, e2) {
          t2 && (t2.classList.add(qs), this._activate(z.getElementFromSelector(t2)), this._queueCallback(() => {
            "tab" === t2.getAttribute("role") ? (t2.removeAttribute("tabindex"), t2.setAttribute("aria-selected", true), this._toggleDropDown(t2, true), N.trigger(t2, Ns, { relatedTarget: e2 })) : t2.classList.add(Ks);
          }, t2, t2.classList.contains(Vs)));
        }
        _deactivate(t2, e2) {
          t2 && (t2.classList.remove(qs), t2.blur(), this._deactivate(z.getElementFromSelector(t2)), this._queueCallback(() => {
            "tab" === t2.getAttribute("role") ? (t2.setAttribute("aria-selected", false), t2.setAttribute("tabindex", "-1"), this._toggleDropDown(t2, false), N.trigger(t2, $s, { relatedTarget: e2 })) : t2.classList.remove(Ks);
          }, t2, t2.classList.contains(Vs)));
        }
        _keydown(t2) {
          if (![Fs, Hs, Ws, Bs, zs, Rs].includes(t2.key)) return;
          t2.stopPropagation(), t2.preventDefault();
          const e2 = this._getChildren().filter((t3) => !l(t3));
          let i2;
          if ([zs, Rs].includes(t2.key)) i2 = e2[t2.key === zs ? 0 : e2.length - 1];
          else {
            const n2 = [Hs, Bs].includes(t2.key);
            i2 = b(e2, t2.target, n2, true);
          }
          i2 && (i2.focus({ preventScroll: true }), Js.getOrCreateInstance(i2).show());
        }
        _getChildren() {
          return z.find(Us, this._parent);
        }
        _getActiveElem() {
          return this._getChildren().find((t2) => this._elemIsActive(t2)) || null;
        }
        _setInitialAttributes(t2, e2) {
          this._setAttributeIfNotExists(t2, "role", "tablist");
          for (const t3 of e2) this._setInitialAttributesOnChild(t3);
        }
        _setInitialAttributesOnChild(t2) {
          t2 = this._getInnerElement(t2);
          const e2 = this._elemIsActive(t2), i2 = this._getOuterElement(t2);
          t2.setAttribute("aria-selected", e2), i2 !== t2 && this._setAttributeIfNotExists(i2, "role", "presentation"), e2 || t2.setAttribute("tabindex", "-1"), this._setAttributeIfNotExists(t2, "role", "tab"), this._setInitialAttributesOnTargetPanel(t2);
        }
        _setInitialAttributesOnTargetPanel(t2) {
          const e2 = z.getElementFromSelector(t2);
          e2 && (this._setAttributeIfNotExists(e2, "role", "tabpanel"), t2.id && this._setAttributeIfNotExists(e2, "aria-labelledby", `${t2.id}`));
        }
        _toggleDropDown(t2, e2) {
          const i2 = this._getOuterElement(t2);
          if (!i2.classList.contains("dropdown")) return;
          const n2 = (t3, n3) => {
            const s2 = z.findOne(t3, i2);
            s2 && s2.classList.toggle(n3, e2);
          };
          n2(Qs, qs), n2(".dropdown-menu", Ks), i2.setAttribute("aria-expanded", e2);
        }
        _setAttributeIfNotExists(t2, e2, i2) {
          t2.hasAttribute(e2) || t2.setAttribute(e2, i2);
        }
        _elemIsActive(t2) {
          return t2.classList.contains(qs);
        }
        _getInnerElement(t2) {
          return t2.matches(Us) ? t2 : z.findOne(Us, t2);
        }
        _getOuterElement(t2) {
          return t2.closest(".nav-item, .list-group-item") || t2;
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = Js.getOrCreateInstance(this);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2] || t2.startsWith("_") || "constructor" === t2) throw new TypeError(`No method named "${t2}"`);
              e2[t2]();
            }
          });
        }
      }
      N.on(document, Ps, Ys, function(t2) {
        ["A", "AREA"].includes(this.tagName) && t2.preventDefault(), l(this) || Js.getOrCreateInstance(this).show();
      }), N.on(window, Ms, () => {
        for (const t2 of z.find(Gs)) Js.getOrCreateInstance(t2);
      }), m(Js);
      const Zs = ".bs.toast", to = `mouseover${Zs}`, eo = `mouseout${Zs}`, io = `focusin${Zs}`, no = `focusout${Zs}`, so = `hide${Zs}`, oo = `hidden${Zs}`, ro = `show${Zs}`, ao = `shown${Zs}`, lo = "hide", co = "show", ho = "showing", uo = { animation: "boolean", autohide: "boolean", delay: "number" }, fo = { animation: true, autohide: true, delay: 5e3 };
      class po extends W {
        constructor(t2, e2) {
          super(t2, e2), this._timeout = null, this._hasMouseInteraction = false, this._hasKeyboardInteraction = false, this._setListeners();
        }
        static get Default() {
          return fo;
        }
        static get DefaultType() {
          return uo;
        }
        static get NAME() {
          return "toast";
        }
        show() {
          N.trigger(this._element, ro).defaultPrevented || (this._clearTimeout(), this._config.animation && this._element.classList.add("fade"), this._element.classList.remove(lo), d(this._element), this._element.classList.add(co, ho), this._queueCallback(() => {
            this._element.classList.remove(ho), N.trigger(this._element, ao), this._maybeScheduleHide();
          }, this._element, this._config.animation));
        }
        hide() {
          this.isShown() && (N.trigger(this._element, so).defaultPrevented || (this._element.classList.add(ho), this._queueCallback(() => {
            this._element.classList.add(lo), this._element.classList.remove(ho, co), N.trigger(this._element, oo);
          }, this._element, this._config.animation)));
        }
        dispose() {
          this._clearTimeout(), this.isShown() && this._element.classList.remove(co), super.dispose();
        }
        isShown() {
          return this._element.classList.contains(co);
        }
        _maybeScheduleHide() {
          this._config.autohide && (this._hasMouseInteraction || this._hasKeyboardInteraction || (this._timeout = setTimeout(() => {
            this.hide();
          }, this._config.delay)));
        }
        _onInteraction(t2, e2) {
          switch (t2.type) {
            case "mouseover":
            case "mouseout":
              this._hasMouseInteraction = e2;
              break;
            case "focusin":
            case "focusout":
              this._hasKeyboardInteraction = e2;
          }
          if (e2) return void this._clearTimeout();
          const i2 = t2.relatedTarget;
          this._element === i2 || this._element.contains(i2) || this._maybeScheduleHide();
        }
        _setListeners() {
          N.on(this._element, to, (t2) => this._onInteraction(t2, true)), N.on(this._element, eo, (t2) => this._onInteraction(t2, false)), N.on(this._element, io, (t2) => this._onInteraction(t2, true)), N.on(this._element, no, (t2) => this._onInteraction(t2, false));
        }
        _clearTimeout() {
          clearTimeout(this._timeout), this._timeout = null;
        }
        static jQueryInterface(t2) {
          return this.each(function() {
            const e2 = po.getOrCreateInstance(this, t2);
            if ("string" == typeof t2) {
              if (void 0 === e2[t2]) throw new TypeError(`No method named "${t2}"`);
              e2[t2](this);
            }
          });
        }
      }
      return R(po), m(po), { Alert: Q, Button: Y, Carousel: Lt, Collapse: Rt, Dropdown: Ki, Modal: kn, Offcanvas: Kn, Popover: bs, ScrollSpy: Ls, Tab: Js, Toast: po, Tooltip: fs };
    });
  })(bootstrap_bundle_min$1);
  return bootstrap_bundle_min$1.exports;
}
requireBootstrap_bundle_min();
const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};
const _sfc_main$1 = {
  name: "App",
  data() {
    return {
      appVersion: "0.5.8",
      currentYear: (/* @__PURE__ */ new Date()).getFullYear()
    };
  }
};
const _hoisted_1$1 = { id: "app" };
const _hoisted_2$1 = {
  class: "navbar navbar-expand-lg navbar-dark",
  style: { "background": "linear-gradient(90deg, #4b2e83 60%, #6a4c93 100%)" }
};
const _hoisted_3$1 = { class: "container" };
const _hoisted_4$1 = {
  class: "collapse navbar-collapse",
  id: "navbarNav"
};
const _hoisted_5 = { class: "navbar-nav me-auto" };
const _hoisted_6 = { class: "nav-item" };
const _hoisted_7 = { class: "nav-item" };
const _hoisted_8 = { class: "nav-item" };
const _hoisted_9 = { class: "nav-item d-none d-lg-block" };
const _hoisted_10 = { class: "nav-item d-none d-lg-block" };
const _hoisted_11 = { class: "d-flex align-items-center" };
const _hoisted_12 = { class: "navbar-text text-light me-2 d-none d-sm-inline" };
const _hoisted_13 = { class: "container-fluid container-lg py-3 py-md-4" };
const _hoisted_14 = { class: "bg-light py-4 mt-5" };
const _hoisted_15 = { class: "container" };
const _hoisted_16 = { class: "row g-4" };
const _hoisted_17 = { class: "col-6 col-md-3" };
const _hoisted_18 = { class: "list-unstyled" };
const _hoisted_19 = { class: "text-center text-muted" };
const _hoisted_20 = { class: "mb-0" };
function _sfc_render$1(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = resolveComponent("router-link");
  const _component_router_view = resolveComponent("router-view");
  return openBlock(), createElementBlock("div", _hoisted_1$1, [
    createBaseVNode("nav", _hoisted_2$1, [
      createBaseVNode("div", _hoisted_3$1, [
        createVNode(_component_router_link, {
          class: "navbar-brand",
          to: "/"
        }, {
          default: withCtx(() => _cache[0] || (_cache[0] = [
            createBaseVNode("i", { class: "bi bi-journal-check me-2" }, null, -1),
            createBaseVNode("span", { class: "d-none d-sm-inline" }, "CaseStrainer", -1),
            createBaseVNode("span", { class: "d-inline d-sm-none" }, "CS", -1)
          ])),
          _: 1,
          __: [0]
        }),
        _cache[7] || (_cache[7] = createBaseVNode("div", { class: "header-banner mt-1" }, [
          createBaseVNode("span", { class: "header-banner-text" }, " Free, Open-Source, and No Generative AI - Experimental - Use at Your Own Risk ")
        ], -1)),
        _cache[8] || (_cache[8] = createBaseVNode("button", {
          class: "navbar-toggler",
          type: "button",
          "data-bs-toggle": "collapse",
          "data-bs-target": "#navbarNav",
          "aria-controls": "navbarNav",
          "aria-expanded": "false",
          "aria-label": "Toggle navigation"
        }, [
          createBaseVNode("span", { class: "navbar-toggler-icon" })
        ], -1)),
        createBaseVNode("div", _hoisted_4$1, [
          createBaseVNode("ul", _hoisted_5, [
            createBaseVNode("li", _hoisted_6, [
              createVNode(_component_router_link, {
                class: "nav-link",
                to: "/"
              }, {
                default: withCtx(() => _cache[1] || (_cache[1] = [
                  createBaseVNode("i", { class: "bi bi-house-door me-1" }, null, -1),
                  createBaseVNode("span", { class: "d-none d-md-inline" }, "Home", -1)
                ])),
                _: 1,
                __: [1]
              })
            ]),
            createBaseVNode("li", _hoisted_7, [
              createVNode(_component_router_link, {
                class: "nav-link",
                to: "/docs"
              }, {
                default: withCtx(() => _cache[2] || (_cache[2] = [
                  createBaseVNode("i", { class: "bi bi-journal-bookmark me-1" }, null, -1),
                  createBaseVNode("span", { class: "d-none d-md-inline" }, "Docs", -1)
                ])),
                _: 1,
                __: [2]
              })
            ]),
            createBaseVNode("li", _hoisted_8, [
              createVNode(_component_router_link, {
                class: "nav-link",
                to: "/docs/api"
              }, {
                default: withCtx(() => _cache[3] || (_cache[3] = [
                  createBaseVNode("i", { class: "bi bi-code-slash me-1" }, null, -1),
                  createBaseVNode("span", { class: "d-none d-md-inline" }, "API Docs", -1)
                ])),
                _: 1,
                __: [3]
              })
            ]),
            createBaseVNode("li", _hoisted_9, [
              createVNode(_component_router_link, {
                class: "nav-link",
                to: "/browser-extension"
              }, {
                default: withCtx(() => _cache[4] || (_cache[4] = [
                  createBaseVNode("i", { class: "bi bi-puzzle me-1" }, null, -1),
                  createTextVNode(" Browser Extension ")
                ])),
                _: 1,
                __: [4]
              })
            ]),
            createBaseVNode("li", _hoisted_10, [
              createVNode(_component_router_link, {
                class: "nav-link",
                to: "/word-plugin"
              }, {
                default: withCtx(() => _cache[5] || (_cache[5] = [
                  createBaseVNode("i", { class: "bi bi-file-earmark-word me-1" }, null, -1),
                  createTextVNode(" Word Plug-in ")
                ])),
                _: 1,
                __: [5]
              })
            ])
          ]),
          createBaseVNode("div", _hoisted_11, [
            createBaseVNode("span", _hoisted_12, " v" + toDisplayString($data.appVersion), 1),
            _cache[6] || (_cache[6] = createBaseVNode("a", {
              href: "https://github.com/jafrank88/casestrainer",
              target: "_blank",
              class: "btn btn-outline-light btn-sm"
            }, [
              createBaseVNode("i", { class: "bi bi-github me-1" }),
              createBaseVNode("span", { class: "d-none d-sm-inline" }, "GitHub")
            ], -1))
          ])
        ])
      ])
    ]),
    createBaseVNode("main", _hoisted_13, [
      createVNode(_component_router_view, null, {
        default: withCtx(({ Component }) => [
          createVNode(Transition, {
            name: "fade",
            mode: "out-in"
          }, {
            default: withCtx(() => [
              (openBlock(), createBlock(resolveDynamicComponent(Component)))
            ]),
            _: 2
          }, 1024)
        ]),
        _: 1
      })
    ]),
    createBaseVNode("footer", _hoisted_14, [
      createBaseVNode("div", _hoisted_15, [
        createBaseVNode("div", _hoisted_16, [
          _cache[13] || (_cache[13] = createBaseVNode("div", { class: "col-12 col-md-6" }, [
            createBaseVNode("h5", null, "About CaseStrainer"),
            createBaseVNode("p", { class: "text-muted" }, " A powerful tool for legal professionals to validate, analyze, and manage legal citations. ")
          ], -1)),
          createBaseVNode("div", _hoisted_17, [
            _cache[12] || (_cache[12] = createBaseVNode("h5", null, "Quick Links", -1)),
            createBaseVNode("ul", _hoisted_18, [
              createBaseVNode("li", null, [
                createVNode(_component_router_link, {
                  to: "/",
                  class: "text-decoration-none"
                }, {
                  default: withCtx(() => _cache[9] || (_cache[9] = [
                    createTextVNode("Home")
                  ])),
                  _: 1,
                  __: [9]
                })
              ]),
              createBaseVNode("li", null, [
                createVNode(_component_router_link, {
                  to: "/docs",
                  class: "text-decoration-none"
                }, {
                  default: withCtx(() => _cache[10] || (_cache[10] = [
                    createTextVNode("Docs")
                  ])),
                  _: 1,
                  __: [10]
                })
              ]),
              createBaseVNode("li", null, [
                createVNode(_component_router_link, {
                  to: "/docs/api",
                  class: "text-decoration-none"
                }, {
                  default: withCtx(() => _cache[11] || (_cache[11] = [
                    createTextVNode("API Documentation")
                  ])),
                  _: 1,
                  __: [11]
                })
              ])
            ])
          ]),
          _cache[14] || (_cache[14] = createBaseVNode("div", { class: "col-6 col-md-3" }, [
            createBaseVNode("h5", null, "Resources"),
            createBaseVNode("ul", { class: "list-unstyled" }, [
              createBaseVNode("li", null, [
                createBaseVNode("a", {
                  href: "https://github.com/jafrank88/casestrainer",
                  class: "text-decoration-none",
                  target: "_blank"
                }, "GitHub Repository")
              ]),
              createBaseVNode("li", null, [
                createBaseVNode("a", {
                  href: "mailto:jafrank@uw.edu",
                  class: "footer-link"
                }, "Report an issue")
              ])
            ])
          ], -1))
        ]),
        _cache[15] || (_cache[15] = createBaseVNode("hr", null, null, -1)),
        createBaseVNode("div", _hoisted_19, [
          createBaseVNode("p", _hoisted_20, "© " + toDisplayString($data.currentYear) + " CaseStrainer. All rights reserved.", 1),
          createBaseVNode("small", null, "v" + toDisplayString($data.appVersion), 1)
        ])
      ])
    ]),
    _cache[16] || (_cache[16] = createBaseVNode("div", {
      class: "position-fixed bottom-0 end-0 p-3",
      style: { "z-index": "11" }
    }, [
      createBaseVNode("div", { class: "toast-container" })
    ], -1))
  ]);
}
const App = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["render", _sfc_render$1]]);
const scriptRel = "modulepreload";
const assetsURL = function(dep) {
  return "/" + dep;
};
const seen = {};
const __vitePreload = function preload(baseModule, deps, importerUrl) {
  let promise = Promise.resolve();
  if (deps && deps.length > 0) {
    let allSettled2 = function(promises) {
      return Promise.all(
        promises.map(
          (p) => Promise.resolve(p).then(
            (value) => ({ status: "fulfilled", value }),
            (reason) => ({ status: "rejected", reason })
          )
        )
      );
    };
    document.getElementsByTagName("link");
    const cspNonceMeta = document.querySelector(
      "meta[property=csp-nonce]"
    );
    const cspNonce = (cspNonceMeta == null ? void 0 : cspNonceMeta.nonce) || (cspNonceMeta == null ? void 0 : cspNonceMeta.getAttribute("nonce"));
    promise = allSettled2(
      deps.map((dep) => {
        dep = assetsURL(dep);
        if (dep in seen) return;
        seen[dep] = true;
        const isCss = dep.endsWith(".css");
        const cssSelector = isCss ? '[rel="stylesheet"]' : "";
        if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) {
          return;
        }
        const link = document.createElement("link");
        link.rel = isCss ? "stylesheet" : scriptRel;
        if (!isCss) {
          link.as = "script";
        }
        link.crossOrigin = "";
        link.href = dep;
        if (cspNonce) {
          link.setAttribute("nonce", cspNonce);
        }
        document.head.appendChild(link);
        if (isCss) {
          return new Promise((res, rej) => {
            link.addEventListener("load", res);
            link.addEventListener(
              "error",
              () => rej(new Error(`Unable to preload CSS for ${dep}`))
            );
          });
        }
      })
    );
  }
  function handlePreloadError(err) {
    const e = new Event("vite:preloadError", {
      cancelable: true
    });
    e.payload = err;
    window.dispatchEvent(e);
    if (!e.defaultPrevented) {
      throw err;
    }
  }
  return promise.then((res) => {
    for (const item of res || []) {
      if (item.status !== "rejected") continue;
      handlePreloadError(item.reason);
    }
    return baseModule().catch(handlePreloadError);
  });
};
const BASE_PATH = "/casestrainer/";
const HomeView = () => __vitePreload(() => import("./HomeView-CI4EUgxv.js"), true ? __vite__mapDeps([0,1,2,3,4]) : void 0);
const EnhancedValidator = () => __vitePreload(() => import("./EnhancedValidator-B30_4ffa.js"), true ? __vite__mapDeps([5,1,2,3,6]) : void 0);
const NotFound = () => __vitePreload(() => import("./NotFound-DpimPS8k.js"), true ? __vite__mapDeps([7,1,8]) : void 0);
const BrowserExtension = () => __vitePreload(() => import("./BrowserExtension-ClwUVEdP.js"), true ? __vite__mapDeps([9,1,10]) : void 0);
const WordPlugin = () => __vitePreload(() => import("./WordPlugin-c3pnPb2h.js"), true ? __vite__mapDeps([11,1,12]) : void 0);
const ApiDocs = () => __vitePreload(() => import("./ApiDocs-CvQsyIwM.js"), true ? __vite__mapDeps([13,1,14]) : void 0);
const Docs = () => __vitePreload(() => import("./Docs-CVXY35kc.js"), true ? __vite__mapDeps([15,1,16]) : void 0);
const routes = [
  {
    path: "/",
    name: "Home",
    component: HomeView,
    meta: {
      title: "CaseStrainer - Legal Citation Validator",
      metaTags: [
        {
          name: "description",
          content: "Validate, analyze, and manage legal citations with CaseStrainer. The powerful tool for legal professionals."
        },
        {
          property: "og:title",
          content: "CaseStrainer - Legal Citation Validator"
        },
        {
          property: "og:description",
          content: "Validate, analyze, and manage legal citations with CaseStrainer. The powerful tool for legal professionals."
        },
        {
          property: "og:type",
          content: "website"
        }
      ]
    }
  },
  {
    path: "/docs",
    name: "Docs",
    component: Docs,
    meta: {
      title: "Documentation | CaseStrainer",
      metaTags: [
        { name: "description", content: "Documentation hub for CaseStrainer, including user guides, API docs, and more." }
      ]
    }
  },
  {
    path: "/docs/api",
    name: "ApiDocs",
    component: ApiDocs,
    meta: {
      title: "API Documentation | CaseStrainer",
      metaTags: [
        { name: "description", content: "API documentation for CaseStrainer." }
      ]
    }
  },
  {
    path: "/browser-extension",
    name: "BrowserExtension",
    component: BrowserExtension,
    meta: {
      title: "Browser Extension | CaseStrainer",
      metaTags: [
        { name: "description", content: "Install the CaseStrainer browser extension to validate citations directly on the web." }
      ]
    }
  },
  {
    path: "/word-plugin",
    name: "WordPlugin",
    component: WordPlugin,
    meta: {
      title: "Word Plug-in | CaseStrainer",
      metaTags: [
        { name: "description", content: "Use the CaseStrainer Word plug-in to validate citations directly in your documents." }
      ]
    }
  },
  {
    path: "/enhanced-validator",
    name: "EnhancedValidator",
    component: EnhancedValidator,
    meta: {
      title: "Enhanced Validator | CaseStrainer",
      metaTags: [
        { name: "description", content: "Advanced citation validation and analysis tools." }
      ]
    }
  },
  // Catch-all route for 404s
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: NotFound,
    meta: {
      title: "404 - Page Not Found | CaseStrainer"
    }
  }
];
const router = createRouter({
  history: createWebHistory(BASE_PATH),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    if (to.hash) {
      return {
        el: to.hash,
        behavior: "smooth",
        top: 100
        // Offset for fixed header
      };
    }
    return { top: 0, behavior: "smooth" };
  }
});
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || "CaseStrainer";
  const existingMetaTags = document.querySelectorAll("meta[data-vue-router-controlled]");
  existingMetaTags.forEach((tag) => tag.parentNode.removeChild(tag));
  if (to.meta.metaTags) {
    to.meta.metaTags.forEach((tag) => {
      const metaTag = document.createElement("meta");
      Object.keys(tag).forEach((key) => {
        metaTag.setAttribute(key, tag[key]);
      });
      metaTag.setAttribute("data-vue-router-controlled", "");
      document.head.appendChild(metaTag);
    });
  }
  next();
});
const _sfc_main = {
  name: "AppErrorHandler",
  setup() {
    const { errors, clearErrors } = useLoadingState();
    const hasErrors = computed(() => errors.value.length > 0);
    function getErrorMessage(error) {
      if (!error) return "An unknown error occurred";
      if (error.isAxiosError) {
        const { response } = error;
        if (response) {
          const { status, data } = response;
          if (data && data.message) {
            return `[${status}] ${data.message}`;
          }
          switch (status) {
            case 400:
              return "Bad request. Please check your input and try again.";
            case 401:
              return "You need to be logged in to perform this action.";
            case 403:
              return "You do not have permission to perform this action.";
            case 404:
              return "The requested resource was not found.";
            case 429:
              return "Too many requests. Please wait before trying again.";
            case 500:
              return "An internal server error occurred. Please try again later.";
            default:
              return `An error occurred (${status}). Please try again.`;
          }
        } else if (error.request) {
          return "Unable to connect to the server. Please check your internet connection.";
        }
      }
      return error.message || "An unexpected error occurred";
    }
    function dismissError(index) {
      if (errors.value[index]) {
        const newErrors = [...errors.value];
        newErrors.splice(index, 1);
        clearErrors();
        errors.value = newErrors;
      }
    }
    function clearAllErrors() {
      clearErrors();
    }
    return {
      errors,
      hasErrors,
      getErrorMessage,
      dismissError,
      clearAllErrors
    };
  }
};
const _hoisted_1 = {
  key: 0,
  class: "app-error-handler"
};
const _hoisted_2 = {
  class: "alert alert-danger alert-dismissible fade show",
  role: "alert"
};
const _hoisted_3 = { class: "mb-0" };
const _hoisted_4 = ["onClick"];
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return $setup.hasErrors ? (openBlock(), createElementBlock("div", _hoisted_1, [
    createBaseVNode("div", _hoisted_2, [
      _cache[1] || (_cache[1] = createBaseVNode("h5", { class: "alert-heading" }, "An error occurred", -1)),
      createBaseVNode("ul", _hoisted_3, [
        (openBlock(true), createElementBlock(Fragment, null, renderList($setup.errors, (error, index) => {
          return openBlock(), createElementBlock("li", { key: index }, [
            createTextVNode(toDisplayString($setup.getErrorMessage(error)) + " ", 1),
            createBaseVNode("button", {
              type: "button",
              class: "btn-close",
              "aria-label": "Dismiss",
              onClick: ($event) => $setup.dismissError(index)
            }, null, 8, _hoisted_4)
          ]);
        }), 128))
      ]),
      createBaseVNode("button", {
        type: "button",
        class: "btn-close",
        "aria-label": "Close",
        onClick: _cache[0] || (_cache[0] = (...args) => $setup.clearAllErrors && $setup.clearAllErrors(...args))
      })
    ])
  ])) : createCommentVNode("", true);
}
const AppErrorHandler = /* @__PURE__ */ _export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-bf9bf3a1"]]);
axios.defaults.withCredentials = true;
axios.defaults.baseURL = "/casestrainer/api";
axios.defaults.timeout = 3e4;
const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    return Promise.reject({
      message: (data == null ? void 0 : data.message) || `Request failed with status ${status}`,
      status,
      data,
      isApiError: true
    });
  } else if (error.request) {
    return Promise.reject({
      message: "No response received from server. Please check your connection.",
      isNetworkError: true
    });
  }
  return Promise.reject({
    message: error.message || "An unknown error occurred",
    isUnknownError: true
  });
};
axios.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: Date.now() };
    if (!config._silent) {
      const message = config.loadingMessage || "Loading...";
      window.activeLoader = createLoader(`request_${Date.now()}`, { message });
    }
    return config;
  },
  (error) => {
    if (window.activeLoader) {
      window.activeLoader.remove();
      window.activeLoader = null;
    }
    return Promise.reject(error);
  }
);
axios.interceptors.response.use(
  (response) => {
    var _a;
    if (window.activeLoader) {
      window.activeLoader.complete();
      window.activeLoader = null;
    }
    if ((_a = response.config.metadata) == null ? void 0 : _a.startTime) {
      const duration = Date.now() - response.config.metadata.startTime;
      console.debug(`API Request: ${response.config.url} completed in ${duration}ms`);
    }
    return response;
  },
  async (error) => {
    if (window.activeLoader) {
      window.activeLoader.error();
      window.activeLoader = null;
    }
    return handleApiError(error);
  }
);
const app = createApp(App);
app.component("AppErrorHandler", AppErrorHandler);
app.config.errorHandler = (err, vm, info) => {
  console.error("Vue error:", { err, vm, info });
};
window.addEventListener("unhandledrejection", (event) => {
  console.error("Unhandled promise rejection:", event.reason);
  event.preventDefault();
});
const pinia = createPinia();
app.use(pinia);
app.use(router);
app.config.globalProperties.$http = axios;
app.mount("#app");
export {
  _export_sfc as _,
  axios as a,
  createLoader as c
};
//# sourceMappingURL=index-C6HUIkwi.js.map
