const form = document.getElementById("convert-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const consoleDrawer = document.getElementById("console-drawer");
const consoleOutput = document.getElementById("console-output");
const consoleResizer = document.getElementById("console-resizer");
const consoleClear = document.getElementById("console-clear");
const isDesktopMode = document.body.dataset.desktop === "1";

let logCursor = 0;
let consoleOpen = false;
let drawerHeight = 220;

function addConsoleLine(level, message, timestamp = null) {
  if (!isDesktopMode || !consoleOutput) return;
  const line = document.createElement("p");
  line.className = `console-line ${level || "info"}`;
  const hhmmss = timestamp || new Date().toLocaleTimeString("it-IT", { hour12: false });
  line.textContent = `[${hhmmss}] ${String(message)}`;
  consoleOutput.appendChild(line);
  while (consoleOutput.childElementCount > 600) {
    consoleOutput.firstElementChild.remove();
  }
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

function setConsoleOpen(open) {
  if (!isDesktopMode || !consoleDrawer) return;
  consoleOpen = open;
  consoleDrawer.classList.toggle("open", open);
  consoleDrawer.setAttribute("aria-hidden", open ? "false" : "true");
}

function toggleConsoleDrawer() {
  setConsoleOpen(!consoleOpen);
}

function applyDrawerHeight(height) {
  drawerHeight = Math.max(120, Math.min(height, Math.floor(window.innerHeight * 0.72)));
  document.documentElement.style.setProperty("--console-height", `${drawerHeight}px`);
}

async function pullServerLogs() {
  if (!isDesktopMode) return;
  try {
    const response = await fetch(`/api/logs?since=${logCursor}`);
    if (!response.ok) return;
    const payload = await response.json();
    const logs = payload.logs || [];
    for (const entry of logs) {
      logCursor = Math.max(logCursor, Number(entry.id || 0));
      addConsoleLine(entry.level || "info", entry.message || "", entry.timestamp || null);
    }
  } catch {
    // Console drawer should stay non-intrusive.
  }
}

function setupIntegratedConsole() {
  if (!isDesktopMode || !consoleDrawer || !consoleResizer || !consoleClear) return;

  applyDrawerHeight(drawerHeight);
  setConsoleOpen(false);

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "\\") {
      event.preventDefault();
      toggleConsoleDrawer();
    }
  });

  consoleClear.addEventListener("click", () => {
    consoleOutput.innerHTML = "";
    addConsoleLine("info", "Console pulita");
  });

  let dragging = false;
  let startY = 0;
  let startHeight = drawerHeight;

  consoleResizer.addEventListener("mousedown", (event) => {
    dragging = true;
    startY = event.clientY;
    startHeight = drawerHeight;
    document.body.style.userSelect = "none";
  });

  window.addEventListener("mousemove", (event) => {
    if (!dragging) return;
    const delta = startY - event.clientY;
    applyDrawerHeight(startHeight + delta);
  });

  window.addEventListener("mouseup", () => {
    dragging = false;
    document.body.style.userSelect = "";
  });

  addConsoleLine("info", "Console integrata pronta (Ctrl+\\)");
  pullServerLogs();
  setInterval(pullServerLogs, 1200);
}

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`.trim();
  if (isDesktopMode) {
    addConsoleLine(kind || "info", message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const file = data.get("file");

  if (!file || !file.name) {
    setStatus("Seleziona un file prima di convertire.", "error");
    return;
  }

  submitBtn.disabled = true;
  setStatus("Conversione in corso...", "");

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      body: data,
    });

    if (!response.ok) {
      let errText = "Conversione non riuscita";
      try {
        const payload = await response.json();
        if (payload.error) errText = payload.error;
      } catch {
        // Keep fallback message.
      }
      throw new Error(errText);
    }

    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^\";]+)"?/i);
    const filename = match ? match[1] : "converted_file";

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    setStatus("Conversione completata. Download avviato.", "ok");
  } catch (error) {
    setStatus(error.message || "Errore inatteso", "error");
  } finally {
    submitBtn.disabled = false;
  }
});

setupIntegratedConsole();
