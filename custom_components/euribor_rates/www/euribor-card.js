/*! euribor-card 2.3.0 | MIT License */
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i5 = decorators.length - 1, decorator; i5 >= 0; i5--)
    if (decorator = decorators[i5])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp(target, key, result);
  return result;
};

// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = /* @__PURE__ */ Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t3, e5, o6) {
    if (this._$cssResult$ = true, o6 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e5;
  }
  get styleSheet() {
    let t3 = this.o;
    const s4 = this.t;
    if (e && void 0 === t3) {
      const e5 = void 0 !== s4 && 1 === s4.length;
      e5 && (t3 = o.get(s4)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e5 && o.set(s4, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new n("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e5) => {
  const o6 = 1 === t3.length ? t3[0] : e5.reduce((e6, s4, o7) => e6 + ((t4) => {
    if (true === t4._$cssResult$) return t4.cssText;
    if ("number" == typeof t4) return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t3[o7 + 1], t3[0]);
  return new n(o6, t3, s);
};
var S = (s4, o6) => {
  if (e) s4.adoptedStyleSheets = o6.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet);
  else for (const e5 of o6) {
    const o7 = document.createElement("style"), n5 = t.litNonce;
    void 0 !== n5 && o7.setAttribute("nonce", n5), o7.textContent = e5.cssText, s4.appendChild(o7);
  }
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e5 = "";
  for (const s4 of t4.cssRules) e5 += s4.cssText;
  return r(e5);
})(t3) : t3;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t3, s4) => t3;
var u = { toAttribute(t3, s4) {
  switch (s4) {
    case Boolean:
      t3 = t3 ? l : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, s4) {
  let i5 = t3;
  switch (s4) {
    case Boolean:
      i5 = null !== t3;
      break;
    case Number:
      i5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t3);
      } catch (t4) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t3, s4) => !i2(t3, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ?? (Symbol.metadata = /* @__PURE__ */ Symbol("metadata")), a.litPropertyMetadata ?? (a.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
var y = class extends HTMLElement {
  static addInitializer(t3) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t3);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t3, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t3) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t3, s4), !s4.noAccessor) {
      const i5 = /* @__PURE__ */ Symbol(), h3 = this.getPropertyDescriptor(t3, i5, s4);
      void 0 !== h3 && e2(this.prototype, t3, h3);
    }
  }
  static getPropertyDescriptor(t3, s4, i5) {
    const { get: e5, set: r6 } = h(this.prototype, t3) ?? { get() {
      return this[s4];
    }, set(t4) {
      this[s4] = t4;
    } };
    return { get: e5, set(s5) {
      const h3 = e5?.call(this);
      r6?.call(this, s5), this.requestUpdate(t3, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t3 = n2(this);
    t3.finalize(), void 0 !== t3.l && (this.l = [...t3.l]), this.elementProperties = new Map(t3.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t4 = this.properties, s4 = [...r2(t4), ...o2(t4)];
      for (const i5 of s4) this.createProperty(i5, t4[i5]);
    }
    const t3 = this[Symbol.metadata];
    if (null !== t3) {
      const s4 = litPropertyMetadata.get(t3);
      if (void 0 !== s4) for (const [t4, i5] of s4) this.elementProperties.set(t4, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t4, s4] of this.elementProperties) {
      const i5 = this._$Eu(t4, s4);
      void 0 !== i5 && this._$Eh.set(i5, t4);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e5 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e5) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t3, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t3) => this.enableUpdating = t3), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t3) => t3(this));
  }
  addController(t3) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t3), void 0 !== this.renderRoot && this.isConnected && t3.hostConnected?.();
  }
  removeController(t3) {
    this._$EO?.delete(t3);
  }
  _$E_() {
    const t3 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t3.set(i5, this[i5]), delete this[i5]);
    t3.size > 0 && (this._$Ep = t3);
  }
  createRenderRoot() {
    const t3 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t3, this.constructor.elementStyles), t3;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), this._$EO?.forEach((t3) => t3.hostConnected?.());
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t3) => t3.hostDisconnected?.());
  }
  attributeChangedCallback(t3, s4, i5) {
    this._$AK(t3, i5);
  }
  _$ET(t3, s4) {
    const i5 = this.constructor.elementProperties.get(t3), e5 = this.constructor._$Eu(t3, i5);
    if (void 0 !== e5 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t3, null == h3 ? this.removeAttribute(e5) : this.setAttribute(e5, h3), this._$Em = null;
    }
  }
  _$AK(t3, s4) {
    const i5 = this.constructor, e5 = i5._$Eh.get(t3);
    if (void 0 !== e5 && this._$Em !== e5) {
      const t4 = i5.getPropertyOptions(e5), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== t4.converter?.fromAttribute ? t4.converter : u;
      this._$Em = e5;
      const r6 = h3.fromAttribute(s4, t4.type);
      this[e5] = r6 ?? this._$Ej?.get(e5) ?? r6, this._$Em = null;
    }
  }
  requestUpdate(t3, s4, i5, e5 = false, h3) {
    if (void 0 !== t3) {
      const r6 = this.constructor;
      if (false === e5 && (h3 = this[t3]), i5 ?? (i5 = r6.getPropertyOptions(t3)), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t3) && !this.hasAttribute(r6._$Eu(t3, i5)))) return;
      this.C(t3, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t3, s4, { useDefault: i5, reflect: e5, wrapped: h3 }, r6) {
    i5 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t3) && (this._$Ej.set(t3, r6 ?? s4 ?? this[t3]), true !== h3 || void 0 !== r6) || (this._$AL.has(t3) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t3, s4)), true === e5 && this._$Em !== t3 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t3));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t5, s5] of this._$Ep) this[t5] = s5;
        this._$Ep = void 0;
      }
      const t4 = this.constructor.elementProperties;
      if (t4.size > 0) for (const [s5, i5] of t4) {
        const { wrapped: t5 } = i5, e5 = this[s5];
        true !== t5 || this._$AL.has(s5) || void 0 === e5 || this.C(s5, void 0, i5, e5);
      }
    }
    let t3 = false;
    const s4 = this._$AL;
    try {
      t3 = this.shouldUpdate(s4), t3 ? (this.willUpdate(s4), this._$EO?.forEach((t4) => t4.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t3 = false, this._$EM(), s5;
    }
    t3 && this._$AE(s4);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    this._$EO?.forEach((t4) => t4.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
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
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t4) => this._$ET(t4, this[t4]))), this._$EM();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ?? (a.reactiveElementVersions = [])).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t3) => t3;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u2 = Array.isArray;
var d2 = (t3) => u2(t3) || "function" == typeof t3?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t3) => (i5, ...s4) => ({ _$litType$: t3, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = /* @__PURE__ */ Symbol.for("lit-noChange");
var A = /* @__PURE__ */ Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t3, i5) {
  if (!u2(t3) || !t3.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t3, i5) => {
  const s4 = t3.length - 1, e5 = [];
  let n5, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t3[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n5 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n5 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n5 = void 0);
    const x2 = c4 === p2 && t3[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e5.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t3, l3 + (t3[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e5];
};
var S2 = class _S {
  constructor({ strings: t3, _$litType$: i5 }, e5) {
    let r6;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t3.length - 1, d3 = this.parts, [f3, v2] = N(t3, i5);
    if (this.el = _S.createElement(f3, e5), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t4 = this.el.content.firstChild;
      t4.replaceWith(...t4.childNodes);
    }
    for (; null !== (r6 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r6.nodeType) {
        if (r6.hasAttributes()) for (const t4 of r6.getAttributeNames()) if (t4.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r6.getAttribute(t4).split(o3), e6 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e6[2], strings: s4, ctor: "." === e6[1] ? I : "?" === e6[1] ? L : "@" === e6[1] ? z : H }), r6.removeAttribute(t4);
        } else t4.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r6.removeAttribute(t4));
        if (y2.test(r6.tagName)) {
          const t4 = r6.textContent.split(o3), i6 = t4.length - 1;
          if (i6 > 0) {
            r6.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r6.append(t4[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r6.append(t4[i6], c3());
          }
        }
      } else if (8 === r6.nodeType) if (r6.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t4 = -1;
        for (; -1 !== (t4 = r6.data.indexOf(o3, t4 + 1)); ) d3.push({ type: 7, index: l3 }), t4 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t3, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t3, s4;
  }
};
function M(t3, i5, s4 = t3, e5) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e5 ? s4._$Co?.[e5] : s4._$Cl;
  const o6 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o6 && (h3?._$AO?.(false), void 0 === o6 ? h3 = void 0 : (h3 = new o6(t3), h3._$AT(t3, s4, e5)), void 0 !== e5 ? (s4._$Co ?? (s4._$Co = []))[e5] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t3, h3._$AS(t3, i5.values), h3, e5)), i5;
}
var R = class {
  constructor(t3, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t3, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t3) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e5 = (t3?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e5;
    let h3 = P.nextNode(), o6 = 0, n5 = 0, r6 = s4[0];
    for (; void 0 !== r6; ) {
      if (o6 === r6.index) {
        let i6;
        2 === r6.type ? i6 = new k(h3, h3.nextSibling, this, t3) : 1 === r6.type ? i6 = new r6.ctor(h3, r6.name, r6.strings, this, t3) : 6 === r6.type && (i6 = new Z(h3, this, t3)), this._$AV.push(i6), r6 = s4[++n5];
      }
      o6 !== r6?.index && (h3 = P.nextNode(), o6++);
    }
    return P.currentNode = l2, e5;
  }
  p(t3) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t3, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t3[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t3, i5, s4, e5) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t3, this._$AB = i5, this._$AM = s4, this.options = e5, this._$Cv = e5?.isConnected ?? true;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t3?.nodeType && (t3 = i5.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i5 = this) {
    t3 = M(this, t3, i5), a2(t3) ? t3 === A || null == t3 || "" === t3 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t3 !== this._$AH && t3 !== E && this._(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : d2(t3) ? this.k(t3) : this._(t3);
  }
  O(t3) {
    return this._$AA.parentNode.insertBefore(t3, this._$AB);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  _(t3) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(l2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    const { values: i5, _$litType$: s4 } = t3, e5 = "number" == typeof s4 ? this._$AC(t3) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e5) this._$AH.p(i5);
    else {
      const t4 = new R(e5, this), s5 = t4.u(this.options);
      t4.p(i5), this.T(s5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i5 = C.get(t3.strings);
    return void 0 === i5 && C.set(t3.strings, i5 = new S2(t3)), i5;
  }
  k(t3) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e5 = 0;
    for (const h3 of t3) e5 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e5], s4._$AI(h3), e5++;
    e5 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e5), i5.length = e5);
  }
  _$AR(t3 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t3 !== this._$AB; ) {
      const s5 = i3(t3).nextSibling;
      i3(t3).remove(), t3 = s5;
    }
  }
  setConnected(t3) {
    void 0 === this._$AM && (this._$Cv = t3, this._$AP?.(t3));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t3, i5, s4, e5, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t3, this.name = i5, this._$AM = e5, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t3, i5 = this, s4, e5) {
    const h3 = this.strings;
    let o6 = false;
    if (void 0 === h3) t3 = M(this, t3, i5, 0), o6 = !a2(t3) || t3 !== this._$AH && t3 !== E, o6 && (this._$AH = t3);
    else {
      const e6 = t3;
      let n5, r6;
      for (t3 = h3[0], n5 = 0; n5 < h3.length - 1; n5++) r6 = M(this, e6[s4 + n5], i5, n5), r6 === E && (r6 = this._$AH[n5]), o6 || (o6 = !a2(r6) || r6 !== this._$AH[n5]), r6 === A ? t3 = A : t3 !== A && (t3 += (r6 ?? "") + h3[n5 + 1]), this._$AH[n5] = r6;
    }
    o6 && !e5 && this.j(t3);
  }
  j(t3) {
    t3 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t3 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === A ? void 0 : t3;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    this.element.toggleAttribute(this.name, !!t3 && t3 !== A);
  }
};
var z = class extends H {
  constructor(t3, i5, s4, e5, h3) {
    super(t3, i5, s4, e5, h3), this.type = 5;
  }
  _$AI(t3, i5 = this) {
    if ((t3 = M(this, t3, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e5 = t3 === A && s4 !== A || t3.capture !== s4.capture || t3.once !== s4.once || t3.passive !== s4.passive, h3 = t3 !== A && (s4 === A || e5);
    e5 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var Z = class {
  constructor(t3, i5, s4) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    M(this, t3);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ?? (t2.litHtmlVersions = [])).push("3.3.3");
var D = (t3, i5, s4) => {
  const e5 = s4?.renderBefore ?? i5;
  let h3 = e5._$litPart$;
  if (void 0 === h3) {
    const t4 = s4?.renderBefore ?? null;
    e5._$litPart$ = h3 = new k(i5.insertBefore(c3(), t4), t4, void 0, s4 ?? {});
  }
  return h3._$AI(t3), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a;
    const t3 = super.createRenderRoot();
    return (_a = this.renderOptions).renderBefore ?? (_a.renderBefore = t3.firstChild), t3;
  }
  update(t3) {
    const r6 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = D(r6, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return E;
  }
};
i4._$litElement$ = true, i4["finalized"] = true, s3.litElementHydrateSupport?.({ LitElement: i4 });
var o4 = s3.litElementPolyfillSupport;
o4?.({ LitElement: i4 });
(s3.litElementVersions ?? (s3.litElementVersions = [])).push("4.2.2");

// node_modules/@lit/reactive-element/decorators/property.js
var o5 = { attribute: true, type: String, converter: u, reflect: false, hasChanged: f };
var r4 = (t3 = o5, e5, r6) => {
  const { kind: n5, metadata: i5 } = r6;
  let s4 = globalThis.litPropertyMetadata.get(i5);
  if (void 0 === s4 && globalThis.litPropertyMetadata.set(i5, s4 = /* @__PURE__ */ new Map()), "setter" === n5 && ((t3 = Object.create(t3)).wrapped = true), s4.set(r6.name, t3), "accessor" === n5) {
    const { name: o6 } = r6;
    return { set(r7) {
      const n6 = e5.get.call(this);
      e5.set.call(this, r7), this.requestUpdate(o6, n6, t3, true, r7);
    }, init(e6) {
      return void 0 !== e6 && this.C(o6, void 0, t3, e6), e6;
    } };
  }
  if ("setter" === n5) {
    const { name: o6 } = r6;
    return function(r7) {
      const n6 = this[o6];
      e5.call(this, r7), this.requestUpdate(o6, n6, t3, true, r7);
    };
  }
  throw Error("Unsupported decorator location: " + n5);
};
function n4(t3) {
  return (e5, o6) => "object" == typeof o6 ? r4(t3, e5, o6) : ((t4, e6, o7) => {
    const r6 = e6.hasOwnProperty(o7);
    return e6.constructor.createProperty(o7, t4), r6 ? Object.getOwnPropertyDescriptor(e6, o7) : void 0;
  })(t3, e5, o6);
}

// node_modules/@lit/reactive-element/decorators/state.js
function r5(r6) {
  return n4({ ...r6, state: true, attribute: false });
}

// src/series.ts
function points(rows, timeZone) {
  const format = new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" });
  const result = [];
  for (const row of rows ?? []) {
    if (typeof row.mean !== "number") {
      continue;
    }
    result.push({ day: format.format(new Date(row.start)), value: row.mean });
  }
  return result.sort((a3, b3) => a3.day.localeCompare(b3.day));
}
function moment(day) {
  return Date.parse(`${day}T12:00:00Z`);
}
function dayOf(time) {
  return new Date(time).toISOString().slice(0, 10);
}
var DAY = 864e5;
function addMonths(day, months) {
  const [year, month, date] = day.split("-").map(Number);
  const total = year * 12 + (month - 1) + months;
  const newYear = Math.floor(total / 12);
  const newMonth = total - newYear * 12;
  const last = new Date(Date.UTC(newYear, newMonth + 1, 0)).getUTCDate();
  return `${String(newYear).padStart(4, "0")}-${String(newMonth + 1).padStart(2, "0")}-${String(Math.min(date, last)).padStart(2, "0")}`;
}
function valueOn(series, day) {
  let found;
  for (const point of series) {
    if (point.day > day) {
      break;
    }
    found = point;
  }
  return found;
}
var RANGES = [
  { key: "1m", months: 1 },
  { key: "1y", months: 12 },
  { key: "2y", months: 24 },
  { key: "3y", months: 36 },
  { key: "5y", months: 60 },
  { key: "all", months: 0 }
];
var SLACK_DAYS = 7;
function availableRanges(series, today) {
  const first = series[0]?.day;
  if (!first) {
    return [];
  }
  return RANGES.filter(({ key, months }) => key === "all" || dayOf(moment(addMonths(today, -months)) + SLACK_DAYS * DAY) >= first).map(
    ({ key }) => key
  );
}
function rangeStart(range, series, today) {
  const months = RANGES.find(({ key }) => key === range)?.months ?? 0;
  return months ? addMonths(today, -months) : series[0]?.day ?? today;
}
function changes(series) {
  const newest = series.at(-1);
  if (!newest) {
    return {};
  }
  const change = (months) => {
    const then = valueOn(series, addMonths(newest.day, -months));
    return then ? newest.value - then.value : void 0;
  };
  return { month: change(1), year: change(12) };
}
function lockedOn(series, reset, lockDays) {
  const lastDay = new Date(moment(reset) - (lockDays ? DAY : 0));
  const lastWorkingDay = dayOf(lastDay.getTime() - Math.max(0, (lastDay.getUTCDay() + 6) % 7 - 4) * DAY);
  if ((series.at(-1)?.day ?? "") < lastWorkingDay) {
    return void 0;
  }
  if (!lockDays) {
    return valueOn(series, reset);
  }
  let count = 0;
  for (let index = series.length - 1; index >= 0; index--) {
    if (series[index].day < reset && ++count === lockDays) {
      return series[index];
    }
  }
  return void 0;
}
function lockPeriods(series, enteredReset, months, lockDays, start, today) {
  const monthOf = (day) => Number(day.slice(0, 4)) * 12 + Number(day.slice(5, 7));
  let count = Math.floor((monthOf(start) - monthOf(enteredReset)) / months) - 2;
  const first = series[0]?.day;
  const periods = [];
  for (let reset = addMonths(enteredReset, count * months); reset <= today; reset = addMonths(enteredReset, ++count * months)) {
    const until = addMonths(enteredReset, (count + 1) * months);
    const locked = first && reset >= first ? lockedOn(series, reset, lockDays) : void 0;
    if (locked && until > start) {
      periods.push({ reset, until, locked });
    }
  }
  return periods;
}
function steps(series) {
  const result = [];
  for (let index = 1; index < series.length; index++) {
    if (series[index].value !== series[index - 1].value) {
      result.push({ day: series[index].day, from: series[index - 1].value, to: series[index].value });
    }
  }
  return result;
}

// src/chart.ts
var PAD = { left: 36, right: 8, top: 16, bottom: 16 };
var FUTURE = 0.25;
function scale(input) {
  const start = moment(input.start);
  const now = moment(input.today);
  const end = input.projection ? now + Math.round((now - start) * FUTURE / DAY) * DAY : now;
  const values = input.rates.map((point) => point.value);
  if (input.ecbMode === "steps") {
    values.push(...input.ecb.map((point) => point.value));
  }
  if (input.loanMarks !== "none") {
    for (const loan of input.loans) {
      values.push(...loan.periods.map((period) => period.locked.value));
    }
  }
  let low = Math.min(...values);
  let high = Math.max(...values);
  if (!Number.isFinite(low)) {
    low = 0;
    high = 1;
  }
  const range = Math.max(high - low, 0.01);
  const step = range > 1 ? 0.25 : range > 0.4 ? 0.1 : range > 0.1 ? 0.05 : 0.01;
  low = Math.floor((low - range * 0.04) / step) * step;
  high = Math.ceil((high + range * 0.04) / step) * step;
  const innerWidth = Math.max(1, input.width - PAD.left - PAD.right);
  const innerHeight = Math.max(1, input.height - PAD.top - PAD.bottom);
  const newest = input.rates.at(-1)?.day ?? input.today;
  return {
    start,
    end,
    low,
    high,
    step,
    x: (time) => PAD.left + (time - start) / (end - start) * innerWidth,
    y: (value) => PAD.top + (1 - (value - low) / (high - low)) * innerHeight,
    dayAt: (x2) => {
      const day = dayOf(start + (x2 - PAD.left) / innerWidth * (end - start));
      return day > newest ? newest : day;
    }
  };
}
function nearest(points2, day) {
  const time = moment(day);
  let best;
  for (const point of points2) {
    if (!best || Math.abs(moment(point.day) - time) < Math.abs(moment(best.day) - time)) {
      best = point;
    }
  }
  return best;
}
function chart(input) {
  const s4 = scale(input);
  const { width, height } = input;
  const small = height < 110;
  const bottom = height - PAD.bottom;
  const ticks = [];
  for (let value = s4.low; value <= s4.high + 1e-9; value += s4.step) {
    ticks.push(value);
  }
  const every = Math.ceil(ticks.length / (small ? 3 : 5));
  const digits = s4.step < 0.05 ? 2 : s4.step < 0.1 ? 2 : s4.step < 0.25 ? 1 : 2;
  const visible = input.rates.filter((point) => moment(point.day) >= s4.start);
  const line = visible.map((point, index) => `${index ? "L" : "M"}${s4.x(moment(point.day)).toFixed(1)},${s4.y(point.value).toFixed(1)}`).join(" ");
  const now = moment(input.today);
  const newest = input.rates.at(-1);
  return w`
        <svg viewBox="0 0 ${width} ${height}" width=${width} height=${height} role="img">
            ${ticks.map(
    (value, index) => index % every ? null : w`<line class="grid" x1=${PAD.left} x2=${width - PAD.right} y1=${s4.y(value)} y2=${s4.y(value)}></line>
                          <text class="axis" x=${PAD.left - 6} y=${s4.y(value) + 3} text-anchor="end">${input.number(value, digits)}</text>`
  )}
            ${monthTicks(s4, width).map((day) => w`<text class="axis" x=${s4.x(moment(day))} y=${height - 3} text-anchor="middle">${input.month(day)}</text>`)}
            ${input.projection ? w`<rect class="future" x=${s4.x(now)} y=${PAD.top} width=${Math.max(0, s4.x(s4.end) - s4.x(now))} height=${bottom - PAD.top}></rect>
                      <text class="axis small" x=${s4.x(s4.end)} y=${PAD.top - 5} text-anchor="end">${input.projectionLabel}</text>` : null}
            ${ecb(input, s4, bottom)}
            ${input.loanMarks === "lines" ? lockLines(input, s4) : null}
            <path class="rate" d=${line}></path>
            ${input.projection && newest ? w`<line class="rate projection" x1=${s4.x(moment(newest.day))} x2=${s4.x(s4.end)} y1=${s4.y(newest.value)} y2=${s4.y(newest.value)}></line>` : null}
            ${input.loanMarks === "markers" ? lockMarkers(input, s4) : null}
            ${hover(input, s4, bottom)}
        </svg>
    `;
}
function monthTicks(s4, width) {
  const span = (s4.end - s4.start) / DAY;
  const result = [];
  if (span <= 45) {
    for (let time = s4.end; time >= s4.start; time -= 7 * DAY) {
      result.unshift(dayOf(time));
    }
    return result;
  }
  const wanted = Math.max(2, Math.floor(width / 70));
  const months = [1, 2, 3, 6, 12, 24, 60].find((step) => span / 30.4 / step <= wanted) ?? 120;
  const first = new Date(s4.start);
  const cursor = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 1, 12));
  for (; cursor.getTime() < s4.end; cursor.setUTCMonth(cursor.getUTCMonth() + 1)) {
    const index = cursor.getUTCFullYear() * 12 + cursor.getUTCMonth();
    if (index % months === 0) {
      result.push(dayOf(cursor.getTime()));
    }
  }
  return result;
}
function ecb(input, s4, bottom) {
  if (input.ecbMode === "none" || !input.ecb.length) {
    return null;
  }
  const changes2 = steps(input.ecb).filter((change) => moment(change.day) >= s4.start);
  if (input.ecbMode === "markers") {
    return w`${changes2.map((change) => {
      const x2 = s4.x(moment(change.day));
      return w`<line class="ecb-mark" x1=${x2} x2=${x2} y1=${PAD.top} y2=${bottom}></line>
                <path class="ecb" d="M${x2 - 4},${bottom} L${x2 + 4},${bottom} L${x2},${bottom - 6} Z"></path>
                <text class="ecb-label" x=${x2 + 5} y=${bottom - 2}>${signed(input, change.to - change.from)}</text>`;
    })}`;
  }
  const before = input.ecb.filter((point) => moment(point.day) <= s4.start).at(-1) ?? input.ecb[0];
  let path = `M${s4.x(s4.start)},${s4.y(before.value)}`;
  let level = before.value;
  for (const change of changes2) {
    const x2 = s4.x(moment(change.day));
    path += ` L${x2},${s4.y(level)} L${x2},${s4.y(change.to)}`;
    level = change.to;
  }
  path += ` L${s4.x(s4.end)},${s4.y(level)}`;
  return w`<path class="ecb-step" d=${path}></path>
        ${changes2.map(
    (change) => w`<text class="ecb-label" x=${s4.x(moment(change.day)) + 3} y=${s4.y(change.to) - 4}>${signed(input, change.to - change.from)}</text>`
  )}`;
}
function lockLines(input, s4) {
  return w`${input.loans.map(
    (loan) => loan.periods.map((period) => {
      const from = Math.max(moment(period.reset), s4.start);
      const until = Math.min(moment(period.until), s4.end);
      return until > from ? w`<line class="lock" style="stroke: ${loan.color}" x1=${s4.x(from)} x2=${s4.x(until)} y1=${s4.y(period.locked.value)} y2=${s4.y(period.locked.value)}></line>` : null;
    })
  )}`;
}
function lockMarkers(input, s4) {
  return w`${input.loans.map(
    (loan) => loan.periods.filter((period) => moment(period.locked.day) >= s4.start).map((period) => {
      const x2 = s4.x(moment(period.locked.day));
      const y3 = s4.y(period.locked.value);
      return w`<circle class="marker" style="stroke: ${loan.color}" cx=${x2} cy=${y3} r="4"></circle>`;
    })
  )}`;
}
function hover(input, s4, bottom) {
  const point = input.hover ? nearest(input.rates, input.hover) : void 0;
  if (!point || moment(point.day) < s4.start) {
    return null;
  }
  const x2 = s4.x(moment(point.day));
  return w`<line class="hover" x1=${x2} x2=${x2} y1=${PAD.top} y2=${bottom}></line>
        <circle class="hover-dot" cx=${x2} cy=${s4.y(point.value)} r="3.5"></circle>`;
}
function signed(input, value) {
  return `${value > 0 ? "+" : value < 0 ? "\u2212" : "\xB1"}${input.number(Math.abs(value), 2)}`;
}

// src/const.ts
var CARD_VERSION = "2.3.0";
var DEFAULT_ROWS = 7;
var ROW_HEIGHT = 56;
var ROW_GAP = 8;
function minimumRows(loans2) {
  return loans2 ? 6 + Math.max(0, Math.ceil((loans2 - 3) / 2)) : 4;
}
var LOAN_COLORS = [
  "var(--euribor-card-loan-1, var(--orange-color, #ff9800))",
  "var(--euribor-card-loan-2, var(--teal-color, #009688))",
  "var(--euribor-card-loan-3, var(--pink-color, #e91e63))",
  "var(--euribor-card-loan-4, var(--purple-color, #926bc7))",
  "var(--euribor-card-loan-5, var(--lime-color, #cddc39))"
];
var STALE_HOURS = 108;

// src/data.ts
var PLATFORM = "euribor_rates";
var MONTHS_BY_MATURITY = { "1 month": 1, "3 months": 3, "6 months": 6, "12 months": 12 };
function rateSensors(hass) {
  return Object.values(hass.states).filter(
    (state) => !!state && platformOf(hass, state.entity_id) === PLATFORM && "latest_rate" in state.attributes
  ).map((state) => state.entity_id).sort();
}
function sources(hass, entity) {
  const rate = hass.states[entity];
  const maturity = rate?.attributes.maturity;
  if (!rate || typeof maturity !== "string") {
    return void 0;
  }
  const siblings = (id) => {
    const device = hass.entities?.[id]?.device_id;
    const found = {};
    for (const entry of Object.values(hass.entities ?? {})) {
      if (entry && device && entry.device_id === device && entry.platform === PLATFORM) {
        found[entry.translation_key ?? ""] = entry.entity_id;
      }
    }
    return found;
  };
  const own = siblings(entity);
  const ecbRate = Object.values(hass.states).find(
    (state) => !!state && platformOf(hass, state.entity_id) === PLATFORM && "effective_date" in state.attributes
  );
  return {
    rate,
    maturity,
    history: own.history,
    published: own.published ? hass.states[own.published] : void 0,
    loans: loans(hass, maturity, siblings),
    ecbRate,
    ecbHistory: ecbRate ? siblings(ecbRate.entity_id).history : void 0
  };
}
function loans(hass, maturity, siblings) {
  const result = [];
  for (const state of Object.values(hass.states)) {
    if (!state || platformOf(hass, state.entity_id) !== PLATFORM || !("margin" in state.attributes) || state.attributes.maturity !== maturity) {
      continue;
    }
    const own = siblings(state.entity_id);
    const reference = own.reference_rate ? hass.states[own.reference_rate] : void 0;
    const attributes = state.attributes;
    result.push({
      entity: state.entity_id,
      name: hass.formatEntityName?.(state, [{ type: "device" }]) || String(attributes.friendly_name ?? state.entity_id),
      rate: number(state.state),
      margin: Number(attributes.margin),
      maturity,
      lockDays: Number(attributes.lock_days ?? 0),
      enteredReset: text(attributes.entered_reset),
      pending: attributes.pending === true,
      locked: number(reference?.state),
      rateToday: number(own.rate_today ? hass.states[own.rate_today]?.state : void 0),
      change: number(own.change ? hass.states[own.change]?.state : void 0),
      nextReset: text(own.next_reset ? hass.states[own.next_reset]?.state : void 0)
    });
  }
  return result.sort((a3, b3) => a3.name.localeCompare(b3.name));
}
function platformOf(hass, entity) {
  return hass.entities?.[entity]?.platform;
}
function number(value) {
  const parsed = value === void 0 ? NaN : Number(value);
  return Number.isFinite(parsed) && value !== "" ? parsed : void 0;
}
function text(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : void 0;
}

// src/localize/languages/en.json
var en_default = {
  common: {
    name: "Euribor",
    description: "A Euribor maturity with its history, the ECB's deposit facility rate and the loans that follow it."
  },
  card: {
    published: "{date} rate, published {published}",
    stale: "Published {days} days ago",
    month: "1 mo",
    year: "1 y",
    projection: "if Euribor stays",
    ecb_legend: "ECB deposit rate",
    ecb_short: "ECB",
    locked_legend: "locked Euribor",
    next: "next",
    pending_long: "waiting for the reset day's rate",
    pending_short: "waiting for the rate",
    pending_tiny: "waiting",
    days: "{days} d",
    now: "now",
    at_reset: "at reset",
    locked_line: "Euribor {rate} + {margin}",
    no_entity: "Choose a Euribor maturity in the card's settings.",
    unavailable: "The rates aren't available.",
    range: "Range"
  },
  ranges: {
    "1m": "1 mo",
    "1y": "1 y",
    "2y": "2 y",
    "3y": "3 y",
    "5y": "5 y",
    all: "All"
  },
  editor: {
    entity: "Maturity",
    loans_on_chart: "Loans on the chart",
    loans_on_chart_helper: "The Euribor each reset locked, as a marker or as a line to the next reset.",
    projection: "Projection",
    projection_helper: "Today's Euribor drawn on into the future.",
    ecb: "ECB rate",
    ecb_helper: "Shown once the ECB's rate is added to the integration.",
    markers: "Markers",
    lines: "Lock periods as lines",
    steps: "Steps",
    axis_markers: "Markers on the axis",
    none: "None"
  }
};

// src/localize/languages/fi.json
var fi_default = {
  common: {
    name: "Euribor",
    description: "Euriborin korkojakso historioineen, EKP:n talletuskorko ja sit\xE4 seuraavat lainat."
  },
  card: {
    published: "{date} noteeraus, julkaistu {published}",
    stale: "Julkaistu {days} pv sitten",
    month: "1 kk",
    year: "1 v",
    projection: "jos euribor pysyy",
    ecb_legend: "EKP:n talletuskorko",
    ecb_short: "EKP",
    locked_legend: "lukittu euribor",
    next: "seuraava",
    pending_long: "odottaa tarkistusp\xE4iv\xE4n noteerausta",
    pending_short: "odottaa noteerausta",
    pending_tiny: "odottaa",
    days: "{days} pv",
    now: "nyt",
    at_reset: "tarkistuksessa",
    locked_line: "Euribor {rate} + {margin}",
    no_entity: "Valitse euriborin korkojakso kortin asetuksista.",
    unavailable: "Korot eiv\xE4t ole saatavilla.",
    range: "Aikav\xE4li"
  },
  ranges: {
    "1m": "1 kk",
    "1y": "1 v",
    "2y": "2 v",
    "3y": "3 v",
    "5y": "5 v",
    all: "Kaikki"
  },
  editor: {
    entity: "Korkojakso",
    loans_on_chart: "Lainat kaaviossa",
    loans_on_chart_helper: "Euribor, jonka kukin tarkistus lukitsi, merkkin\xE4 tai viivana seuraavaan tarkistukseen.",
    projection: "Ennuste",
    projection_helper: "T\xE4m\xE4n p\xE4iv\xE4n euribor jatkettuna tulevaan.",
    ecb: "EKP:n korko",
    ecb_helper: "N\xE4kyy, kun EKP:n korko on lis\xE4tty integraatioon.",
    markers: "Merkit",
    lines: "Lukitusjaksot viivoina",
    steps: "Portaina",
    axis_markers: "Merkit akselilla",
    none: "Ei mit\xE4\xE4n"
  }
};

// src/localize/localize.ts
var FILES = { "./languages/en.json": en_default, "./languages/fi.json": fi_default };
var LANGUAGES = Object.fromEntries(
  Object.entries(FILES).map(([path, table]) => [path.replace(/^.*\/|\.json$/g, "").toLowerCase(), table])
);
var LANGUAGE_CODES = Object.keys(LANGUAGES).sort();
function translate(language, key) {
  const code = (language ?? "en").split(/[-_]/)[0].toLowerCase();
  return read(LANGUAGES[code], key) ?? read(LANGUAGES.en, key) ?? key;
}
function read(table, key) {
  let value = table;
  for (const part of key.split(".")) {
    if (value === null || typeof value !== "object") {
      return void 0;
    }
    value = value[part];
  }
  return typeof value === "string" ? value : void 0;
}
function browserLanguage() {
  return document.documentElement.lang || navigator.language || "en";
}

// src/editor.ts
var DEFAULTS = {
  loans_on_chart: "lines",
  projection: true,
  ecb: "steps"
};
function schema(hass, text2) {
  const select = (options) => ({
    select: { mode: "dropdown", options: options.map(([value, label]) => ({ value, label: text2(`editor.${label}`) })) }
  });
  return [
    { name: "entity", required: true, selector: { entity: { include_entities: rateSensors(hass) } } },
    {
      name: "loans_on_chart",
      selector: select([
        ["markers", "markers"],
        ["lines", "lines"],
        ["none", "none"]
      ])
    },
    { name: "projection", selector: { boolean: {} } },
    {
      name: "ecb",
      selector: select([
        ["steps", "steps"],
        ["markers", "axis_markers"],
        ["none", "none"]
      ])
    }
  ];
}
var EuriborCardEditor = class extends i4 {
  constructor() {
    super(...arguments);
    this.config = { type: "custom:euribor-card", entity: "" };
  }
  setConfig(config) {
    this.config = { ...config };
  }
  render() {
    if (!this.hass) {
      return A;
    }
    return b2`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...DEFAULTS, ...this.config }}
                .schema=${schema(this.hass, (key) => this.text(key))}
                .computeLabel=${(entry) => this.text(`editor.${entry.name}`)}
                .computeHelper=${(entry) => this.helper(entry.name)}
                @value-changed=${this.valueChanged}
            ></ha-form>
        `;
  }
  valueChanged(event) {
    const config = { ...event.detail.value };
    for (const [key, value] of Object.entries(DEFAULTS)) {
      if (config[key] === value || config[key] === void 0 || config[key] === null) {
        delete config[key];
      }
    }
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }
  text(key) {
    return translate(this.language(), key);
  }
  helper(name) {
    const key = `editor.${name}_helper`;
    const helper = translate(this.language(), key);
    return helper === key ? void 0 : helper;
  }
  language() {
    return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
  }
};
__decorateClass([
  n4({ attribute: false })
], EuriborCardEditor.prototype, "hass", 2);
__decorateClass([
  r5()
], EuriborCardEditor.prototype, "config", 2);
if (!customElements.get("euribor-card-editor")) {
  customElements.define("euribor-card-editor", EuriborCardEditor);
}

// src/euribor-card.ts
var HISTORY_START = "1998-12-30T00:00:00Z";
var RETRY_MS = 6e4;
var MAX_RETRIES = 5;
var EuriborCard = class extends i4 {
  constructor() {
    super(...arguments);
    this.size = { width: 0, height: 0 };
  }
  static getConfigElement() {
    return document.createElement("euribor-card-editor");
  }
  static getStubConfig(hass) {
    return { entity: hass ? rateSensors(hass)[0] ?? "" : "" };
  }
  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this.config = { ...config };
  }
  getGridOptions() {
    return { columns: 12, min_columns: 12, rows: DEFAULT_ROWS, min_rows: minimumRows(this.sources()?.loans.length ?? 0) };
  }
  getCardSize() {
    return DEFAULT_ROWS;
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this.observer?.disconnect();
    this.observer = void 0;
  }
  updated(changed) {
    super.updated(changed);
    this.observeChart();
    if (changed.has("hass") || changed.has("config")) {
      void this.loadStatistics();
    }
  }
  render() {
    const found = this.sources();
    const outside = this.layout !== "grid" ? `height: ${DEFAULT_ROWS * ROW_HEIGHT + (DEFAULT_ROWS - 1) * ROW_GAP}px` : "";
    if (!this.config?.entity || !found) {
      return b2`<ha-card style=${outside}
                ><div class="message">${this.text(this.config?.entity ? "card.unavailable" : "card.no_entity")}</div></ha-card
            >`;
    }
    const loans2 = found.loans;
    const body = !loans2.length ? this.layoutRate(found) : loans2.length <= 2 ? this.layoutTiles(found) : this.layoutTable(found);
    return b2`<ha-card style=${outside}>${body}</ha-card>`;
  }
  /** No loans: the rate in the header, its changes, the chart. */
  layoutRate(found) {
    return b2`${this.header(found)}${this.changeChips(false)}${this.chartBox(found, [])}${this.legend(found, false)}`;
  }
  /** One or two loans: a tile each, then the rate on one line and the chart. */
  layoutTiles(found) {
    const one = found.loans.length === 1;
    const tiles = found.loans.map((loan, index) => {
      const change = loan.change;
      const next = loan.pending ? b2`<span class="pending"
                      ><ha-icon icon="mdi:timer-sand"></ha-icon
                      ><span class=${one ? "" : "pending-wide"}>${this.text(one ? "card.pending_long" : "card.pending_short")}</span
                      >${one ? A : b2`<span class="pending-narrow">${this.text("card.pending_tiny")}</span>`}</span
                  >` : b2`${one ? `${this.text("card.next")} ` : ""}<b class=${this.tone(change, true)}>${this.signed(change, 3)}</b> →
                      ${this.percent(loan.rateToday, 3)}`;
      const locked = one && loan.locked !== void 0 ? ` \xB7 ${this.text("card.locked_line").replace("{rate}", this.number(loan.locked, 3)).replace("{margin}", this.number(loan.margin, 2))}` : "";
      return b2`<div class="tile">
                <div class="tile-name line" title=${loan.name}>
                    <span class="dot" style="background: ${LOAN_COLORS[index % LOAN_COLORS.length]}"></span>${loan.name}
                </div>
                <div class="tile-rate">${this.percent(loan.rate, 3)}</div>
                <div class="tile-line line">${next}</div>
                <div class="tile-line line">${this.resetLine(loan)}${locked}</div>
            </div>`;
    });
    return b2`<div class="tiles" style="grid-template-columns: repeat(${found.loans.length}, minmax(0, 1fr))">${tiles}</div>
            <div class="rate-line">
                <div class="line">
                    <span class="title">${this.cardTitle(found)}</span>
                    <span class="rate-small ${this.stale(found) ? "stale" : ""}">${this.percent(Number(found.rate.state), 3)}</span>
                </div>
                ${this.ranges()}
            </div>
            ${this.published(found)}${this.chartBox(found, found.loans)}${this.legend(found, this.loanMarks() === "lines")}`;
  }
  /** Three or more loans: the header and the chart, then a line per loan. */
  layoutTable(found) {
    const rows = found.loans.map((loan, index) => {
      const next = loan.pending ? b2`<span class="pending"><ha-icon icon="mdi:timer-sand"></ha-icon>${this.text("card.pending_tiny")}</span>` : b2`<b>${this.percent(loan.rateToday, 2)}</b>
                      <span class=${this.tone(loan.change, true)}>${this.signed(loan.change, 2)}</span>`;
      return b2`<div class="loan-row">
                <span class="loan-name"
                    ><span class="dot" style="background: ${LOAN_COLORS[index % LOAN_COLORS.length]}"></span
                    ><span class="line">${loan.name}</span></span
                >
                <span class="loan-now">${this.percent(loan.rate, 2)}</span>
                <span class="loan-next">${next} · ${loan.nextReset ? this.shortDate(loan.nextReset) : ""}</span>
            </div>`;
    });
    return b2`${this.header(found)}${this.changeChips(true)}${this.chartBox(found, found.loans)}${this.legend(found, this.loanMarks() === "lines")}
            <div class="loans">
                <div class="loan-row loan-head">
                    <span></span><span>${this.text("card.now")}</span><span>${this.text("card.at_reset")}</span>
                </div>
                ${rows}
            </div>`;
  }
  header(found) {
    return b2`<div class="header">
                <div class="header-text">
                    <div class="title line">${this.cardTitle(found)}</div>
                    <div class="rate-big ${this.stale(found) ? "stale" : ""}">
                        ${this.number(Number(found.rate.state), 3)}<small> %</small>
                    </div>
                </div>
                ${this.ranges()}
            </div>
            ${this.published(found)}`;
  }
  published(found) {
    const hours = this.ageHours(found);
    if (hours !== void 0 && hours > STALE_HOURS) {
      return b2`<div class="published stale-text line">
                <ha-icon icon="mdi:clock-alert-outline"></ha-icon
                >${this.text("card.stale").replace("{days}", String(Math.floor(hours / 24)))}
            </div>`;
    }
    const day = found.rate.attributes.latest_date;
    const at = found.published?.state ? new Date(found.published.state) : void 0;
    const when = at && !Number.isNaN(at.getTime()) ? this.dateTime(at) : "";
    return b2`<div class="published line">
            ${typeof day === "string" ? this.text("card.published").replace("{date}", this.shortDate(day)).replace("{published}", when) : ""}
        </div>`;
  }
  changeChips(loans2) {
    const { month, year } = changes(this.statistics?.rates ?? []);
    const chip = (label, value) => value === void 0 ? A : b2`<span class="chip ${this.tone(value, loans2)}">${label} ${this.signed(value, 3)}</span>`;
    return b2`<div class="chips">${chip(this.text("card.month"), month)}${chip(this.text("card.year"), year)}</div>`;
  }
  ranges() {
    const available = this.availableRanges();
    if (available.length < 2) {
      return A;
    }
    const current = this.currentRange();
    return b2`<div class="ranges">
                ${available.map(
      (key) => b2`<button class=${key === current ? "on" : ""} @click=${() => this.range = key}>
                            ${this.text(`ranges.${key}`)}
                        </button>`
    )}
            </div>
            <select
                class="range-select"
                aria-label=${this.text("card.range")}
                @change=${(event) => this.range = event.target.value}
            >
                ${available.map((key) => b2`<option value=${key} ?selected=${key === current}>${this.text(`ranges.${key}`)}</option>`)}
            </select>`;
  }
  chartBox(found, loans2) {
    const input = this.chartInput(found, loans2);
    const point = this.hover && input ? input.rates.find((rate) => rate.day === this.hover) : void 0;
    const ecb2 = point && found.ecbRate && this.ecbMode() !== "none" ? this.statistics?.ecb.filter((rate) => rate.day <= point.day).at(-1) : void 0;
    return b2`<div class="chart" @pointermove=${this.pointerMove} @pointerleave=${() => this.hover = void 0}>
            ${point ? b2`<div class="readout">
                          ${this.shortDate(point.day, true)} ·
                          <b>${this.percent(point.value, 3)}</b
                          >${ecb2 ? b2` · ${this.text("card.ecb_short")} ${this.percent(ecb2.value, 2)}` : A}
                      </div>` : A}
            ${input ? chart(input) : A}
        </div>`;
  }
  chartInput(found, loans2) {
    const rates = this.statistics?.rates ?? [];
    if (!this.size.width || !this.size.height || !rates.length) {
      return void 0;
    }
    const today = this.today();
    const start = rangeStart(this.currentRange(), rates, today);
    const months = MONTHS_BY_MATURITY[found.maturity] ?? 12;
    const chartLoans = loans2.map((loan, index) => ({
      color: LOAN_COLORS[index % LOAN_COLORS.length],
      periods: loan.enteredReset ? lockPeriods(rates, loan.enteredReset, months, loan.lockDays, start, today) : []
    }));
    return {
      width: this.size.width,
      height: this.size.height,
      start,
      today,
      rates: rates.filter((point) => point.day >= start),
      ecb: found.ecbRate ? this.statistics?.ecb ?? [] : [],
      ecbMode: this.ecbMode(),
      loans: chartLoans,
      loanMarks: loans2.length ? this.loanMarks() : "none",
      projection: this.config?.projection !== false,
      hover: this.hover,
      number: (value, digits) => this.number(value, digits),
      month: (day) => this.monthLabel(day),
      date: (day) => this.shortDate(day, true),
      projectionLabel: this.text("card.projection")
    };
  }
  // The rate's own line needs no entry, as the title above it names it in the same colour.
  legend(found, locked) {
    const ecb2 = !!found.ecbRate && this.ecbMode() === "steps";
    if (!locked && !ecb2) {
      return A;
    }
    return b2`<div class="legend">
            ${locked ? b2`<span><i class="swatch lock-swatch"></i>${this.text("card.locked_legend")}</span>` : A}
            ${ecb2 ? b2`<span><i class="swatch ecb-swatch"></i>${this.text("card.ecb_legend")}</span>` : A}
        </div>`;
  }
  pointerMove(event) {
    const found = this.sources();
    const svg = event.currentTarget.querySelector("svg");
    const input = found ? this.chartInput(found, found.loans) : void 0;
    if (!svg || !input) {
      return;
    }
    const box = svg.getBoundingClientRect();
    const day = scale(input).dayAt((event.clientX - box.left) / box.width * input.width);
    const point = input.rates.reduce(
      (best, rate) => !best || Math.abs(Date.parse(rate.day) - Date.parse(day)) < Math.abs(Date.parse(best.day) - Date.parse(day)) ? rate : best,
      void 0
    );
    this.hover = point?.day;
  }
  resetLine(loan) {
    if (!loan.nextReset) {
      return "";
    }
    const days = Math.round((Date.parse(loan.nextReset) - Date.parse(this.today())) / 864e5);
    return `${this.shortDate(loan.nextReset, true)} \xB7 ${this.text("card.days").replace("{days}", String(days))}`;
  }
  observeChart() {
    const box = this.renderRoot.querySelector(".chart");
    if (!box) {
      return;
    }
    if (!this.observer) {
      this.observer = new ResizeObserver(() => this.measureChart());
    }
    this.observer.disconnect();
    this.observer.observe(box);
    this.measureChart();
  }
  measureChart() {
    const box = this.renderRoot.querySelector(".chart");
    if (!box) {
      return;
    }
    const width = Math.floor(box.clientWidth);
    const height = Math.floor(box.clientHeight);
    if (width !== this.size.width || height !== this.size.height) {
      this.size = { width, height };
    }
  }
  async loadStatistics() {
    const found = this.sources();
    if (!this.hass?.callWS || !found?.history) {
      return;
    }
    const ids = [found.history, ...found.ecbHistory ? [found.ecbHistory] : []];
    const key = ids.map((id) => `${id}:${this.hass?.states[id]?.state}`).join("|");
    const now = Date.now();
    const read2 = this.statistics?.key === key ? this.statistics : void 0;
    if (this.loading === key || read2 && (read2.complete || read2.retries >= MAX_RETRIES || now - read2.readAt < RETRY_MS) || this.failed?.key === key && now - this.failed.at < RETRY_MS) {
      return;
    }
    this.loading = key;
    try {
      const rows = await this.hass.callWS({
        type: "recorder/statistics_during_period",
        start_time: HISTORY_START,
        statistic_ids: ids,
        period: "day",
        types: ["mean"]
      });
      const zone = this.hass.config?.time_zone;
      const rates = points(rows[found.history], zone);
      const ecb2 = found.ecbHistory ? points(rows[found.ecbHistory], zone) : [];
      const newest = (series, id) => !id || series.at(-1)?.day === this.hass?.states[id]?.state;
      this.statistics = {
        key,
        rates,
        ecb: ecb2,
        complete: newest(rates, found.history) && newest(ecb2, found.ecbHistory),
        readAt: now,
        retries: read2 ? read2.retries + 1 : 0
      };
      this.failed = void 0;
    } catch (error) {
      this.failed = { key, at: now };
      console.error("euribor-card: the statistics couldn't be read", error);
    } finally {
      this.loading = void 0;
    }
  }
  sources() {
    return this.hass && this.config?.entity ? sources(this.hass, this.config.entity) : void 0;
  }
  availableRanges() {
    return availableRanges(this.statistics?.rates ?? [], this.today());
  }
  currentRange() {
    const available = this.availableRanges();
    if (this.range && available.includes(this.range)) {
      return this.range;
    }
    return available.includes("1y") ? "1y" : "all";
  }
  loanMarks() {
    return this.config?.loans_on_chart ?? "lines";
  }
  ecbMode() {
    return this.config?.ecb ?? "steps";
  }
  ageHours(found) {
    const at = found.published?.state ? Date.parse(found.published.state) : NaN;
    return Number.isNaN(at) ? void 0 : (Date.now() - at) / 36e5;
  }
  stale(found) {
    return (this.ageHours(found) ?? 0) > STALE_HOURS;
  }
  /** Red for a rise and green for a fall where loans show, as a borrower sees them, and neutral otherwise. */
  tone(value, loans2) {
    if (!loans2 || value === void 0 || value === 0) {
      return "";
    }
    return value > 0 ? "up" : "down";
  }
  cardTitle(found) {
    return this.hass?.formatEntityName?.(found.rate, [{ type: "device" }]) || String(found.rate.attributes.friendly_name ?? "Euribor");
  }
  today() {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: this.hass?.config?.time_zone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(/* @__PURE__ */ new Date());
  }
  number(value, digits) {
    return new Intl.NumberFormat(this.language(), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  }
  percent(value, digits) {
    return value === void 0 || Number.isNaN(value) ? "\u2013" : `${this.number(value, digits)} %`;
  }
  signed(value, digits) {
    if (value === void 0) {
      return "\u2013";
    }
    return `${value > 0 ? "+" : value < 0 ? "\u2212" : "\xB1"}${this.number(Math.abs(value), digits)}`;
  }
  shortDate(day, year = false) {
    const options = year ? { day: "numeric", month: "numeric", year: "numeric" } : { day: "numeric", month: "numeric" };
    return new Intl.DateTimeFormat(this.language(), { ...options, timeZone: "UTC" }).format(/* @__PURE__ */ new Date(`${day}T12:00:00Z`));
  }
  dateTime(at) {
    return new Intl.DateTimeFormat(this.language(), {
      day: "numeric",
      month: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZone: this.hass?.config?.time_zone
    }).format(at);
  }
  monthLabel(day) {
    const date = /* @__PURE__ */ new Date(`${day}T12:00:00Z`);
    const span = this.currentRange() === "1m";
    if (span) {
      return this.shortDate(day);
    }
    const month = new Intl.DateTimeFormat(this.language(), { month: "short", timeZone: "UTC" }).format(date).replace(".", "");
    return date.getUTCMonth() === 0 ? `${month} ${String(date.getUTCFullYear()).slice(2)}` : month;
  }
  text(key) {
    return translate(this.language(), key);
  }
  language() {
    return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
  }
};
EuriborCard.styles = i`
        :host {
            --euribor-card-rate: var(--primary-color);
            --euribor-card-ecb: var(--purple-color, #926bc7);
        }
        ha-card {
            box-sizing: border-box;
            height: 100%;
            padding: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            container-type: inline-size;
        }
        .message {
            color: var(--secondary-text-color);
        }
        .line {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            min-width: 0;
        }
        .header,
        .rate-line {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            flex: none;
        }
        .rate-line {
            align-items: baseline;
            margin-top: 12px;
        }
        .header-text {
            min-width: 0;
        }
        .title {
            color: var(--secondary-text-color);
            font-size: 14px;
        }
        .rate-big {
            font-size: 28px;
            font-weight: 600;
            line-height: 1.15;
            color: var(--euribor-card-rate);
        }
        .rate-big small {
            font-size: 15px;
            font-weight: 500;
        }
        .rate-small {
            font-size: 16px;
            font-weight: 600;
            color: var(--euribor-card-rate);
        }
        .stale {
            color: var(--secondary-text-color);
        }
        .published {
            flex: none;
            font-size: 12px;
            color: var(--secondary-text-color);
        }
        .stale-text {
            color: var(--warning-color);
        }
        .published ha-icon,
        .pending ha-icon {
            --mdc-icon-size: 14px;
            vertical-align: -2px;
            margin-right: 2px;
        }
        .chips {
            display: flex;
            gap: 6px;
            margin-top: 6px;
            flex: none;
            min-height: 20px;
        }
        .chip {
            font-size: 12px;
            line-height: 18px;
            padding: 0 7px;
            border-radius: 999px;
            background: rgba(127, 127, 127, 0.12);
            color: var(--secondary-text-color);
            white-space: nowrap;
        }
        .up {
            color: var(--error-color);
        }
        .down {
            color: var(--success-color);
        }
        .chip.up {
            background: color-mix(in srgb, var(--error-color) 12%, transparent);
        }
        .chip.down {
            background: color-mix(in srgb, var(--success-color) 12%, transparent);
        }
        .pending {
            color: var(--warning-color);
        }
        .ranges {
            display: flex;
            gap: 2px;
            flex: none;
        }
        .ranges button {
            background: transparent;
            border: 0;
            color: var(--secondary-text-color);
            font: inherit;
            font-size: 12px;
            padding: 3px 7px;
            border-radius: 8px;
            cursor: pointer;
        }
        .ranges button.on {
            background: color-mix(in srgb, var(--primary-color) 15%, transparent);
            color: var(--primary-color);
        }
        .range-select {
            display: none;
            flex: none;
            font: inherit;
            font-size: 12px;
            color: var(--primary-color);
            background: transparent;
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 2px 4px;
        }
        /* Below 394 px of card the six range buttons don't fit beside the title, so they turn into a list. */
        .pending-narrow {
            display: none;
        }
        @container (max-width: 360px) {
            .ranges,
            .pending-wide {
                display: none;
            }
            .pending-narrow {
                display: inline;
            }
            .range-select {
                display: block;
            }
        }
        .chart {
            flex: 1 1 0;
            min-height: 0;
            margin: 8px -4px 0;
            position: relative;
            touch-action: pan-y;
        }
        .chart svg {
            display: block;
            position: absolute;
            inset: 0;
        }
        .readout {
            position: absolute;
            top: 0;
            left: 4px;
            z-index: 1;
            font-size: 12px;
            padding: 1px 6px;
            border-radius: 6px;
            background: var(--card-background-color);
            pointer-events: none;
            white-space: nowrap;
        }
        .grid {
            stroke: var(--divider-color);
            stroke-width: 1;
        }
        .axis {
            fill: var(--secondary-text-color);
            font-size: 10px;
        }
        .axis.small {
            font-size: 9px;
        }
        .future {
            fill: rgba(127, 127, 127, 0.06);
        }
        .rate {
            fill: none;
            stroke: var(--euribor-card-rate);
            stroke-width: 1.6;
            stroke-linejoin: round;
        }
        .projection {
            stroke-dasharray: 3 4;
            opacity: 0.7;
        }
        .ecb-step {
            fill: none;
            stroke: var(--euribor-card-ecb);
            stroke-width: 1.5;
            stroke-dasharray: 4 3;
        }
        .ecb {
            fill: var(--euribor-card-ecb);
        }
        .ecb-mark {
            stroke: var(--euribor-card-ecb);
            opacity: 0.35;
        }
        .ecb-label {
            fill: var(--euribor-card-ecb);
            font-size: 9px;
        }
        .lock {
            stroke-width: 3;
            stroke-linecap: round;
            opacity: 0.6;
        }
        .marker {
            fill: var(--card-background-color);
            stroke-width: 2;
        }
        .hover {
            stroke: var(--secondary-text-color);
            opacity: 0.6;
        }
        .hover-dot {
            fill: var(--euribor-card-rate);
        }
        .legend {
            display: flex;
            gap: 12px;
            margin-top: 4px;
            flex: none;
            font-size: 11px;
            color: var(--secondary-text-color);
            white-space: nowrap;
            overflow: hidden;
        }
        .swatch {
            display: inline-block;
            width: 12px;
            height: 2px;
            vertical-align: middle;
            margin-right: 4px;
        }
        .lock-swatch {
            height: 3px;
            background: var(--secondary-text-color);
        }
        .ecb-swatch {
            background: var(--euribor-card-ecb);
        }
        .dot {
            display: inline-block;
            flex: none;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .tiles {
            display: grid;
            gap: 10px;
            flex: none;
        }
        .tile {
            min-width: 0;
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid var(--divider-color);
        }
        .tile-name {
            font-size: 13px;
            color: var(--secondary-text-color);
        }
        .tile-rate {
            font-size: 24px;
            font-weight: 600;
            margin: 1px 0;
        }
        .tile-line {
            font-size: 12px;
            line-height: 1.55;
            color: var(--secondary-text-color);
        }
        .tile-line b {
            font-weight: 600;
        }
        .loans {
            flex: none;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid var(--divider-color);
        }
        .loan-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto auto;
            gap: 10px;
            align-items: baseline;
            font-size: 13px;
            line-height: 24px;
        }
        .loan-head {
            font-size: 11px;
            line-height: 16px;
            color: var(--secondary-text-color);
        }
        .loan-head span:not(:first-child),
        .loan-now,
        .loan-next {
            text-align: right;
        }
        .loan-name {
            display: flex;
            align-items: center;
            min-width: 0;
        }
        .loan-now {
            font-weight: 600;
        }
        .loan-next {
            font-size: 12px;
            color: var(--secondary-text-color);
            white-space: nowrap;
        }
        .loan-next b {
            color: var(--primary-text-color);
            font-weight: 600;
        }
    `;
__decorateClass([
  n4({ attribute: false })
], EuriborCard.prototype, "hass", 2);
__decorateClass([
  n4({ attribute: false })
], EuriborCard.prototype, "layout", 2);
__decorateClass([
  r5()
], EuriborCard.prototype, "config", 2);
__decorateClass([
  r5()
], EuriborCard.prototype, "statistics", 2);
__decorateClass([
  r5()
], EuriborCard.prototype, "range", 2);
__decorateClass([
  r5()
], EuriborCard.prototype, "hover", 2);
__decorateClass([
  r5()
], EuriborCard.prototype, "size", 2);
if (!customElements.get("euribor-card")) {
  console.info(
    `%c  EURIBOR-CARD 
%c  ${CARD_VERSION}    `,
    "color: orange; font-weight: bold; background: black",
    "color: white; font-weight: bold; background: dimgray"
  );
  const registry = window;
  registry.customCards = registry.customCards ?? [];
  registry.customCards.push({
    type: "euribor-card",
    name: translate(browserLanguage(), "common.name"),
    description: translate(browserLanguage(), "common.description"),
    documentationURL: "https://github.com/jesmak/euribor_rates#euribor-card",
    preview: true
  });
  customElements.define("euribor-card", EuriborCard);
}
export {
  EuriborCard
};
