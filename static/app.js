const form = document.getElementById("convert-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const fileInput = document.getElementById("file-input");
const sourceFormatInput = document.getElementById("source-format");
const targetFormatInput = document.getElementById("target-format");
const sourceToggle = document.getElementById("source-format-toggle");
const targetToggle = document.getElementById("target-format-toggle");
const sourcePanel = document.getElementById("source-format-panel");
const targetPanel = document.getElementById("target-format-panel");
const sourceList = document.getElementById("source-format-list");
const targetList = document.getElementById("target-format-list");
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
let selectedSourceFormat = "auto";
let selectedTargetFormat = "";
let openPickerRole = null;
let activeTabs = {
  source: "data",
  target: "data",
};

const formatCatalog = {
  data: ["json", "csv", "yaml", "toml", "xml", "txt", "md"],
  image: ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"],
  media: {
    audio: ["mp3", "wav", "flac", "aac", "ogg", "m4a"],
    video: ["mp4", "mkv", "mov", "avi", "webm"],
  },
};

const formatToCategory = new Map();
for (const format of formatCatalog.data) formatToCategory.set(format, "data");
for (const format of formatCatalog.image) formatToCategory.set(format, "image");
for (const format of formatCatalog.media.audio) formatToCategory.set(format, "media");
for (const format of formatCatalog.media.video) formatToCategory.set(format, "media");

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
    // non intrusivo
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toggleText(role) {
  if (role === "source") {
    return selectedSourceFormat === "auto"
      ? "Sorgente: Auto"
      : `Sorgente: ${selectedSourceFormat.toUpperCase()}`;
  }
  return selectedTargetFormat ? `Destinazione: ${selectedTargetFormat.toUpperCase()}` : "Destinazione: scegli formato";
}

function openPicker(role, open) {
  const panel = role === "source" ? sourcePanel : targetPanel;
  const toggle = role === "source" ? sourceToggle : targetToggle;
  const otherRole = role === "source" ? "target" : "source";
  const otherPanel = otherRole === "source" ? sourcePanel : targetPanel;
  const otherToggle = otherRole === "source" ? sourceToggle : targetToggle;

  if (!panel || !toggle) return;

  if (open) {
    otherPanel?.classList.add("hidden");
    otherToggle?.setAttribute("aria-expanded", "false");
    if (openPickerRole && openPickerRole !== role) {
      renderPicker(openPickerRole);
    }
    openPickerRole = role;
  } else if (openPickerRole === role) {
    openPickerRole = null;
  }

  panel.classList.toggle("hidden", !open);
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
}

function renderChip(value, label, role) {
  const selected = role === "source" ? selectedSourceFormat === value : selectedTargetFormat === value;
  return `
    <button type="button" class="format-chip${selected ? " selected" : ""}" data-role="${role}" data-value="${escapeHtml(value)}">
      ${escapeHtml(label)}
    </button>
  `;
}

function renderGroup(title, values, role) {
  const chips = values.map((value) => renderChip(value, value.toUpperCase(), role)).join("");
  return `
    <section class="format-chip-group">
      <div class="format-chip-group-title">${escapeHtml(title)}</div>
      <div class="format-chip-grid">${chips}</div>
    </section>
  `;
}

function renderPicker(role) {
  const panel = role === "source" ? sourcePanel : targetPanel;
  const list = role === "source" ? sourceList : targetList;
  if (!panel || !list) return;

  const tab = activeTabs[role] || "data";
  const body = [];

  if (role === "source") {
    body.push(`
      <div class="format-chip-group">
        <div class="format-chip-group-title">Auto rilevamento</div>
        <div class="format-chip-grid">${renderChip("auto", "Auto", role)}</div>
      </div>
    `);
  }

  if (tab === "data") {
    body.push(renderGroup("Dati e Testo", formatCatalog.data, role));
  } else if (tab === "image") {
    body.push(renderGroup("Immagini", formatCatalog.image, role));
  } else if (tab === "media") {
    body.push(renderGroup("Audio", formatCatalog.media.audio, role));
    body.push(renderGroup("Video", formatCatalog.media.video, role));
  }

  list.innerHTML = body.join("");

  for (const chip of list.querySelectorAll(".format-chip")) {
    chip.addEventListener("click", () => {
      const value = chip.dataset.value;
      if (role === "source") {
        selectedSourceFormat = value;
        sourceFormatInput.value = value;
      } else {
        selectedTargetFormat = value;
        targetFormatInput.value = value;
      }
      renderPicker(role);
      updatePickerButton(role);
      if (role === "source" && value !== "auto") {
        const category = formatToCategory.get(value);
        if (category) {
          activeTabs.source = category;
        }
      }
      openPicker(role, false);
    });
  }

  updatePickerButton(role);
}

function updatePickerButton(role) {
  const toggle = role === "source" ? sourceToggle : targetToggle;
  if (!toggle) return;
  toggle.textContent = toggleText(role);
}

function setActiveTab(role, tab) {
  activeTabs[role] = tab;
  const tabs = Array.from(document.querySelectorAll(`.format-tab[data-role="${role}"]`));
  for (const button of tabs) {
    const isActive = button.dataset.tab === tab;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  }
  renderPicker(role);
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

function initialSyncFromFileName() {
  const file = fileInput.files?.[0];
  if (!file) return;
  const ext = detectExtFromFilename(file.name);
  if (!ext) return;
  if (formatToCategory.has(ext)) {
    activeTabs.source = formatToCategory.get(ext);
    setActiveTab("source", activeTabs.source);
  }
}

sourceToggle?.addEventListener("click", () => openPicker("source", sourcePanel?.classList.contains("hidden") ?? true));
targetToggle?.addEventListener("click", () => openPicker("target", targetPanel?.classList.contains("hidden") ?? true));

for (const tabButton of document.querySelectorAll('.format-tab[data-role="source"]')) {
  tabButton.addEventListener("click", () => setActiveTab("source", tabButton.dataset.tab));
}
for (const tabButton of document.querySelectorAll('.format-tab[data-role="target"]')) {
  tabButton.addEventListener("click", () => setActiveTab("target", tabButton.dataset.tab));
}

fileInput.addEventListener("change", () => {
  initialSyncFromFileName();
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

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const clickedInside = target.closest(".format-picker");
  if (!clickedInside) {
    openPicker("source", false);
    openPicker("target", false);
  }
});

updatePickerButton("source");
updatePickerButton("target");
renderPicker("source");
renderPicker("target");
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
    setStatus("Seleziona il formato destinazione nel dropdown.", "error");
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
        // keep fallback message
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
