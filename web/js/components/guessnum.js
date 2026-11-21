/* 猜数字（1A2B）组件 */

PF.register("guessnum", function (entry, root) {
  const p = entry.puzzle;
  const secret = entry.solution.secret;
  const length = p.length;

  const card = PF.el("div", "card");
  card.appendChild(PF.el("h2", null, (entry.display_name || "猜数字") + " " + PF.stars(entry.difficulty)));
  card.appendChild(PF.el("p", "detail", entry.difficulty_detail));
  card.appendChild(PF.el("p", "note", p.note));

  // 线索表
  const table = PF.el("table", "logic-grid");
  const head = PF.el("tr");
  ["猜测", "A（位置对）", "B（数字对）"].forEach((h) => head.appendChild(PF.el("th", null, h)));
  table.appendChild(head);
  p.clues.forEach((c) => {
    const tr = PF.el("tr");
    const g = PF.el("td");
    g.style.fontFamily = "Consolas, monospace";
    g.style.fontSize = "18px";
    g.textContent = c.guess;
    tr.appendChild(g);
    tr.appendChild(PF.el("td", null, String(c.a)));
    tr.appendChild(PF.el("td", null, String(c.b)));
    table.appendChild(tr);
  });
  card.appendChild(table);

  // 答案输入
  const inputRow = PF.el("div", "map-box");
  const inputs = [];
  for (let i = 0; i < length; i++) {
    const inp = document.createElement("input");
    inp.maxLength = 1;
    inp.inputMode = "numeric";
    inp.style.width = "44px";
    inp.style.height = "40px";
    inp.style.fontSize = "22px";
    inp.addEventListener("input", () => {
      inp.value = inp.value.replace(/[^0-9]/g, "");
      inp.classList.remove("wrong");
    });
    inputs.push(inp);
    inputRow.appendChild(inp);
  }
  card.appendChild(inputRow);

  const msg = PF.el("p", "msg");
  const actions = PF.el("div", "actions");
  const btnCheck = PF.el("button", "btn primary", "检查答案");
  const btnReveal = PF.el("button", "btn", "查看答案");
  actions.append(btnCheck, btnReveal);
  card.append(actions, msg);

  btnCheck.addEventListener("click", () => {
    const guess = inputs.map((i) => i.value).join("");
    if (guess.length !== length) {
      msg.textContent = `请填满 ${length} 位数字。`;
      msg.className = "msg bad";
      return;
    }
    const done = guess === secret;
    if (done) {
      msg.textContent = `🎉 破解成功！答案就是 ${secret}`;
    } else {
      // 给玩家本次尝试的 xAyB 反馈，帮助推理
      const a = [...guess].filter((ch, i) => ch === secret[i]).length;
      const b = [...new Set(guess)].filter((ch) => secret.includes(ch)).length - a;
      msg.textContent = `不对。你的猜测反馈：${a}A${b}B，继续推理！`;
      msg.className = "msg bad";
    }
  });
  btnReveal.addEventListener("click", () => {
    [...secret].forEach((ch, i) => {
      inputs[i].value = ch;
      inputs[i].classList.remove("wrong");
    });
    msg.textContent = `答案：${secret}`;
    msg.className = "msg";
  });

  root.appendChild(card);
});
