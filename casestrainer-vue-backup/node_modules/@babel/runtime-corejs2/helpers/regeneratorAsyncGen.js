var _Promise = require("core-js/library/fn/promise.js");
var regenerator = require("./regenerator.js");
var regeneratorAsyncIterator = require("./regeneratorAsyncIterator.js");
function _regeneratorAsyncGen(r, e, t, o, n) {
  return new regeneratorAsyncIterator(regenerator().w(r, e, t, o), n || _Promise);
}
module.exports = _regeneratorAsyncGen, module.exports.__esModule = true, module.exports["default"] = module.exports;