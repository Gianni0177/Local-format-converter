<div align="center">

# 🔨 Format Forge

**Converti file tra decine di formati — direttamente dal browser o come app desktop Windows.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-web%20app-lightgrey?logo=flask)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Web-informational)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 📋 Indice

- [📦 Formati supportati](#-formati-supportati)
- [📐 Regole conversione](#-regole-conversione)
- [🚀 Avvio locale](#-avvio-locale)
- [🖥️ Build EXE (Windows)](#%EF%B8%8F-build-exe-windows)
  - [⚡ Metodo rapido](#-metodo-rapido)
  - [🔍 Differenze tra i due EXE](#-differenze-tra-i-due-exe)
  - [🎨 Personalizzazione icona e titolo finestra](#-personalizzazione-icona-e-titolo-finestra)
  - [🌐 Avvio web opzionale](#-avvio-web-opzionale)
  - [🔧 Metodo manuale](#-metodo-manuale)
- [📝 Note](#-note)

---

## 📦 Formati supportati

| Categoria | Formati |
|:---------:|:--------|
| 🗂️ **Dati/testo** | `JSON` `CSV` `YAML` `TOML` `XML` `TXT` `MD` |
| 🎵 **Audio** | `MP3` `WAV` `FLAC` `AAC` `OGG` `M4A` |
| 🎬 **Video** | `MP4` `MKV` `MOV` `AVI` `WEBM` |
| 🖼️ **Immagini** | `PNG` `JPG/JPEG` `WEBP` `BMP` `GIF` `TIFF` `ICO` |

---

## 📐 Regole conversione

| Tipo | Conversioni consentite |
|:----:|:----------------------|
| 🗂️ Dati/testo | Qualsiasi formato strutturato → qualsiasi altro |
| 🎵 Audio | Audio → Audio |
| 🎬 Video | Video → Video &nbsp;·&nbsp; Video → Audio |
| 🖼️ Immagini | Immagine → Immagine |
| ❌ Non consentito | Binario (audio/video/immagini) ↔ Testo/strutturati |

---

## 🚀 Avvio locale

**1.** Crea e attiva un ambiente virtuale Python:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux
```

**2.** Installa le dipendenze:

```bash
pip install -r requirements.txt
```

**3.** Avvia l'app:

```bash
python app.py
```

**4.** Apri il browser all'URL mostrato in console.
> 💡 La porta viene auto-selezionata se la 5000 è già occupata.

---

## 🖥️ Build EXE (Windows)

### ⚡ Metodo rapido

```bat
build_exe.bat
```

Al termine troverai nella cartella `dist\`:

| File | Descrizione |
|------|-------------|
| `FormatForgeWeb.exe` | Avvia il server locale e apre il browser di sistema |
| `FormatForgeDesktop.exe` | Avvia l'app in finestra desktop nativa (senza browser esterno) |

---

### 🔍 Differenze tra i due EXE

- **`FormatForgeWeb.exe`** — avvia un server locale in background e apre il browser di sistema.
- **`FormatForgeDesktop.exe`** — l'app gira in una finestra desktop Windows autonoma.
  - La console è integrata nell'app: pannello in basso, nascosto di default.
  - Apribile con <kbd>CTRL</kbd>+<kbd>\\</kbd> e ridimensionabile trascinando il bordo superiore.

---

### 🎨 Personalizzazione icona e titolo finestra

- Per usare un'icona personalizzata, aggiungi il file `assets\formatforge.ico`.
- Per cambiare il titolo della finestra desktop, imposta la variabile `APP_WINDOW_TITLE`:

```bat
set APP_WINDOW_TITLE=Format Forge Pro
FormatForgeDesktop.exe
```

---

### 🌐 Avvio web opzionale

Controlla l'apertura automatica del browser tramite flag:

```bash
python app.py --open-browser
python app.py --no-open-browser
```

Oppure tramite variabile d'ambiente:

```bash
set AUTO_OPEN_BROWSER=0
python app.py
```

---

### 🔧 Metodo manuale

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# EXE Web
pyinstaller --noconsole --onefile --name FormatForgeWeb \
  --add-data "templates;templates" \
  --add-data "static;static" \
  --collect-all imageio_ffmpeg \
  app.py

# EXE Desktop
pyinstaller --noconsole --onefile --name FormatForgeDesktop \
  --add-data "templates;templates" \
  --add-data "static;static" \
  --collect-all imageio_ffmpeg \
  --collect-all webview \
  desktop_app.py
```

---

## 📝 Note

> - 🔎 Il formato sorgente può essere scelto manualmente o rilevato automaticamente dall'estensione file.
> - 📊 Se esporti in CSV, i dati devono rappresentare una tabella (lista di oggetti).
> - 🎞️ Le conversioni audio/video usano **FFmpeg** tramite il pacchetto `imageio-ffmpeg`.
> - 🗂️ La selezione formati usa due dropdown separati (sorgente e destinazione) con chip organizzati per tab.

### 📁 Dove finiscono i file convertiti?

| Modalità | Percorso |
|----------|---------|
| 🌐 **Browser web** | Cartella `Download` configurata nel browser |
| 🖥️ **Desktop app** | `Downloads\FormatForge` — con pulsante **Locate file?** per aprire la cartella |

---

<div align="center">
  <sub>Made with ❤️ using Python & Flask</sub>
</div>
