const form = document.getElementById("convert-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`.trim();
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
