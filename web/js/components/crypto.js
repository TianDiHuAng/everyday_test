/* 密码谜题组件：替换密码 + 算式谜题两个子型 */

PF.register("crypto", function (entry, root) {
  const p = entry.puzzle;
  const card = PF.el("div", "card");
  card.appendChild(PF.el("h2", null, "密码谜题 " + PF.stars(entry.difficulty)));
  card.appendChild(PF.el("p", "detail", entry.difficulty_detail));

  const msg = PF.el("p", "msg");
  const actions = PF.el("div", "actions");
  const btnCheck = PF.el("button", "btn primary", "检查答案");
  const btnReveal = PF.el("button", "btn", "查看答案");
  actions.append(btnCheck, btnReveal);

  if (p.subtype === "substitution") {
    card.appendChild(PF.el("p", "note", p.note));
    const cipherBox = PF.el("div", "cipher");
    cipherBox.textContent = p.cipher;
    card.appendChild(cipherBox);

    // 明码提示
    if (p.hints && Object.keys(p.hints).length) {
      const hintBox = PF.el("div", "hint-chips");
      Object.entries(p.hints).forEach(([k, v]) => {
        hintBox.appendChild(PF.el("span", "chip", `${k} → ${v}`));
      });
      card.appendChild(hintBox);
    }

    // 映射编辑器（密文字母 → 猜测明文字母）
    const letters = [...new Set(p.cipher.replace(/[^a-z]/g, ""))].sort();
    const mapBox = PF.el("div", "map-box");
    const mapInputs = {};
    letters.forEach((ch) => {
      const row = PF.el("div", "map-row");
      row.appendChild(PF.el("span", "map-key", ch));
      const inp = document.createElement("input");
      inp.maxLength = 1;
      inp.value = p.hints[ch] || "";
      if (p.hints[ch]) inp.disabled = true;
      inp.dataset.cipher = ch;
      inp.addEventListener("input", () => {
        inp.value = inp.value.replace(/[^a-z]/g, "");
        updatePreview();
      });
      mapInputs[ch] = inp;
      row.appendChild(inp);
      mapBox.appendChild(row);
    });
    card.appendChild(mapBox);

    const preview = PF.el("div", "cipher preview");
    card.appendChild(preview);
    function updatePreview() {
      preview.textContent = p.cipher
        .split("")
        .map((ch) => (/[a-z]/.test(ch) ? mapInputs[ch].value || "·" : ch))
        .join("");
    }
    updatePreview();

    btnCheck.addEventListener("click", () => {
      const target = entry.solution.pinyin;
      const decoded = p.cipher
        .split("")
        .map((ch) => (/[a-z]/.test(ch) ? mapInputs[ch].value : ch))
        .join("");
      const done = decoded === target;
      msg.textContent = done
        ? `🎉 破译成功！「${entry.solution.text}」——${entry.solution.source}`
        : "还未破译成功，试试结合拼音规律和名句知识。";
      msg.className = "msg " + (done ? "ok" : "bad");
    });
    btnReveal.addEventListener("click", () => {
      letters.forEach((ch) => {
        if (!p.hints[ch]) mapInputs[ch].value = entry.solution.mapping[ch];
      });
      updatePreview();
      msg.textContent = `答案：「${entry.solution.text}」（${entry.solution.source}）`;
      msg.className = "msg";
    });
  } else {
    // 算式谜题 cryptarithm
    card.appendChild(PF.el("p", "note", p.note));
    const eqBox = PF.el("div", "equation");
    eqBox.textContent = p.equation;
    card.appendChild(eqBox);

    const letters = [...new Set(p.equation.replace(/[^A-Z]/g, ""))].sort();
    const mapBox = PF.el("div", "map-box");
    const mapInputs = {};
    letters.forEach((ch) => {
      const row = PF.el("div", "map-row");
      row.appendChild(PF.el("span", "map-key", ch));
      const inp = document.createElement("input");
      inp.maxLength = 1;
      inp.inputMode = "numeric";
      inp.dataset.cipher = ch;
      inp.addEventListener("input", () => {
        inp.value = inp.value.replace(/[^0-9]/g, "");
      });
      mapInputs[ch] = inp;
      row.appendChild(inp);
      mapBox.appendChild(row);
    });
    card.appendChild(mapBox);
    if (entry.hints && entry.hints.length) {
      const hintBox = PF.el("div", "hint-chips");
      entry.hints.forEach((h) => hintBox.appendChild(PF.el("span", "chip", h)));
      card.appendChild(hintBox);
    }

    btnCheck.addEventListener("click", () => {
      const sol = entry.solution.digits;
      let done = true;
      letters.forEach((ch) => {
        const ok = mapInputs[ch].value !== "" && Number(mapInputs[ch].value) === sol[ch];
        mapInputs[ch].classList.toggle("wrong", !ok);
        if (!ok) done = false;
      });
      msg.textContent = done ? `🎉 正确！${entry.solution.equation_numbers}` : "还有错误，注意进位和首位不为 0。";
      msg.className = "msg " + (done ? "ok" : "bad");
    });
    btnReveal.addEventListener("click", () => {
      letters.forEach((ch) => {
        mapInputs[ch].value = String(entry.solution.digits[ch]);
        mapInputs[ch].classList.remove("wrong");
      });
      msg.textContent = `答案：${entry.solution.equation_numbers}`;
      msg.className = "msg";
    });
  }

  card.append(actions, msg);
  root.appendChild(card);
});
