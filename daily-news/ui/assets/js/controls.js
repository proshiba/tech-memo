// 画面共通の小さな部品。3 つの一覧画面（ニュース / イベント / IOC）で同じものを
// 使い回す。ここに置いてあるのは「見た目と操作が同じもの」だけで、
// 絞り込みの意味づけは各画面が持つ。

import { el, copy } from "./util.js";

/** チェックボックス 1 つ。 */
export function toggle(label, checked, onchange) {
  const input = el("input", { type: "checkbox", checked, onchange: (e) => onchange(e.target.checked) });
  return el("label", { class: "check" }, [input, el("span", { text: label })]);
}

/**
 * ラベルつきのセレクト。
 *
 * options は [値, 表示] の並び。deep link で来た値が options に無いことがあるので
 * （ファセット上位に入っていない値など）、その場合は選択肢を足してから選ぶ。
 */
export function selectField(id, label, options, value, onchange, { title = "" } = {}) {
  const node = el("select", { id, class: "input", onchange: (e) => onchange(e.target.value) },
    options.map(([v, t]) => el("option", { value: v, text: t })));
  node.value = value || "";
  if (value && node.value !== value) {
    node.append(el("option", { value, text: value }));
    node.value = value;
  }
  return el("div", { class: "field" }, [
    el("label", { class: "field-label", for: id, text: label, title }),
    node,
  ]);
}

/** 値をクリップボードに写すボタン。押した結果をその場に出す。 */
export function copyButton(value) {
  return el("button", {
    class: "icon-btn", type: "button", title: "コピー", text: "⧉",
    onclick: async (e) => {
      const ok = await copy(value);
      const btn = e.currentTarget;
      btn.textContent = ok ? "✓" : "×";
      setTimeout(() => { btn.textContent = "⧉"; }, 900);
    },
  });
}

/** `ioc.sha256` → `sha256`。表の見出しに置く用。 */
export function shortType(type) {
  return String(type).replace(/^ioc\./, "");
}
