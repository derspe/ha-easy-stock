/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
var _a;
const t$3 = globalThis, e$2 = t$3.ShadowRoot && (void 0 === t$3.ShadyCSS || t$3.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, s$2 = Symbol(), o$4 = /* @__PURE__ */ new WeakMap();
let n$3 = class n {
  constructor(t2, e2, o2) {
    if (this._$cssResult$ = true, o2 !== s$2) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t2, this.t = e2;
  }
  get styleSheet() {
    let t2 = this.o;
    const s2 = this.t;
    if (e$2 && void 0 === t2) {
      const e2 = void 0 !== s2 && 1 === s2.length;
      e2 && (t2 = o$4.get(s2)), void 0 === t2 && ((this.o = t2 = new CSSStyleSheet()).replaceSync(this.cssText), e2 && o$4.set(s2, t2));
    }
    return t2;
  }
  toString() {
    return this.cssText;
  }
};
const r$4 = (t2) => new n$3("string" == typeof t2 ? t2 : t2 + "", void 0, s$2), i$3 = (t2, ...e2) => {
  const o2 = 1 === t2.length ? t2[0] : e2.reduce((e3, s2, o3) => e3 + ((t3) => {
    if (true === t3._$cssResult$) return t3.cssText;
    if ("number" == typeof t3) return t3;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t3 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s2) + t2[o3 + 1], t2[0]);
  return new n$3(o2, t2, s$2);
}, S$1 = (s2, o2) => {
  if (e$2) s2.adoptedStyleSheets = o2.map((t2) => t2 instanceof CSSStyleSheet ? t2 : t2.styleSheet);
  else for (const e2 of o2) {
    const o3 = document.createElement("style"), n3 = t$3.litNonce;
    void 0 !== n3 && o3.setAttribute("nonce", n3), o3.textContent = e2.cssText, s2.appendChild(o3);
  }
}, c$2 = e$2 ? (t2) => t2 : (t2) => t2 instanceof CSSStyleSheet ? ((t3) => {
  let e2 = "";
  for (const s2 of t3.cssRules) e2 += s2.cssText;
  return r$4(e2);
})(t2) : t2;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: i$2, defineProperty: e$1, getOwnPropertyDescriptor: h$1, getOwnPropertyNames: r$3, getOwnPropertySymbols: o$3, getPrototypeOf: n$2 } = Object, a$1 = globalThis, c$1 = a$1.trustedTypes, l$1 = c$1 ? c$1.emptyScript : "", p$1 = a$1.reactiveElementPolyfillSupport, d$1 = (t2, s2) => t2, u$1 = { toAttribute(t2, s2) {
  switch (s2) {
    case Boolean:
      t2 = t2 ? l$1 : null;
      break;
    case Object:
    case Array:
      t2 = null == t2 ? t2 : JSON.stringify(t2);
  }
  return t2;
}, fromAttribute(t2, s2) {
  let i2 = t2;
  switch (s2) {
    case Boolean:
      i2 = null !== t2;
      break;
    case Number:
      i2 = null === t2 ? null : Number(t2);
      break;
    case Object:
    case Array:
      try {
        i2 = JSON.parse(t2);
      } catch (t3) {
        i2 = null;
      }
  }
  return i2;
} }, f$1 = (t2, s2) => !i$2(t2, s2), b$1 = { attribute: true, type: String, converter: u$1, reflect: false, useDefault: false, hasChanged: f$1 };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), a$1.litPropertyMetadata ?? (a$1.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let y$1 = class y extends HTMLElement {
  static addInitializer(t2) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t2);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t2, s2 = b$1) {
    if (s2.state && (s2.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t2) && ((s2 = Object.create(s2)).wrapped = true), this.elementProperties.set(t2, s2), !s2.noAccessor) {
      const i2 = Symbol(), h2 = this.getPropertyDescriptor(t2, i2, s2);
      void 0 !== h2 && e$1(this.prototype, t2, h2);
    }
  }
  static getPropertyDescriptor(t2, s2, i2) {
    const { get: e2, set: r2 } = h$1(this.prototype, t2) ?? { get() {
      return this[s2];
    }, set(t3) {
      this[s2] = t3;
    } };
    return { get: e2, set(s3) {
      const h2 = e2 == null ? void 0 : e2.call(this);
      r2 == null ? void 0 : r2.call(this, s3), this.requestUpdate(t2, h2, i2);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t2) {
    return this.elementProperties.get(t2) ?? b$1;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d$1("elementProperties"))) return;
    const t2 = n$2(this);
    t2.finalize(), void 0 !== t2.l && (this.l = [...t2.l]), this.elementProperties = new Map(t2.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d$1("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d$1("properties"))) {
      const t3 = this.properties, s2 = [...r$3(t3), ...o$3(t3)];
      for (const i2 of s2) this.createProperty(i2, t3[i2]);
    }
    const t2 = this[Symbol.metadata];
    if (null !== t2) {
      const s2 = litPropertyMetadata.get(t2);
      if (void 0 !== s2) for (const [t3, i2] of s2) this.elementProperties.set(t3, i2);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t3, s2] of this.elementProperties) {
      const i2 = this._$Eu(t3, s2);
      void 0 !== i2 && this._$Eh.set(i2, t3);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s2) {
    const i2 = [];
    if (Array.isArray(s2)) {
      const e2 = new Set(s2.flat(1 / 0).reverse());
      for (const s3 of e2) i2.unshift(c$2(s3));
    } else void 0 !== s2 && i2.push(c$2(s2));
    return i2;
  }
  static _$Eu(t2, s2) {
    const i2 = s2.attribute;
    return false === i2 ? void 0 : "string" == typeof i2 ? i2 : "string" == typeof t2 ? t2.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var _a2;
    this._$ES = new Promise((t2) => this.enableUpdating = t2), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (_a2 = this.constructor.l) == null ? void 0 : _a2.forEach((t2) => t2(this));
  }
  addController(t2) {
    var _a2;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t2), void 0 !== this.renderRoot && this.isConnected && ((_a2 = t2.hostConnected) == null ? void 0 : _a2.call(t2));
  }
  removeController(t2) {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.delete(t2);
  }
  _$E_() {
    const t2 = /* @__PURE__ */ new Map(), s2 = this.constructor.elementProperties;
    for (const i2 of s2.keys()) this.hasOwnProperty(i2) && (t2.set(i2, this[i2]), delete this[i2]);
    t2.size > 0 && (this._$Ep = t2);
  }
  createRenderRoot() {
    const t2 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S$1(t2, this.constructor.elementStyles), t2;
  }
  connectedCallback() {
    var _a2;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t2) => {
      var _a3;
      return (_a3 = t2.hostConnected) == null ? void 0 : _a3.call(t2);
    });
  }
  enableUpdating(t2) {
  }
  disconnectedCallback() {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t2) => {
      var _a3;
      return (_a3 = t2.hostDisconnected) == null ? void 0 : _a3.call(t2);
    });
  }
  attributeChangedCallback(t2, s2, i2) {
    this._$AK(t2, i2);
  }
  _$ET(t2, s2) {
    var _a2;
    const i2 = this.constructor.elementProperties.get(t2), e2 = this.constructor._$Eu(t2, i2);
    if (void 0 !== e2 && true === i2.reflect) {
      const h2 = (void 0 !== ((_a2 = i2.converter) == null ? void 0 : _a2.toAttribute) ? i2.converter : u$1).toAttribute(s2, i2.type);
      this._$Em = t2, null == h2 ? this.removeAttribute(e2) : this.setAttribute(e2, h2), this._$Em = null;
    }
  }
  _$AK(t2, s2) {
    var _a2, _b;
    const i2 = this.constructor, e2 = i2._$Eh.get(t2);
    if (void 0 !== e2 && this._$Em !== e2) {
      const t3 = i2.getPropertyOptions(e2), h2 = "function" == typeof t3.converter ? { fromAttribute: t3.converter } : void 0 !== ((_a2 = t3.converter) == null ? void 0 : _a2.fromAttribute) ? t3.converter : u$1;
      this._$Em = e2;
      const r2 = h2.fromAttribute(s2, t3.type);
      this[e2] = r2 ?? ((_b = this._$Ej) == null ? void 0 : _b.get(e2)) ?? r2, this._$Em = null;
    }
  }
  requestUpdate(t2, s2, i2, e2 = false, h2) {
    var _a2;
    if (void 0 !== t2) {
      const r2 = this.constructor;
      if (false === e2 && (h2 = this[t2]), i2 ?? (i2 = r2.getPropertyOptions(t2)), !((i2.hasChanged ?? f$1)(h2, s2) || i2.useDefault && i2.reflect && h2 === ((_a2 = this._$Ej) == null ? void 0 : _a2.get(t2)) && !this.hasAttribute(r2._$Eu(t2, i2)))) return;
      this.C(t2, s2, i2);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t2, s2, { useDefault: i2, reflect: e2, wrapped: h2 }, r2) {
    i2 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t2) && (this._$Ej.set(t2, r2 ?? s2 ?? this[t2]), true !== h2 || void 0 !== r2) || (this._$AL.has(t2) || (this.hasUpdated || i2 || (s2 = void 0), this._$AL.set(t2, s2)), true === e2 && this._$Em !== t2 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t2));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t3) {
      Promise.reject(t3);
    }
    const t2 = this.scheduleUpdate();
    return null != t2 && await t2, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var _a2;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t4, s3] of this._$Ep) this[t4] = s3;
        this._$Ep = void 0;
      }
      const t3 = this.constructor.elementProperties;
      if (t3.size > 0) for (const [s3, i2] of t3) {
        const { wrapped: t4 } = i2, e2 = this[s3];
        true !== t4 || this._$AL.has(s3) || void 0 === e2 || this.C(s3, void 0, i2, e2);
      }
    }
    let t2 = false;
    const s2 = this._$AL;
    try {
      t2 = this.shouldUpdate(s2), t2 ? (this.willUpdate(s2), (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t3) => {
        var _a3;
        return (_a3 = t3.hostUpdate) == null ? void 0 : _a3.call(t3);
      }), this.update(s2)) : this._$EM();
    } catch (s3) {
      throw t2 = false, this._$EM(), s3;
    }
    t2 && this._$AE(s2);
  }
  willUpdate(t2) {
  }
  _$AE(t2) {
    var _a2;
    (_a2 = this._$EO) == null ? void 0 : _a2.forEach((t3) => {
      var _a3;
      return (_a3 = t3.hostUpdated) == null ? void 0 : _a3.call(t3);
    }), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t2)), this.updated(t2);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t2) {
    return true;
  }
  update(t2) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t3) => this._$ET(t3, this[t3]))), this._$EM();
  }
  updated(t2) {
  }
  firstUpdated(t2) {
  }
};
y$1.elementStyles = [], y$1.shadowRootOptions = { mode: "open" }, y$1[d$1("elementProperties")] = /* @__PURE__ */ new Map(), y$1[d$1("finalized")] = /* @__PURE__ */ new Map(), p$1 == null ? void 0 : p$1({ ReactiveElement: y$1 }), (a$1.reactiveElementVersions ?? (a$1.reactiveElementVersions = [])).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$2 = globalThis, i$1 = (t2) => t2, s$1 = t$2.trustedTypes, e = s$1 ? s$1.createPolicy("lit-html", { createHTML: (t2) => t2 }) : void 0, h = "$lit$", o$2 = `lit$${Math.random().toFixed(9).slice(2)}$`, n$1 = "?" + o$2, r$2 = `<${n$1}>`, l = document, c = () => l.createComment(""), a = (t2) => null === t2 || "object" != typeof t2 && "function" != typeof t2, u = Array.isArray, d = (t2) => u(t2) || "function" == typeof (t2 == null ? void 0 : t2[Symbol.iterator]), f = "[ 	\n\f\r]", v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, _ = /-->/g, m = />/g, p = RegExp(`>|${f}(?:([^\\s"'>=/]+)(${f}*=${f}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), g = /'/g, $ = /"/g, y2 = /^(?:script|style|textarea|title)$/i, x = (t2) => (i2, ...s2) => ({ _$litType$: t2, strings: i2, values: s2 }), b = x(1), w = x(2), E = Symbol.for("lit-noChange"), A = Symbol.for("lit-nothing"), C = /* @__PURE__ */ new WeakMap(), P = l.createTreeWalker(l, 129);
function V(t2, i2) {
  if (!u(t2) || !t2.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e ? e.createHTML(i2) : i2;
}
const N = (t2, i2) => {
  const s2 = t2.length - 1, e2 = [];
  let n3, l2 = 2 === i2 ? "<svg>" : 3 === i2 ? "<math>" : "", c2 = v;
  for (let i3 = 0; i3 < s2; i3++) {
    const s3 = t2[i3];
    let a2, u2, d2 = -1, f2 = 0;
    for (; f2 < s3.length && (c2.lastIndex = f2, u2 = c2.exec(s3), null !== u2); ) f2 = c2.lastIndex, c2 === v ? "!--" === u2[1] ? c2 = _ : void 0 !== u2[1] ? c2 = m : void 0 !== u2[2] ? (y2.test(u2[2]) && (n3 = RegExp("</" + u2[2], "g")), c2 = p) : void 0 !== u2[3] && (c2 = p) : c2 === p ? ">" === u2[0] ? (c2 = n3 ?? v, d2 = -1) : void 0 === u2[1] ? d2 = -2 : (d2 = c2.lastIndex - u2[2].length, a2 = u2[1], c2 = void 0 === u2[3] ? p : '"' === u2[3] ? $ : g) : c2 === $ || c2 === g ? c2 = p : c2 === _ || c2 === m ? c2 = v : (c2 = p, n3 = void 0);
    const x2 = c2 === p && t2[i3 + 1].startsWith("/>") ? " " : "";
    l2 += c2 === v ? s3 + r$2 : d2 >= 0 ? (e2.push(a2), s3.slice(0, d2) + h + s3.slice(d2) + o$2 + x2) : s3 + o$2 + (-2 === d2 ? i3 : x2);
  }
  return [V(t2, l2 + (t2[s2] || "<?>") + (2 === i2 ? "</svg>" : 3 === i2 ? "</math>" : "")), e2];
};
class S {
  constructor({ strings: t2, _$litType$: i2 }, e2) {
    let r2;
    this.parts = [];
    let l2 = 0, a2 = 0;
    const u2 = t2.length - 1, d2 = this.parts, [f2, v2] = N(t2, i2);
    if (this.el = S.createElement(f2, e2), P.currentNode = this.el.content, 2 === i2 || 3 === i2) {
      const t3 = this.el.content.firstChild;
      t3.replaceWith(...t3.childNodes);
    }
    for (; null !== (r2 = P.nextNode()) && d2.length < u2; ) {
      if (1 === r2.nodeType) {
        if (r2.hasAttributes()) for (const t3 of r2.getAttributeNames()) if (t3.endsWith(h)) {
          const i3 = v2[a2++], s2 = r2.getAttribute(t3).split(o$2), e3 = /([.?@])?(.*)/.exec(i3);
          d2.push({ type: 1, index: l2, name: e3[2], strings: s2, ctor: "." === e3[1] ? I : "?" === e3[1] ? L : "@" === e3[1] ? z : H }), r2.removeAttribute(t3);
        } else t3.startsWith(o$2) && (d2.push({ type: 6, index: l2 }), r2.removeAttribute(t3));
        if (y2.test(r2.tagName)) {
          const t3 = r2.textContent.split(o$2), i3 = t3.length - 1;
          if (i3 > 0) {
            r2.textContent = s$1 ? s$1.emptyScript : "";
            for (let s2 = 0; s2 < i3; s2++) r2.append(t3[s2], c()), P.nextNode(), d2.push({ type: 2, index: ++l2 });
            r2.append(t3[i3], c());
          }
        }
      } else if (8 === r2.nodeType) if (r2.data === n$1) d2.push({ type: 2, index: l2 });
      else {
        let t3 = -1;
        for (; -1 !== (t3 = r2.data.indexOf(o$2, t3 + 1)); ) d2.push({ type: 7, index: l2 }), t3 += o$2.length - 1;
      }
      l2++;
    }
  }
  static createElement(t2, i2) {
    const s2 = l.createElement("template");
    return s2.innerHTML = t2, s2;
  }
}
function M(t2, i2, s2 = t2, e2) {
  var _a2, _b;
  if (i2 === E) return i2;
  let h2 = void 0 !== e2 ? (_a2 = s2._$Co) == null ? void 0 : _a2[e2] : s2._$Cl;
  const o2 = a(i2) ? void 0 : i2._$litDirective$;
  return (h2 == null ? void 0 : h2.constructor) !== o2 && ((_b = h2 == null ? void 0 : h2._$AO) == null ? void 0 : _b.call(h2, false), void 0 === o2 ? h2 = void 0 : (h2 = new o2(t2), h2._$AT(t2, s2, e2)), void 0 !== e2 ? (s2._$Co ?? (s2._$Co = []))[e2] = h2 : s2._$Cl = h2), void 0 !== h2 && (i2 = M(t2, h2._$AS(t2, i2.values), h2, e2)), i2;
}
class R {
  constructor(t2, i2) {
    this._$AV = [], this._$AN = void 0, this._$AD = t2, this._$AM = i2;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t2) {
    const { el: { content: i2 }, parts: s2 } = this._$AD, e2 = ((t2 == null ? void 0 : t2.creationScope) ?? l).importNode(i2, true);
    P.currentNode = e2;
    let h2 = P.nextNode(), o2 = 0, n3 = 0, r2 = s2[0];
    for (; void 0 !== r2; ) {
      if (o2 === r2.index) {
        let i3;
        2 === r2.type ? i3 = new k(h2, h2.nextSibling, this, t2) : 1 === r2.type ? i3 = new r2.ctor(h2, r2.name, r2.strings, this, t2) : 6 === r2.type && (i3 = new Z(h2, this, t2)), this._$AV.push(i3), r2 = s2[++n3];
      }
      o2 !== (r2 == null ? void 0 : r2.index) && (h2 = P.nextNode(), o2++);
    }
    return P.currentNode = l, e2;
  }
  p(t2) {
    let i2 = 0;
    for (const s2 of this._$AV) void 0 !== s2 && (void 0 !== s2.strings ? (s2._$AI(t2, s2, i2), i2 += s2.strings.length - 2) : s2._$AI(t2[i2])), i2++;
  }
}
class k {
  get _$AU() {
    var _a2;
    return ((_a2 = this._$AM) == null ? void 0 : _a2._$AU) ?? this._$Cv;
  }
  constructor(t2, i2, s2, e2) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t2, this._$AB = i2, this._$AM = s2, this.options = e2, this._$Cv = (e2 == null ? void 0 : e2.isConnected) ?? true;
  }
  get parentNode() {
    let t2 = this._$AA.parentNode;
    const i2 = this._$AM;
    return void 0 !== i2 && 11 === (t2 == null ? void 0 : t2.nodeType) && (t2 = i2.parentNode), t2;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t2, i2 = this) {
    t2 = M(this, t2, i2), a(t2) ? t2 === A || null == t2 || "" === t2 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t2 !== this._$AH && t2 !== E && this._(t2) : void 0 !== t2._$litType$ ? this.$(t2) : void 0 !== t2.nodeType ? this.T(t2) : d(t2) ? this.k(t2) : this._(t2);
  }
  O(t2) {
    return this._$AA.parentNode.insertBefore(t2, this._$AB);
  }
  T(t2) {
    this._$AH !== t2 && (this._$AR(), this._$AH = this.O(t2));
  }
  _(t2) {
    this._$AH !== A && a(this._$AH) ? this._$AA.nextSibling.data = t2 : this.T(l.createTextNode(t2)), this._$AH = t2;
  }
  $(t2) {
    var _a2;
    const { values: i2, _$litType$: s2 } = t2, e2 = "number" == typeof s2 ? this._$AC(t2) : (void 0 === s2.el && (s2.el = S.createElement(V(s2.h, s2.h[0]), this.options)), s2);
    if (((_a2 = this._$AH) == null ? void 0 : _a2._$AD) === e2) this._$AH.p(i2);
    else {
      const t3 = new R(e2, this), s3 = t3.u(this.options);
      t3.p(i2), this.T(s3), this._$AH = t3;
    }
  }
  _$AC(t2) {
    let i2 = C.get(t2.strings);
    return void 0 === i2 && C.set(t2.strings, i2 = new S(t2)), i2;
  }
  k(t2) {
    u(this._$AH) || (this._$AH = [], this._$AR());
    const i2 = this._$AH;
    let s2, e2 = 0;
    for (const h2 of t2) e2 === i2.length ? i2.push(s2 = new k(this.O(c()), this.O(c()), this, this.options)) : s2 = i2[e2], s2._$AI(h2), e2++;
    e2 < i2.length && (this._$AR(s2 && s2._$AB.nextSibling, e2), i2.length = e2);
  }
  _$AR(t2 = this._$AA.nextSibling, s2) {
    var _a2;
    for ((_a2 = this._$AP) == null ? void 0 : _a2.call(this, false, true, s2); t2 !== this._$AB; ) {
      const s3 = i$1(t2).nextSibling;
      i$1(t2).remove(), t2 = s3;
    }
  }
  setConnected(t2) {
    var _a2;
    void 0 === this._$AM && (this._$Cv = t2, (_a2 = this._$AP) == null ? void 0 : _a2.call(this, t2));
  }
}
class H {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t2, i2, s2, e2, h2) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t2, this.name = i2, this._$AM = e2, this.options = h2, s2.length > 2 || "" !== s2[0] || "" !== s2[1] ? (this._$AH = Array(s2.length - 1).fill(new String()), this.strings = s2) : this._$AH = A;
  }
  _$AI(t2, i2 = this, s2, e2) {
    const h2 = this.strings;
    let o2 = false;
    if (void 0 === h2) t2 = M(this, t2, i2, 0), o2 = !a(t2) || t2 !== this._$AH && t2 !== E, o2 && (this._$AH = t2);
    else {
      const e3 = t2;
      let n3, r2;
      for (t2 = h2[0], n3 = 0; n3 < h2.length - 1; n3++) r2 = M(this, e3[s2 + n3], i2, n3), r2 === E && (r2 = this._$AH[n3]), o2 || (o2 = !a(r2) || r2 !== this._$AH[n3]), r2 === A ? t2 = A : t2 !== A && (t2 += (r2 ?? "") + h2[n3 + 1]), this._$AH[n3] = r2;
    }
    o2 && !e2 && this.j(t2);
  }
  j(t2) {
    t2 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t2 ?? "");
  }
}
class I extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t2) {
    this.element[this.name] = t2 === A ? void 0 : t2;
  }
}
class L extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t2) {
    this.element.toggleAttribute(this.name, !!t2 && t2 !== A);
  }
}
class z extends H {
  constructor(t2, i2, s2, e2, h2) {
    super(t2, i2, s2, e2, h2), this.type = 5;
  }
  _$AI(t2, i2 = this) {
    if ((t2 = M(this, t2, i2, 0) ?? A) === E) return;
    const s2 = this._$AH, e2 = t2 === A && s2 !== A || t2.capture !== s2.capture || t2.once !== s2.once || t2.passive !== s2.passive, h2 = t2 !== A && (s2 === A || e2);
    e2 && this.element.removeEventListener(this.name, this, s2), h2 && this.element.addEventListener(this.name, this, t2), this._$AH = t2;
  }
  handleEvent(t2) {
    var _a2;
    "function" == typeof this._$AH ? this._$AH.call(((_a2 = this.options) == null ? void 0 : _a2.host) ?? this.element, t2) : this._$AH.handleEvent(t2);
  }
}
class Z {
  constructor(t2, i2, s2) {
    this.element = t2, this.type = 6, this._$AN = void 0, this._$AM = i2, this.options = s2;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t2) {
    M(this, t2);
  }
}
const B = t$2.litHtmlPolyfillSupport;
B == null ? void 0 : B(S, k), (t$2.litHtmlVersions ?? (t$2.litHtmlVersions = [])).push("3.3.2");
const D = (t2, i2, s2) => {
  const e2 = (s2 == null ? void 0 : s2.renderBefore) ?? i2;
  let h2 = e2._$litPart$;
  if (void 0 === h2) {
    const t3 = (s2 == null ? void 0 : s2.renderBefore) ?? null;
    e2._$litPart$ = h2 = new k(i2.insertBefore(c(), t3), t3, void 0, s2 ?? {});
  }
  return h2._$AI(t2), h2;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const s = globalThis;
class i extends y$1 {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a2;
    const t2 = super.createRenderRoot();
    return (_a2 = this.renderOptions).renderBefore ?? (_a2.renderBefore = t2.firstChild), t2;
  }
  update(t2) {
    const r2 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t2), this._$Do = D(r2, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var _a2;
    super.connectedCallback(), (_a2 = this._$Do) == null ? void 0 : _a2.setConnected(true);
  }
  disconnectedCallback() {
    var _a2;
    super.disconnectedCallback(), (_a2 = this._$Do) == null ? void 0 : _a2.setConnected(false);
  }
  render() {
    return E;
  }
}
i._$litElement$ = true, i["finalized"] = true, (_a = s.litElementHydrateSupport) == null ? void 0 : _a.call(s, { LitElement: i });
const o$1 = s.litElementPolyfillSupport;
o$1 == null ? void 0 : o$1({ LitElement: i });
(s.litElementVersions ?? (s.litElementVersions = [])).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1 = (t2) => (e2, o2) => {
  void 0 !== o2 ? o2.addInitializer(() => {
    customElements.define(t2, e2);
  }) : customElements.define(t2, e2);
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const o = { attribute: true, type: String, converter: u$1, reflect: false, hasChanged: f$1 }, r$1 = (t2 = o, e2, r2) => {
  const { kind: n3, metadata: i2 } = r2;
  let s2 = globalThis.litPropertyMetadata.get(i2);
  if (void 0 === s2 && globalThis.litPropertyMetadata.set(i2, s2 = /* @__PURE__ */ new Map()), "setter" === n3 && ((t2 = Object.create(t2)).wrapped = true), s2.set(r2.name, t2), "accessor" === n3) {
    const { name: o2 } = r2;
    return { set(r3) {
      const n4 = e2.get.call(this);
      e2.set.call(this, r3), this.requestUpdate(o2, n4, t2, true, r3);
    }, init(e3) {
      return void 0 !== e3 && this.C(o2, void 0, t2, e3), e3;
    } };
  }
  if ("setter" === n3) {
    const { name: o2 } = r2;
    return function(r3) {
      const n4 = this[o2];
      e2.call(this, r3), this.requestUpdate(o2, n4, t2, true, r3);
    };
  }
  throw Error("Unsupported decorator location: " + n3);
};
function n2(t2) {
  return (e2, o2) => "object" == typeof o2 ? r$1(t2, e2, o2) : ((t3, e3, o3) => {
    const r2 = e3.hasOwnProperty(o3);
    return e3.constructor.createProperty(o3, t3), r2 ? Object.getOwnPropertyDescriptor(e3, o3) : void 0;
  })(t2, e2, o2);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function r(r2) {
  return n2({ ...r2, state: true, attribute: false });
}
const translations = {
  en: {
    editor: {
      title_label: "Title (optional)",
      display_currency: "Display currency",
      default_range: "Default time range",
      tile_size: "Tile size",
      selected: "Selected",
      drag_hint: "drag to reorder",
      add: "Add",
      no_sensors: "No Easy Stock sensors found.",
      setup_hint: "Set up under Settings → Integrations → Easy Stock."
    },
    card: { not_found: "Not found" }
  },
  de: {
    editor: {
      title_label: "Titel (optional)",
      display_currency: "Anzeigewährung",
      default_range: "Standard Zeitraum",
      tile_size: "Kachelgröße",
      selected: "Ausgewählt",
      drag_hint: "ziehen zum Sortieren",
      add: "Hinzufügen",
      no_sensors: "Keine Easy Stock Sensoren gefunden.",
      setup_hint: "Integration einrichten unter Einstellungen → Integrationen → Easy Stock."
    },
    card: { not_found: "Nicht gefunden" }
  },
  fr: {
    editor: {
      title_label: "Titre (optionnel)",
      display_currency: "Devise d'affichage",
      default_range: "Période par défaut",
      tile_size: "Taille des tuiles",
      selected: "Sélectionnés",
      drag_hint: "glisser pour réorganiser",
      add: "Ajouter",
      no_sensors: "Aucun capteur Easy Stock trouvé.",
      setup_hint: "Configurer sous Paramètres → Intégrations → Easy Stock."
    },
    card: { not_found: "Introuvable" }
  },
  nl: {
    editor: {
      title_label: "Titel (optioneel)",
      display_currency: "Weergavevaluta",
      default_range: "Standaard tijdsbereik",
      tile_size: "Tegelgrootte",
      selected: "Geselecteerd",
      drag_hint: "slepen om te sorteren",
      add: "Toevoegen",
      no_sensors: "Geen Easy Stock-sensoren gevonden.",
      setup_hint: "Instellen via Instellingen → Integraties → Easy Stock."
    },
    card: { not_found: "Niet gevonden" }
  },
  es: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moneda de visualización",
      default_range: "Rango de tiempo predeterminado",
      tile_size: "Tamaño de ficha",
      selected: "Seleccionados",
      drag_hint: "arrastrar para ordenar",
      add: "Añadir",
      no_sensors: "No se encontraron sensores Easy Stock.",
      setup_hint: "Configurar en Ajustes → Integraciones → Easy Stock."
    },
    card: { not_found: "No encontrado" }
  },
  it: {
    editor: {
      title_label: "Titolo (opzionale)",
      display_currency: "Valuta di visualizzazione",
      default_range: "Intervallo predefinito",
      tile_size: "Dimensione tessera",
      selected: "Selezionati",
      drag_hint: "trascina per riordinare",
      add: "Aggiungi",
      no_sensors: "Nessun sensore Easy Stock trovato.",
      setup_hint: "Configurare in Impostazioni → Integrazioni → Easy Stock."
    },
    card: { not_found: "Non trovato" }
  },
  pt: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moeda de exibição",
      default_range: "Intervalo padrão",
      tile_size: "Tamanho do bloco",
      selected: "Selecionados",
      drag_hint: "arrastar para reordenar",
      add: "Adicionar",
      no_sensors: "Nenhum sensor Easy Stock encontrado.",
      setup_hint: "Configurar em Definições → Integrações → Easy Stock."
    },
    card: { not_found: "Não encontrado" }
  },
  pl: {
    editor: {
      title_label: "Tytuł (opcjonalny)",
      display_currency: "Waluta wyświetlania",
      default_range: "Domyślny zakres czasu",
      tile_size: "Rozmiar kafelka",
      selected: "Wybrane",
      drag_hint: "przeciągnij, aby zmienić kolejność",
      add: "Dodaj",
      no_sensors: "Nie znaleziono czujników Easy Stock.",
      setup_hint: "Skonfiguruj w Ustawienia → Integracje → Easy Stock."
    },
    card: { not_found: "Nie znaleziono" }
  },
  sv: {
    editor: {
      title_label: "Titel (valfritt)",
      display_currency: "Visningsvaluta",
      default_range: "Standardtidsintervall",
      tile_size: "Kakelstorlek",
      selected: "Valda",
      drag_hint: "dra för att sortera",
      add: "Lägg till",
      no_sensors: "Inga Easy Stock-sensorer hittades.",
      setup_hint: "Konfigurera under Inställningar → Integrationer → Easy Stock."
    },
    card: { not_found: "Hittades inte" }
  },
  da: {
    editor: {
      title_label: "Titel (valgfrit)",
      display_currency: "Visningsvaluta",
      default_range: "Standard tidsinterval",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "træk for at sortere",
      add: "Tilføj",
      no_sensors: "Ingen Easy Stock-sensorer fundet.",
      setup_hint: "Opsæt under Indstillinger → Integrationer → Easy Stock."
    },
    card: { not_found: "Ikke fundet" }
  },
  nb: {
    editor: {
      title_label: "Tittel (valgfritt)",
      display_currency: "Visningsvaluta",
      default_range: "Standard tidsintervall",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "dra for å sortere",
      add: "Legg til",
      no_sensors: "Ingen Easy Stock-sensorer funnet.",
      setup_hint: "Konfigurer under Innstillinger → Integrasjoner → Easy Stock."
    },
    card: { not_found: "Ikke funnet" }
  },
  fi: {
    editor: {
      title_label: "Otsikko (valinnainen)",
      display_currency: "Näyttövaluutta",
      default_range: "Oletusjaksovali",
      tile_size: "Ruudun koko",
      selected: "Valitut",
      drag_hint: "vedä järjestääksesi",
      add: "Lisää",
      no_sensors: "Easy Stock -antureita ei löydy.",
      setup_hint: "Määritä kohdassa Asetukset → Integraatiot → Easy Stock."
    },
    card: { not_found: "Ei löydy" }
  },
  cs: {
    editor: {
      title_label: "Název (volitelný)",
      display_currency: "Zobrazovaná měna",
      default_range: "Výchozí časový rozsah",
      tile_size: "Velikost dlaždice",
      selected: "Vybrané",
      drag_hint: "přetáhněte pro seřazení",
      add: "Přidat",
      no_sensors: "Nebyly nalezeny žádné senzory Easy Stock.",
      setup_hint: "Nastavte v Nastavení → Integrace → Easy Stock."
    },
    card: { not_found: "Nenalezeno" }
  },
  hu: {
    editor: {
      title_label: "Cím (opcionális)",
      display_currency: "Megjelenítési pénznem",
      default_range: "Alapértelmezett időtartomány",
      tile_size: "Csempe mérete",
      selected: "Kiválasztottak",
      drag_hint: "húzza a rendezéshez",
      add: "Hozzáadás",
      no_sensors: "Nem találhatók Easy Stock érzékelők.",
      setup_hint: "Állítsa be a Beállítások → Integrációk → Easy Stock menüpontban."
    },
    card: { not_found: "Nem található" }
  },
  ru: {
    editor: {
      title_label: "Заголовок (необязательно)",
      display_currency: "Валюта отображения",
      default_range: "Временной диапазон по умолчанию",
      tile_size: "Размер плитки",
      selected: "Выбранные",
      drag_hint: "перетащите для сортировки",
      add: "Добавить",
      no_sensors: "Датчики Easy Stock не найдены.",
      setup_hint: "Настройте в Настройки → Интеграции → Easy Stock."
    },
    card: { not_found: "Не найдено" }
  },
  zh: {
    editor: {
      title_label: "标题（可选）",
      display_currency: "显示货币",
      default_range: "默认时间范围",
      tile_size: "磁贴大小",
      selected: "已选择",
      drag_hint: "拖动以排序",
      add: "添加",
      no_sensors: "未找到 Easy Stock 传感器。",
      setup_hint: "在设置 → 集成 → Easy Stock 中进行配置。"
    },
    card: { not_found: "未找到" }
  },
  ja: {
    editor: {
      title_label: "タイトル（省略可）",
      display_currency: "表示通貨",
      default_range: "デフォルト期間",
      tile_size: "タイルサイズ",
      selected: "選択済み",
      drag_hint: "ドラッグして並び替え",
      add: "追加",
      no_sensors: "Easy Stock センサーが見つかりません。",
      setup_hint: "設定 → インテグレーション → Easy Stock で設定してください。"
    },
    card: { not_found: "見つかりません" }
  },
  ko: {
    editor: {
      title_label: "제목 (선택사항)",
      display_currency: "표시 통화",
      default_range: "기본 기간",
      tile_size: "타일 크기",
      selected: "선택됨",
      drag_hint: "드래그하여 정렬",
      add: "추가",
      no_sensors: "Easy Stock 센서를 찾을 수 없습니다.",
      setup_hint: "설정 → 통합 → Easy Stock에서 설정하세요."
    },
    card: { not_found: "찾을 수 없음" }
  },
  tr: {
    editor: {
      title_label: "Başlık (isteğe bağlı)",
      display_currency: "Görüntüleme para birimi",
      default_range: "Varsayılan zaman aralığı",
      tile_size: "Kutucuk boyutu",
      selected: "Seçilenler",
      drag_hint: "sıralamak için sürükle",
      add: "Ekle",
      no_sensors: "Easy Stock sensörü bulunamadı.",
      setup_hint: "Ayarlar → Entegrasyonlar → Easy Stock altında yapılandırın."
    },
    card: { not_found: "Bulunamadı" }
  },
  ar: {
    editor: {
      title_label: "العنوان (اختياري)",
      display_currency: "عملة العرض",
      default_range: "النطاق الزمني الافتراضي",
      tile_size: "حجم البلاطة",
      selected: "المحددة",
      drag_hint: "اسحب للترتيب",
      add: "إضافة",
      no_sensors: "لم يتم العثور على أجهزة استشعار Easy Stock.",
      setup_hint: "الإعداد في الإعدادات ← التكاملات ← Easy Stock."
    },
    card: { not_found: "غير موجود" }
  }
};
function t(lang) {
  const base = lang.split("-")[0].toLowerCase();
  return translations[base] ?? translations["en"];
}
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i2 = decorators.length - 1, decorator; i2 >= 0; i2--)
    if (decorator = decorators[i2])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp(target, key, result);
  return result;
};
const CURRENCIES = [
  { code: "EUR", label: "€ EUR" },
  { code: "USD", label: "$ USD" },
  { code: "GBP", label: "£ GBP" },
  { code: "CHF", label: "Fr CHF" },
  { code: "AUD", label: "A$ AUD" },
  { code: "CAD", label: "CA$ CAD" },
  { code: "JPY", label: "¥ JPY" },
  { code: "SEK", label: "kr SEK" },
  { code: "NOK", label: "kr NOK" },
  { code: "DKK", label: "kr DKK" },
  { code: "CNY", label: "¥ CNY" },
  { code: "HKD", label: "HK$ HKD" }
];
let _rateCache = null;
let _rateFetchInFlight = false;
const RATE_TTL = 15 * 60 * 1e3;
async function fetchRates() {
  if (_rateCache && Date.now() - _rateCache.fetchedAt < RATE_TTL) {
    return _rateCache.rates;
  }
  if (_rateFetchInFlight) {
    return (_rateCache == null ? void 0 : _rateCache.rates) ?? {};
  }
  _rateFetchInFlight = true;
  try {
    const resp = await fetch("https://api.frankfurter.app/latest?base=EUR");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const rates = { EUR: 1, ...data.rates };
    _rateCache = { rates, fetchedAt: Date.now() };
    return rates;
  } catch (err) {
    console.warn("[easy-stock-card] Currency rate fetch failed, using last known rates:", err);
    return (_rateCache == null ? void 0 : _rateCache.rates) ?? {};
  } finally {
    _rateFetchInFlight = false;
  }
}
function convertPrice(price, from, to, rates) {
  if (from === to) return price;
  const rateFrom = rates[from] ?? 1;
  const rateTo = rates[to] ?? 1;
  const inEur = from === "EUR" ? price : price / rateFrom;
  return to === "EUR" ? inEur : inEur * rateTo;
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "easy-stock-card",
  name: "Easy Stock Card",
  description: "Displays stock prices from the Easy Stock integration with sparkline charts.",
  preview: true
});
const TILE_MIN_WIDTHS = {
  small: "170px",
  medium: "220px",
  large: "280px"
};
const RANGES = [
  { value: "1T", label: "1D" },
  { value: "1W", label: "1W" },
  { value: "1M", label: "1M" },
  { value: "YTD", label: "YTD" },
  { value: "1J", label: "1Y" }
];
let EasyStockCardEditor = class extends i {
  constructor() {
    super(...arguments);
    this._dragIndex = null;
  }
  setConfig(config) {
    this._config = config;
  }
  _detectStockSensors() {
    if (!this.hass) return [];
    return Object.values(this.hass.states).filter(
      (e2) => typeof e2.attributes["symbol"] === "string"
    ).sort(
      (a2, b2) => a2.attributes["symbol"].localeCompare(
        b2.attributes["symbol"]
      )
    );
  }
  _sensorName(sensor) {
    return sensor.attributes.long_name || sensor.attributes.symbol;
  }
  // ---- Drag & Drop --------------------------------------------------------
  _onDragStart(e2, index) {
    this._dragIndex = index;
    e2.dataTransfer.effectAllowed = "move";
  }
  _onDragOver(e2, index) {
    var _a2;
    e2.preventDefault();
    if (this._dragIndex === null || this._dragIndex === index) return;
    const entities = [...((_a2 = this._config) == null ? void 0 : _a2.entities) ?? []];
    const [moved] = entities.splice(this._dragIndex, 1);
    entities.splice(index, 0, moved);
    this._dragIndex = index;
    this._set("entities", entities);
  }
  _onDragEnd() {
    this._dragIndex = null;
  }
  // ---- Render -------------------------------------------------------------
  render() {
    var _a2, _b, _c;
    if (!this._config) return A;
    const { title, default_range, entities = [] } = this._config;
    const all = this._detectStockSensors();
    const available = all.filter((s22) => !entities.includes(s22.entity_id));
    const s2 = t(((_b = (_a2 = this.hass) == null ? void 0 : _a2.locale) == null ? void 0 : _b.language) ?? "en").editor;
    return b`
      <div class="editor">
        <ha-textfield
          label=${s2.title_label}
          .value=${title ?? ""}
          @change=${(e2) => {
      const v2 = e2.target.value.trim();
      this._set("title", v2 || void 0);
    }}
        ></ha-textfield>

        <div class="field-label">${s2.display_currency}</div>
        <select
          class="currency-select"
          .value=${((_c = this._config) == null ? void 0 : _c.display_currency) ?? "EUR"}
          @change=${(e2) => this._set("display_currency", e2.target.value)}
        >
          ${CURRENCIES.map(({ code, label }) => {
      var _a3;
      return b`
            <option value=${code} ?selected=${(((_a3 = this._config) == null ? void 0 : _a3.display_currency) ?? "EUR") === code}>${label}</option>
          `;
    })}
        </select>

        <div class="field-label">${s2.default_range}</div>
        <div class="range-picker">
          ${RANGES.map(
      ({ value, label }) => b`
              <button
                class="range-opt ${(default_range ?? "1T") === value ? "active" : ""}"
                @click=${() => this._set("default_range", value)}
              >${label}</button>
            `
    )}
        </div>

        <div class="field-label">${s2.tile_size}</div>
        <div class="range-picker">
          ${["small", "medium", "large"].map((size) => {
      var _a3;
      return b`
            <button
              class="range-opt ${(((_a3 = this._config) == null ? void 0 : _a3.tile_size) ?? "small") === size ? "active" : ""}"
              @click=${() => this._set("tile_size", size)}
            >${size === "small" ? "S" : size === "medium" ? "M" : "L"}</button>
          `;
    })}
        </div>

        ${entities.length > 0 ? b`
          <div class="section-label">${s2.selected} <span class="hint-inline">— ${s2.drag_hint}</span></div>
          <div class="selected-list">
            ${entities.map((entityId, index) => {
      const sensor = all.find((s22) => s22.entity_id === entityId);
      const name = sensor ? this._sensorName(sensor) : entityId;
      const symbol = (sensor == null ? void 0 : sensor.attributes.symbol) ?? "";
      return b`
                <div
                  class="selected-row ${this._dragIndex === index ? "dragging" : ""}"
                  draggable="true"
                  @dragstart=${(e2) => this._onDragStart(e2, index)}
                  @dragover=${(e2) => this._onDragOver(e2, index)}
                  @dragend=${() => this._onDragEnd()}
                >
                  <span class="drag-handle">⠿</span>
                  <span class="sensor-name">${name}</span>
                  <span class="sensor-meta">${symbol}</span>
                  <button class="remove-btn" @click=${() => this._removeEntity(entityId)}>✕</button>
                </div>
              `;
    })}
          </div>
        ` : A}

        ${all.length === 0 ? b`<p class="hint">${s2.no_sensors}<br />${s2.setup_hint}</p>` : available.length > 0 ? b`
              <div class="section-label">${s2.add}</div>
              ${available.map((sensor) => b`
                <label class="sensor-row">
                  <input type="checkbox" .checked=${false} @change=${() => this._addEntity(sensor.entity_id)} />
                  <span class="sensor-name">${this._sensorName(sensor)}</span>
                  <span class="sensor-meta">${sensor.attributes.symbol} · ${sensor.entity_id}</span>
                </label>
              `)}
            ` : A}
      </div>
    `;
  }
  _set(key, value) {
    const config = { ...this._config, [key]: value };
    if (value === void 0) delete config[key];
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config } }));
  }
  _addEntity(entityId) {
    var _a2;
    const current = ((_a2 = this._config) == null ? void 0 : _a2.entities) ?? [];
    this._set("entities", [...current, entityId]);
  }
  _removeEntity(entityId) {
    var _a2;
    const current = ((_a2 = this._config) == null ? void 0 : _a2.entities) ?? [];
    this._set("entities", current.filter((id) => id !== entityId));
  }
};
EasyStockCardEditor.styles = i$3`
    .editor {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 8px 0;
    }
    ha-textfield {
      display: block;
      width: 100%;
    }
    .field-label {
      font-size: 0.8rem;
      color: var(--secondary-text-color);
      margin-top: 4px;
    }
    .currency-select {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      font-size: 0.88rem;
      cursor: pointer;
    }
    .range-picker {
      display: flex;
      gap: 6px;
    }
    .range-opt {
      flex: 1;
      padding: 6px 0;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: none;
      cursor: pointer;
      font-size: 0.82rem;
      color: var(--secondary-text-color);
    }
    .range-opt.active {
      background: var(--primary-color);
      border-color: var(--primary-color);
      color: var(--text-primary-color, #fff);
      font-weight: 600;
    }
    .section-label {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--secondary-text-color);
      margin-top: 8px;
      padding-bottom: 2px;
      border-bottom: 1px solid var(--divider-color);
    }
    .hint-inline {
      font-weight: 400;
      font-size: 0.78rem;
    }
    .selected-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .selected-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 6px;
      background: var(--secondary-background-color);
      cursor: grab;
      user-select: none;
    }
    .selected-row.dragging {
      opacity: 0.4;
    }
    .drag-handle {
      font-size: 1.1rem;
      color: var(--secondary-text-color);
      cursor: grab;
      flex-shrink: 0;
    }
    .remove-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: var(--secondary-text-color);
      font-size: 0.8rem;
      padding: 2px 4px;
      border-radius: 4px;
      flex-shrink: 0;
      line-height: 1;
    }
    .remove-btn:hover {
      color: var(--error-color, #f44336);
    }
    .sensor-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      cursor: pointer;
      border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
    }
    .sensor-row input[type="checkbox"] {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      cursor: pointer;
      accent-color: var(--primary-color);
    }
    .sensor-name {
      font-size: 0.88rem;
      color: var(--primary-text-color);
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .sensor-meta {
      font-size: 0.72rem;
      color: var(--secondary-text-color);
      font-family: monospace;
      flex-shrink: 0;
    }
    .hint {
      font-size: 0.82rem;
      color: var(--secondary-text-color);
      line-height: 1.5;
      margin: 4px 0;
    }
  `;
__decorateClass([
  n2({ attribute: false })
], EasyStockCardEditor.prototype, "hass", 2);
__decorateClass([
  r()
], EasyStockCardEditor.prototype, "_config", 2);
__decorateClass([
  r()
], EasyStockCardEditor.prototype, "_dragIndex", 2);
EasyStockCardEditor = __decorateClass([
  t$1("easy-stock-card-editor")
], EasyStockCardEditor);
const HA_HISTORY_TTL = 5 * 60 * 1e3;
const HA_HISTORY_RANGES = ["1T", "1W"];
let EasyStockCard = class extends i {
  constructor() {
    super(...arguments);
    this._timeRange = "1T";
    this._rates = {};
    this._haCache = /* @__PURE__ */ new Map();
    this._fetching = /* @__PURE__ */ new Set();
    this._yahooHistoryCache = /* @__PURE__ */ new Map();
    this._fetchingYahoo = /* @__PURE__ */ new Set();
  }
  set hass(hass) {
    this._hass = hass;
    if (!_rateCache || Date.now() - _rateCache.fetchedAt >= RATE_TTL) {
      void fetchRates().then((rates) => {
        if (Object.keys(rates).length > 0) this._rates = rates;
      });
    }
  }
  get hass() {
    return this._hass;
  }
  setConfig(config) {
    if (!Array.isArray(config.entities) || config.entities.length === 0) {
      throw new Error("easy-stock-card: 'entities' muss ein nicht-leeres Array sein.");
    }
    this._config = config;
    this._timeRange = config.default_range ?? "1T";
    void fetchRates().then((rates) => {
      if (Object.keys(rates).length > 0) this._rates = rates;
    });
  }
  getCardSize() {
    var _a2;
    const rows = Math.ceil((((_a2 = this._config) == null ? void 0 : _a2.entities.length) ?? 1) / 3);
    return rows * 3 + 1;
  }
  static getStubConfig() {
    return {
      type: "custom:easy-stock-card",
      title: "Mein Portfolio",
      entities: [],
      default_range: "1T"
    };
  }
  static getConfigElement() {
    return document.createElement("easy-stock-card-editor");
  }
  // -------------------------------------------------------------------------
  // HA history cache
  // -------------------------------------------------------------------------
  _cacheKey(entityId, range) {
    return `${entityId}:${range}`;
  }
  _cachedHaHistory(entityId, range) {
    const entry = this._haCache.get(this._cacheKey(entityId, range));
    if (!entry || Date.now() - entry.fetchedAt > HA_HISTORY_TTL) return null;
    return entry.data;
  }
  async _fetchHaHistory(entityId, range) {
    const key = this._cacheKey(entityId, range);
    if (this._fetching.has(key)) return;
    const existing = this._haCache.get(key);
    if (existing && Date.now() - existing.fetchedAt < HA_HISTORY_TTL) return;
    this._fetching.add(key);
    try {
      const start = /* @__PURE__ */ new Date();
      if (range === "1T") start.setDate(start.getDate() - 1);
      else start.setDate(start.getDate() - 7);
      const result = await this._hass.callApi(
        "GET",
        `history/period/${start.toISOString()}?filter_entity_id=${entityId}&minimal_response=true&no_attributes=true&significant_changes_only=false`
      );
      const states = (result == null ? void 0 : result[0]) ?? [];
      const data = states.map((s2) => [s2.last_changed, parseFloat(s2.state)]).filter(([, p2]) => !isNaN(p2));
      this._haCache.set(key, { data, fetchedAt: Date.now() });
      this.requestUpdate();
    } catch (err) {
      console.warn(`[easy-stock-card] HA history fetch failed for ${entityId}:`, err);
    } finally {
      this._fetching.delete(key);
    }
  }
  // -------------------------------------------------------------------------
  // Yahoo history cache (fetched from /api/easy_stock/history)
  // -------------------------------------------------------------------------
  _cachedYahooHistory(symbol) {
    const entry = this._yahooHistoryCache.get(symbol);
    if (!entry || Date.now() - entry.ts > 60 * 60 * 1e3) return null;
    return entry.data;
  }
  async _fetchYahooHistory(symbol) {
    if (this._fetchingYahoo.has(symbol)) return;
    if (this._cachedYahooHistory(symbol) !== null) return;
    this._fetchingYahoo.add(symbol);
    try {
      const result = await this._hass.callApi(
        "GET",
        `easy_stock/history?symbol=${encodeURIComponent(symbol)}`
      );
      this._yahooHistoryCache.set(symbol, { data: result.history, ts: Date.now() });
      this.requestUpdate();
    } catch (err) {
      console.warn(`[easy-stock-card] Yahoo history fetch failed for ${symbol}:`, err);
    } finally {
      this._fetchingYahoo.delete(symbol);
    }
  }
  // -------------------------------------------------------------------------
  // Chart data helpers
  // -------------------------------------------------------------------------
  /** Today as "YYYY-MM-DD" in local time */
  _todayStr() {
    const d2 = /* @__PURE__ */ new Date();
    return `${d2.getFullYear()}-${String(d2.getMonth() + 1).padStart(2, "0")}-${String(d2.getDate()).padStart(2, "0")}`;
  }
  /**
   * Build chart data for the selected range.
   * 1T / 1W: HA recorder history (5-min resolution), fallback to sensor attributes.
   * 1M / YTD / 1J: Yahoo daily history from sensor attribute.
   */
  _buildChartData(entityId, yahooHistory, range, livePrice, previousClose, priceIsLive) {
    const today = this._todayStr();
    if (HA_HISTORY_RANGES.includes(range)) {
      const haData = this._cachedHaHistory(entityId, range);
      if (range === "1T") {
        if (!priceIsLive) {
          return [["prev", livePrice], [today, livePrice]];
        }
        const lastYahooEntry = yahooHistory.length > 0 ? yahooHistory[yahooHistory.length - 1] : null;
        const prev = lastYahooEntry && lastYahooEntry[0] < today ? lastYahooEntry[1] : previousClose > 0 ? previousClose : livePrice;
        const todayStart = /* @__PURE__ */ new Date();
        todayStart.setHours(0, 0, 0, 0);
        const midnightISO = todayStart.toISOString();
        if (haData && haData.length >= 1) {
          const todayData = haData.filter(([t2]) => new Date(t2) >= todayStart);
          if (todayData.length >= 1) {
            return [[midnightISO, prev], [todayData[0][0], prev], ...todayData];
          }
        }
        return [[midnightISO, prev], [(/* @__PURE__ */ new Date()).toISOString(), livePrice]];
      }
      if (haData && haData.length >= 2) return haData;
      const base2 = yahooHistory.slice(-4);
      return base2.length > 0 ? [...base2, [today, livePrice]] : [["prev", previousClose], [today, livePrice]];
    }
    let base;
    if (range === "1M") {
      const cutoff = /* @__PURE__ */ new Date();
      cutoff.setDate(cutoff.getDate() - 30);
      const cutoffStr = cutoff.toISOString().slice(0, 10);
      const filtered = yahooHistory.filter(([d2]) => d2 >= cutoffStr);
      base = filtered.length >= 2 ? filtered : yahooHistory.slice(-2);
    } else if (range === "YTD") {
      const jan1 = `${(/* @__PURE__ */ new Date()).getFullYear()}-01-01`;
      const filtered = yahooHistory.filter(([d2]) => d2 >= jan1);
      const prevYearEntries = yahooHistory.filter(([d2]) => d2 < jan1);
      const prevYearClose = prevYearEntries[prevYearEntries.length - 1];
      if (prevYearClose) {
        base = [prevYearClose, ...filtered];
      } else {
        base = filtered.length >= 2 ? filtered : yahooHistory.slice(-2);
      }
    } else {
      base = yahooHistory;
    }
    if (base.length === 0) return [[today, livePrice]];
    const last = base[base.length - 1];
    if (last[0] === today) return [...base.slice(0, -1), [today, livePrice]];
    return [...base, [today, livePrice]];
  }
  _calcPeriodChange(chartData, range, dailyChangePct) {
    if (chartData.length < 2) return range === "1T" ? dailyChangePct : 0;
    const oldest = chartData[0][1];
    const newest = chartData[chartData.length - 1][1];
    if (range === "1T") {
      if (oldest === newest) return 0;
      return oldest !== 0 ? (newest - oldest) / oldest * 100 : 0;
    }
    return oldest !== 0 ? (newest - oldest) / oldest * 100 : 0;
  }
  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  render() {
    if (!this._config || !this._hass) return A;
    const tileMinWidth = TILE_MIN_WIDTHS[this._config.tile_size ?? "small"] ?? "170px";
    return b`
      <ha-card>
        <div class="card-top">
          ${this._config.title ? b`<h1 class="card-header">${this._config.title}</h1>` : A}
          <div class="range-selector">
            ${RANGES.map(
      ({ value, label }) => b`
                <button
                  class="range-btn ${this._timeRange === value ? "active" : ""}"
                  @click=${() => {
        this._timeRange = value;
      }}
                >
                  ${label}
                </button>
              `
    )}
          </div>
        </div>
        <div class="card-content">
          <div class="asset-grid" style="grid-template-columns: repeat(auto-fill, minmax(${tileMinWidth}, 1fr))">
            ${this._config.entities.map(
      (entityId) => this._renderEntity(entityId)
    )}
          </div>
        </div>
      </ha-card>
    `;
  }
  _renderEntity(entityId) {
    var _a2, _b, _c, _d;
    const raw = (_a2 = this._hass) == null ? void 0 : _a2.states[entityId];
    if (!raw) {
      return b`
        <div class="asset-tile">
          <div class="asset-header">
            <span class="asset-name">${entityId}</span>
          </div>
          <div class="status error">${t(((_c = (_b = this._hass) == null ? void 0 : _b.locale) == null ? void 0 : _c.language) ?? "en").card.not_found}</div>
        </div>
      `;
    }
    const entity = raw;
    const attr = entity.attributes;
    const displayName = raw.attributes["friendly_name"] || attr.long_name || attr.symbol;
    const nativeCurrency = attr.currency;
    const targetCurrency = ((_d = this._config) == null ? void 0 : _d.display_currency) ?? "EUR";
    const hasRates = Object.keys(this._rates).length > 0;
    const price = parseFloat(entity.state);
    const displayPrice = hasRates ? convertPrice(price, nativeCurrency, targetCurrency, this._rates) : price;
    const displayCurrency = hasRates ? targetCurrency : nativeCurrency;
    void this._fetchYahooHistory(attr.symbol);
    if (HA_HISTORY_RANGES.includes(this._timeRange)) {
      void this._fetchHaHistory(entityId, this._timeRange);
    }
    const yahooHistory = this._cachedYahooHistory(attr.symbol) ?? [];
    const priceIsLive = attr.price_is_live ?? false;
    const chartData = this._buildChartData(entityId, yahooHistory, this._timeRange, price, attr.previous_close ?? 0, priceIsLive);
    const periodChange = this._calcPeriodChange(chartData, this._timeRange, attr.change_pct ?? 0);
    const isPositive = periodChange >= 0;
    const trendColor = isPositive ? "var(--success-color, #4caf50)" : "var(--error-color, #f44336)";
    const arrow = isPositive ? "▲" : "▼";
    const refRaw = chartData.length > 0 ? chartData[0][1] : null;
    const displayRefPrice = refRaw !== null ? hasRates ? convertPrice(refRaw, nativeCurrency, targetCurrency, this._rates) : refRaw : null;
    const showRef = displayRefPrice !== null && Math.abs(displayRefPrice - displayPrice) > 1e-4;
    return b`
      <div class="asset-tile" @click=${() => this._openMoreInfo(entityId)}>
        <div class="asset-header">
          <span class="asset-name" title="${displayName}">${displayName}</span>
          <span class="asset-ticker">${attr.symbol}</span>
        </div>
        <div class="asset-price">
          <div class="price-stack">
            <span class="price">${this._formatPrice(displayPrice, displayCurrency)}</span>
            ${showRef ? b`<span class="ref-price">${this._formatPrice(displayRefPrice, displayCurrency)}</span>` : A}
          </div>
          <span class="change" style="color:${trendColor}">
            <span class="arrow">${arrow}</span>${Math.abs(periodChange).toFixed(2)}%
          </span>
        </div>
        <div class="sparkline-wrap">
          ${this._renderSparkline(chartData, trendColor, this._timeRange)}
        </div>
      </div>
    `;
  }
  _openMoreInfo(entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId },
      bubbles: true,
      composed: true
    }));
  }
  _renderSparkline(history, color, range) {
    if (history.length < 2) return A;
    const prices = history.map(([, p2]) => p2);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const priceRange = max - min || 1;
    const W = 200;
    const H2 = 48;
    const pad = 2;
    const isIntraday = range === "1T" && history[0][0].includes("T");
    let points;
    if (isIntraday) {
      const todayStart = /* @__PURE__ */ new Date();
      todayStart.setHours(0, 0, 0, 0);
      const dayMs = 24 * 60 * 60 * 1e3;
      points = history.map(([t2, p2]) => {
        const xFrac = Math.max(0, Math.min(1, (new Date(t2).getTime() - todayStart.getTime()) / dayMs));
        const x2 = pad + xFrac * (W - pad * 2);
        const y3 = pad + (1 - (p2 - min) / priceRange) * (H2 - pad * 2);
        return `${x2.toFixed(1)},${y3.toFixed(1)}`;
      }).join(" ");
    } else {
      points = prices.map((p2, i2) => {
        const x2 = pad + i2 / (prices.length - 1) * (W - pad * 2);
        const y3 = pad + (1 - (p2 - min) / priceRange) * (H2 - pad * 2);
        return `${x2.toFixed(1)},${y3.toFixed(1)}`;
      }).join(" ");
    }
    return w`
      <svg viewBox="0 0 ${W} ${H2}" preserveAspectRatio="none" class="sparkline-svg" aria-hidden="true">
        <polyline
          points="${points}"
          fill="none"
          stroke="${color}"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    `;
  }
  _formatPrice(price, currency) {
    if (isNaN(price)) return "–";
    try {
      return new Intl.NumberFormat(void 0, {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: price < 10 ? 4 : 2
      }).format(price);
    } catch {
      return `${price.toFixed(2)} ${currency}`;
    }
  }
};
EasyStockCard.styles = i$3`
    ha-card { height: 100%; }

    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px 0;
      gap: 8px;
    }
    .card-header {
      font-size: 1.1rem;
      font-weight: 500;
      margin: 0;
      color: var(--primary-text-color);
      flex: 1 1 auto;
    }
    .range-selector {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }
    .range-btn {
      background: none;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 0.72rem;
      font-weight: 500;
      cursor: pointer;
      color: var(--secondary-text-color);
      line-height: 1.6;
    }
    .range-btn.active {
      background: var(--primary-color);
      border-color: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .card-content { padding: 10px 16px 16px; }

    .asset-grid {
      display: grid;
      gap: 10px;
    }
    .asset-tile {
      background: var(--secondary-background-color);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
      cursor: pointer;
      transition: filter 0.15s ease;
    }
    .asset-tile:hover {
      filter: brightness(1.08);
    }
    .asset-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 4px;
      min-width: 0;
    }
    .asset-name {
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--primary-text-color);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .asset-ticker {
      font-size: 0.7rem;
      color: var(--secondary-text-color);
      font-family: monospace;
      flex-shrink: 0;
    }
    .asset-price {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 4px;
    }
    .price-stack {
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .price {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--primary-text-color);
      white-space: nowrap;
    }
    .ref-price {
      font-size: 0.7rem;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }
    .change {
      font-size: 0.78rem;
      font-weight: 600;
      white-space: nowrap;
      display: flex;
      align-items: baseline;
      gap: 2px;
    }
    .arrow { font-size: 0.7rem; }
    .sparkline-wrap { margin-top: 5px; }
    .sparkline-svg {
      width: 100%;
      height: 40px;
      display: block;
    }
    .status {
      font-size: 0.78rem;
      padding: 6px 0;
    }
    .error { color: var(--error-color, #f44336); }
  `;
__decorateClass([
  r()
], EasyStockCard.prototype, "_config", 2);
__decorateClass([
  r()
], EasyStockCard.prototype, "_timeRange", 2);
__decorateClass([
  r()
], EasyStockCard.prototype, "_rates", 2);
EasyStockCard = __decorateClass([
  t$1("easy-stock-card")
], EasyStockCard);
export {
  EasyStockCard,
  EasyStockCardEditor
};
//# sourceMappingURL=easy-stock-card.js.map
