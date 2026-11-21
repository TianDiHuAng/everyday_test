/* 网格逻辑题组件 */

PF.register("logic", function (entry, root) {
  const { entities, categories, clues } = entry.puzzle;
  const solution = entry.solution.assignment;

  const card = PF.el("div", "card");
  card.appendChild(PF.el("h2", null, "逻辑推理 " + PF.stars(entry.difficulty)));
  card.appendChild(PF.el("p", "detail", entry.difficulty_detail));

  const clueBox = PF.el("ol", "clues");
  clues.forEach((c) => {
    clueBox.appendChild(PF.el("li", null, c.text));
  });
  card.appendChild(clueBox);

  const table = PF.el("table", "logic-grid");
  const head = PF.el("tr");
  head.appendChild(PF.el("th", null, ""));
  categories.forEach((cat) => head.appendChild(PF.el("th", null, cat.name)));
  table.appendChild(head);

  const selects = {};
  entities.forEach((name) => {
    const tr = PF.el("tr");
    tr.appendChild(PF.el("th", null, name));
    categories.forEach((cat) => {
      const td = PF.el("td");
      const sel = document.createElement("select");
      sel.appendChild(new Option("—", ""));
      cat.values.forEach((v) => sel.appendChild(new Option(v, v)));
      sel.value = "";
      sel.dataset.entity = name;
      sel.dataset.cat = cat.name;
      sel.addEventListener("change", () => sel.classList.remove("wrong"));
      selects[name + "|" + cat.name] = sel;
      td.appendChild(sel);
      tr.appendChild(td);
    });
    table.appendChild(tr);
  });
  card.appendChild(table);

  const msg = PF.el("p", "msg");
  const actions = PF.el("div", "actions");
  const btnCheck = PF.el("button", "btn primary", "检查答案");
  const btnReveal = PF.el("button", "btn", "查看答案");
  actions.append(btnCheck, btnReveal);
  card.append(actions, msg);

  btnCheck.addEventListener("click", () => {
    let done = true;
    entities.forEach((name) => {
      categories.forEach((cat) => {
        const sel = selects[name + "|" + cat.name];
        const ok = sel.value !== "" && sel.value === solution[name][cat.name];
        sel.classList.toggle("wrong", !ok);
        if (!ok) done = false;
      });
    });
    msg.textContent = done ? "🎉 全部正确！" : "还有错误，红色选项再想想。";
    msg.className = "msg " + (done ? "ok" : "bad");
  });
  btnReveal.addEventListener("click", () => {
    entities.forEach((name) => {
      categories.forEach((cat) => {
        const sel = selects[name + "|" + cat.name];
        sel.value = solution[name][cat.name];
        sel.classList.remove("wrong");
      });
    });
    msg.textContent = "已展示完整答案。";
    msg.className = "msg";
  });

  root.appendChild(card);
});
