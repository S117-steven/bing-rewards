/* Bing 双号刷积分 - 前端脚本 */

window.addLog = function(msg) {
  const el = document.getElementById("log-console");
  if (!el) return;
  const t = new Date().toTimeString().split(' ')[0];
  el.textContent += `\n[${t}] ${msg}`;
  el.parentElement.scrollTop = el.parentElement.scrollHeight;
};

window.updateProgress = function(pct, text) {
  const c = document.getElementById("progress-container");
  const b = document.getElementById("progress-bar");
  const l = document.getElementById("progress-text");
  if (pct === null || pct < 0) { c.classList.add("hidden"); return; }
  c.classList.remove("hidden");
  b.style.width = `${pct * 100}%`;
  l.textContent = text || "";
};

window.updateCard = function(which, state, detail) {
  const s = document.getElementById(`state-${which}`);
  const d = document.getElementById(`detail-${which}`);
  if (s) { s.textContent = state; s.className = "card-state"; }
  if (d) d.textContent = detail || "-";
};

window.setCardClass = function(which, cls) {
  const s = document.getElementById(`state-${which}`);
  if (s) s.classList.add(cls);
};

window.setButtons = function(running) {
  document.getElementById("btn-start").disabled = running;
  document.getElementById("btn-stop").disabled = !running;
  // 设置区域在运行时禁用
  document.querySelectorAll('.settings-card input').forEach(el => {
    el.disabled = running;
  });
};

function getSelectedMode() {
  return document.querySelector('input[name="exec-mode"]:checked').value;
}

function getDelayMinutes() {
  return parseInt(document.getElementById("delay-minutes").value) || 30;
}

function getScheduleTime() {
  return document.getElementById("schedule-time").value || "03:30";
}

function getShutdownAfter() {
  return document.getElementById("shutdown-after").checked;
}

// 模式切换 - 显示/隐藏子选项
document.querySelectorAll('input[name="exec-mode"]').forEach(radio => {
  radio.addEventListener("change", () => {
    const mode = getSelectedMode();
    document.getElementById("delay-row").classList.toggle("hidden", mode !== "delay");
    document.getElementById("schedule-row").classList.toggle("hidden", mode !== "schedule");
  });
});

window.addEventListener("pywebviewready", () => {
  window.addLog("[系统] 控制台就绪。");

  document.getElementById("btn-start").addEventListener("click", async () => {
    const mode = getSelectedMode();
    const shutdown = getShutdownAfter();
    let config = { mode: mode, shutdown: shutdown };

    if (mode === "delay") {
      config.delay_minutes = getDelayMinutes();
      if (config.delay_minutes < 1) {
        window.addLog("[提示] 延迟时间不能小于 1 分钟");
        return;
      }
      window.addLog(`[设置] ${config.delay_minutes} 分钟后执行`);
    } else if (mode === "schedule") {
      config.schedule_time = getScheduleTime();
      window.addLog(`[设置] 定时 ${config.schedule_time} 执行`);
    } else {
      window.addLog("[设置] 立即执行");
    }

    if (shutdown) {
      window.addLog("[设置] 执行完毕后自动关机");
    }

    window.setButtons(true);
    window.updateCard("overall", "运行中", "请勿关闭窗口");
    window.setCardClass("overall", "state-running");

    try {
      await window.pywebview.api.start_tasks(JSON.stringify(config));
    } catch (e) {
      window.addLog(`[错误] ${e}`);
      window.setButtons(false);
    }
  });

  document.getElementById("btn-stop").addEventListener("click", async () => {
    window.addLog("[操作] 请求停止...");
    try {
      await window.pywebview.api.stop_tasks();
    } catch (e) {
      window.addLog(`[错误] ${e}`);
    }
  });
});
