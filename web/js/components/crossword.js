/* 中文填字组件 */

PF.register("crossword", function (entry, root) {
  const { size, layout, clues } = entry.puzzle;
  const sol = entry.solution.grid;

  const card = PF.el("div", "card");
  card.appendChild(PF.el("h2", null, "中文填字 " + PF.stars(entry.difficulty)));
  card.appendChild(PF.el("p", "detail", entry.difficulty_detail));

  // 编号：起点格 → 号码
  const numbers = {};
  ["across", "down"].forEach((dir) => {
    clues[dir].forEach((c) => {
      numbers[c.row + "," + c.col] = c.number;
    });
  });

  const table = PF.el("table", "crossword");
  const inputs = {};
  for (let r = 0; r < size; r++) {
    const tr = PF.el("tr");
    for (let c = 0; c < size; c++) {
      const td = PF.el("td");
      if (layout[r][c]) {
        td.classList.add("white");
        const num = numbers[r + "," + c];
        if (num) {
          const sup = PF.el("span", "num", String(num));
          td.appendChild(sup);
        }
        const inp = document.createElement("input");
        inp.type = "text";
        inp.maxLength = 1;
        inp.dataset.key = r + "," + c;
        inp.addEventListener("input", () => {
          inp.value = inp.value.replace(/[^\u4e00-\u9fff]/g, "");
          inp.classList.remove("wrong");
        });
        inp.dataset.dirClues = "";
        td.appendChild(inp);
        inputs[r + "," + c] = inp;
      } else {
        td.classList.add("black");
      }
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  card.appendChild(table);

  // 线索列表
  const clueWrap = PF.el("div", "cw-clues");
  const clueLists = {};
  [["across", "横向"], ["down", "纵向"]].forEach(([dir, label]) => {
    const box = PF.el("div", "cw-col");
    box.appendChild(PF.el("h3", null, label));
    const ol = PF.el("ol");
    clueLists[dir] = [];
    clues[dir].forEach((c) => {
      const li = PF.el("li", null, c.text);
      li.addEventListener("click", () => {
        const inp = inputs[c.row + "," + c.col];
        if (inp) inp.focus();
      });
      ol.appendChild(li);
    });
    box.appendChild(ol);
    clueWrap.appendChild(box);
  });
  card.appendChild(clueWrap);

  const msg = PF.el("p", "msg");
  const actions = PF.el("div", "actions");
  const btnCheck = PF.el("button", "btn primary", "检查答案");
  const btnReveal = PF.el("button", "btn", "查看答案");
  actions.append(btnCheck, btnReveal);
  card.append(actions, msg);

  btnCheck.addEventListener("click", () => {
    let done = true;
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const inp = inputs[r + "," + c];
        if (!inp) continue;
        const ok = inp.value !== "" && inp.value === sol[r][c];
        inp.classList.toggle("wrong", !ok);
        if (!ok) done = false;
      }
    }
    msg.textContent = done ? "🎉 全部正确！" : "还有错误，红色格子再想想。";
    msg.className = "msg " + (done ? "ok" : "bad");
  });
  btnReveal.addEventListener("click", () => {
    for (let r = 0; r < size; r++)
      for (let c = 0; c < size; c++) {
        const inp = inputs[r + "," + c];
        if (!inp) continue;
        inp.value = sol[r][c];
        inp.classList.remove("wrong");
      }
    msg.textContent = "已展示完整答案。";
    msg.className = "msg";
  });

  root.appendChild(card);
});
