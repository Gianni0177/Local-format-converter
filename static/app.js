const form = document.getElementById("convert-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const fileInput = document.getElementById("file-input");
const sourceFormatInput = document.getElementById("source-format");
const targetFormatInput = document.getElementById("target-format");
const sourcePickers = Array.from(document.querySelectorAll('input[name="source-pick"]'));
const targetPickers = Array.from(document.querySelectorAll('input[name="target-pick"]'));
const afterDownloadBox = document.getElementById("after-download");
const locateBtn = document.getElementById("locate-btn");
const downloadNote = document.getElementById("download-note");
const consoleDrawer = document.getElementById("console-drawer");
const consoleOutput = document.getElementById("console-output");
const consoleResizer = document.getElementById("console-resizer");
const consoleClear = document.getElementById("console-clear");
const isDesktopMode = document.body.dataset.desktop === "1";

let logCursor = 0;
let consoleOpen = false;
let drawerHeight = 220;
let lastSavedPath = "";

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

function setDownloadNote(message) {
  if (!downloadNote) return;
  downloadNote.textContent = message;
}

function resetAfterDownload() {
  lastSavedPath = "";
  if (!afterDownloadBox || !locateBtn) return;
  afterDownloadBox.classList.add("hidden");
  locateBtn.disabled = true;
  setDownloadNote("");
}

function showAfterDownload(canLocate, note) {
  if (!afterDownloadBox || !locateBtn) return;
  afterDownloadBox.classList.remove("hidden");
  locateBtn.disabled = !canLocate;
  setDownloadNote(note);
}

function selectRadioByValue(radios, value) {
  const normalized = String(value || "").toLowerCase();
  let found = false;
  for (const radio of radios) {
    const match = radio.value.toLowerCase() === normalized;
    radio.checked = match;
    if (match) found = true;
  }
  return found;
}

function updateHiddenFormats() {
  const sourceSelected = sourcePickers.find((radio) => radio.checked);
  const targetSelected = targetPickers.find((radio) => radio.checked);
  sourceFormatInput.value = sourceSelected ? sourceSelected.value : "auto";
  targetFormatInput.value = targetSelected ? targetSelected.value : "";
}

function detectExtFromFilename(name) {
  const parts = String(name || "").toLowerCase().split(".");
  if (parts.length < 2) return "";
  return parts.pop();
}

async function blobToBase64(blob) {
  const buffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function readDownloadNameFromHeaders(response) {
  const disposition = response.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : "converted_file";
}

async function saveViaDesktopBridge(blob, filename) {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.save_converted_file) {
    return "";
  }
  const payload = await blobToBase64(blob);
  const path = await window.pywebview.api.save_converted_file(payload, filename);
  return String(path || "");
}

function saveViaBrowserDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

for (const picker of sourcePickers) {
  picker.addEventListener("change", updateHiddenFormats);
}
for (const picker of targetPickers) {
  picker.addEventListener("change", updateHiddenFormats);
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  const ext = detectExtFromFilename(file.name);
  if (!ext) return;
  if (selectRadioByValue(sourcePickers, ext)) {
    updateHiddenFormats();
  }
});

locateBtn?.addEventListener("click", async () => {
  if (!lastSavedPath) return;
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.locate_file) {
    setStatus("Funzione Locate non disponibile in modalita browser.", "error");
    return;
  }
  const ok = await window.pywebview.api.locate_file(lastSavedPath);
  if (!ok) {
    setStatus("Impossibile aprire la cartella del file.", "error");
  }
});

updateHiddenFormats();
resetAfterDownload();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const file = data.get("file");

  if (!file || !file.name) {
    setStatus("Seleziona un file prima di convertire.", "error");
    return;
  }

  if (!targetFormatInput.value) {
    setStatus("Seleziona il formato destinazione nella tabella.", "error");
    return;
  }

  submitBtn.disabled = true;
  resetAfterDownload();
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
    const filename = readDownloadNameFromHeaders(response);
    const runningInDesktopBridge = Boolean(
      isDesktopMode && window.pywebview && window.pywebview.api && window.pywebview.api.save_converted_file,
    );

    if (runningInDesktopBridge) {
      lastSavedPath = await saveViaDesktopBridge(blob, filename);
      setStatus("Conversione completata. File salvato in Downloads/FormatForge.", "ok");
      showAfterDownload(Boolean(lastSavedPath), lastSavedPath || "File salvato.");
    } else {
      saveViaBrowserDownload(blob, filename);
      setStatus("Conversione completata. Download avviato.", "ok");
      showAfterDownload(
        false,
        "Nel browser i file vengono salvati nella cartella download configurata (o scelta manualmente).",
      );
    }
  } catch (error) {
    setStatus(error.message || "Errore inatteso", "error");
  } finally {
    submitBtn.disabled = false;
  }
});

setupIntegratedConsole();
