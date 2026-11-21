/* 数独组件（同时服务对角线数独 sudokux） */

function renderSudoku(entry, root) {
  const grid = entry.puzzle.grid;
  const sol = entry.solution.grid;
  const n = 9;
  let user = grid.map((row) => row.map((v) => (v === 0 ? "" : String(v))));
  const given = grid.map((row) => row.map((v) => v !== 0));

  const card = PF.el("div", "card");
  card.appendChild(PF.el("h2", null, (entry.display_name || "数独") + " " + PF.stars(entry.difficulty)));
  card.appendChild(PF.el("p", "detail", entry.difficulty_detail));
  if (entry.puzzle.note) card.appendChild(PF.el("p", "note", entry.puzzle.note));

  const table = PF.el("table", "sudoku");
  const inputs = [];
  for (let r = 0; r < n; r++) {
    const tr = PF.el("tr");
    inputs.push(new Array(n).fill(null));
    for (let c = 0; c < n; c++) {
      const td = PF.el("td");
      if (given[r][c]) {
        td.classList.add("given");
        td.textContent = String(grid[r][c]);
      } else {
        const inp = document.createElement("input");
        inp.type = "text";
        inp.maxLength = 1;
        inp.inputMode = "numeric";
        inp.value = user[r][c];
        inp.addEventListener("input", () => {
          const v = inp.value.replace(/[^1-9]/g, "");
          inp.value = v;
          user[r][c] = v;
          inp.classList.remove("wrong");
        });
        td.appendChild(inp);
        inputs[r][c] = inp;
      }
      if (c % 3 === 2 && c < 8) td.classList.add("br");
      if (r % 3 === 2 && r < 8) td.classList.add("bb");
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  card.appendChild(table);

  const msg = PF.el("p", "msg");
  const actions = PF.el("div", "actions");
  const btnCheck = PF.el("button", "btn primary", "检查答案");
  const btnReveal = PF.el("button", "btn", "查看答案");
  const btnReset = PF.el("button", "btn ghost", "清空重填");
  actions.append(btnCheck, btnReveal, btnReset);
  card.append(actions, msg);

  btnCheck.addEventListener("click", () => {
    let done = true;
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        const inp = inputs[r][c];
        if (!inp) continue;
        const ok = user[r][c] !== "" && user[r][c] === String(sol[r][c]);
        inp.classList.toggle("wrong", !ok);
        if (!ok) done = false;
      }
    }
    msg.textContent = done ? "🎉 全部正确！" : "还有错误，红色格子再想想。";
    msg.className = "msg " + (done ? "ok" : "bad");
  });
  btnReveal.addEventListener("click", () => {
    for (let r = 0; r < n; r++)
      for (let c = 0; c < n; c++) {
        const inp = inputs[r][c];
        if (!inp) continue;
        user[r][c] = String(sol[r][c]);
        inp.value = user[r][c];
        inp.classList.remove("wrong");
      }
    msg.textContent = "已展示完整答案。";
    msg.className = "msg";
  });
  btnReset.addEventListener("click", () => {
    for (let r = 0; r < n; r++)
      for (let c = 0; c < n; c++) {
        const inp = inputs[r][c];
        if (!inp) continue;
        user[r][c] = "";
        inp.value = "";
        inp.classList.remove("wrong");
      }
    msg.textContent = "";
  });

  root.appendChild(card);
}

PF.register("sudoku", renderSudoku);
PF.register("sudokux", renderSudoku);
