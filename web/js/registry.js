/* 前端渲染器注册表：题型 → 组件。
 * 未注册的题型自动回退到通用卡片，后端新增题型时页面照常工作。 */

window.PF = {
  renderers: {},

  register(type, fn) {
    this.renderers[type] = fn;
  },

  render(entry, root) {
    root.innerHTML = "";
    const fn = this.renderers[entry.type];
    if (fn) {
      fn(entry, root);
      return;
    }
    this.renderFallback(entry, root);
  },

  renderFallback(entry, root) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h2>${entry.display_name || entry.type}</h2>
      <p class="detail">${entry.difficulty_detail || ""}</p>
      <pre class="raw">${JSON.stringify(entry.puzzle, null, 2)}</pre>
      <div class="actions">
        <button class="btn reveal">查看答案</button>
      </div>
      <pre class="raw solution hidden">${JSON.stringify(entry.solution, null, 2)}</pre>`;
    card.querySelector(".reveal").addEventListener("click", () => {
      card.querySelector(".solution").classList.toggle("hidden");
    });
    root.appendChild(card);
  },

  stars(difficulty) {
    return "★".repeat(difficulty) + "☆".repeat(Math.max(0, 5 - difficulty));
  },

  el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  },
};
