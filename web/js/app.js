/* 每日一题主页面：日期导航 + 题型 Tab + 装载当日内容 */

(function () {
  const app = document.getElementById("app");
  const dateInput = document.getElementById("date-input");
  // 内容库路径：本地开发在 /web/ 子路径下（../content/），部署在根路径（content/）
  const CONTENT_BASE = window.location.pathname.split("/").includes("web")
    ? "../content/"
    : "content/";

  function todayStr() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function getDate() {
    const q = new URLSearchParams(location.search).get("date");
    return /^\d{4}-\d{2}-\d{2}$/.test(q || "") ? q : todayStr();
  }

  function setDate(d) {
    history.replaceState(null, "", "?date=" + d);
    load(d);
  }

  // 主推：周五全科目日，其余按星期轮换当日题型之一（索引随当日题数取模）
  function featuredIndex(dateStr, count) {
    const day = new Date(dateStr + "T12:00:00").getDay(); // 0=周日
    if (day === 5) return "all";
    return day % count;
  }

  async function load(dateStr) {
    app.innerHTML = '<div class="loading">加载中…</div>';
    dateInput.value = dateStr;
    let data;
    try {
      const resp = await fetch(`${CONTENT_BASE}${dateStr}.json`);
      if (!resp.ok) throw new Error(resp.status);
      data = await resp.json();
    } catch (e) {
      app.innerHTML = `
        <div class="card empty">
          <h2>${dateStr} 还没有内容</h2>
          <p>运行生成器补上这一天：</p>
          <pre>python -m puzzleforge generate --date ${dateStr}</pre>
        </div>`;
      return;
    }
    render(dateStr, data);
  }

  function render(dateStr, data) {
    app.innerHTML = "";
    const featured = featuredIndex(dateStr, data.puzzles.length);

    const head = PF.el("div", "day-head");
    const title = PF.el("h1", null, `${dateStr} · 每日一题`);
    head.appendChild(title);
    if (featured === "all") {
      head.appendChild(PF.el("span", "featured-badge", "⭐ 周五全科目日"));
    }
    app.appendChild(head);

    const tabs = PF.el("div", "tabs");
    const panes = PF.el("div", "panes");
    const tabBtns = [];
    const paneEls = [];

    function activate(idx) {
      tabBtns.forEach((b, i) => b.classList.toggle("active", i === idx));
      paneEls.forEach((p, i) => p.classList.toggle("hidden", i !== idx));
    }

    data.puzzles.forEach((entry, idx) => {
      const btn = PF.el("button", "tab", `${entry.display_name || entry.type} ${PF.stars(entry.difficulty)}`);
      if (featured === idx || featured === "all") {
        btn.classList.add("featured");
        btn.title = "今日主推";
      }
      btn.addEventListener("click", () => activate(idx));
      tabs.appendChild(btn);
      tabBtns.push(btn);

      const pane = PF.el("div", "pane");
      PF.render(entry, pane);
      panes.appendChild(pane);
      paneEls.push(pane);
    });

    app.append(tabs, panes);

    activate(featured === "all" ? 0 : featured);
  }

  document.getElementById("prev-day").addEventListener("click", () => {
    const d = new Date(getDate() + "T12:00:00");
    d.setDate(d.getDate() - 1);
    setDate(d.toISOString().slice(0, 10));
  });
  document.getElementById("next-day").addEventListener("click", () => {
    const d = new Date(getDate() + "T12:00:00");
    d.setDate(d.getDate() + 1);
    setDate(d.toISOString().slice(0, 10));
  });
  document.getElementById("today-btn").addEventListener("click", () => setDate(todayStr()));
  dateInput.addEventListener("change", () => {
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateInput.value)) setDate(dateInput.value);
  });

  load(getDate());
})();
