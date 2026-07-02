# Format Forge

Web app per convertire file tra piu formati con una GUI semplice.

## Indice

- [Formati supportati](#formati-supportati)
- [Regole conversione](#regole-conversione)
- [Avvio locale](#avvio-locale)
- [Build EXE (Windows)](#build-exe-windows)
  - [Metodo rapido](#metodo-rapido)
  - [Differenze tra i due EXE](#differenze-tra-i-due-exe)
  - [Personalizzazione icona e titolo finestra](#personalizzazione-icona-e-titolo-finestra)
  - [Avvio web opzionale](#avvio-web-opzionale)
  - [Metodo manuale](#metodo-manuale)
- [Note](#note)

## Formati supportati

| Categoria | Formati |
| --- | --- |
| Dati/testo | JSON, CSV, YAML, TOML, XML, TXT, MD |
| Audio | MP3, WAV, FLAC, AAC, OGG, M4A |
| Video | MP4, MKV, MOV, AVI, WEBM |
| Immagini | PNG, JPG / JPEG, WEBP, BMP, GIF, TIFF, ICO |

## Regole conversione

- Dati/testo: conversioni tra i formati strutturati elencati sopra.
- Media: consentite audio -> audio, video -> video e video -> audio.
- Immagini: consentite conversioni immagine -> immagine.
- Non sono consentite conversioni miste tra binary (audio/video/immagini) e testo/strutturati.

## Avvio locale

1. Crea e attiva un ambiente virtuale Python.
2. Installa le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

3. Avvia l'app:

   ```bash
   python app.py
   ```

4. Apri il browser sull'URL mostrato in console (porta auto-selezionata se 5000 non disponibile).

## Build EXE (Windows)

### Metodo rapido

Esegui:

```bat
build_exe.bat
```

Output:

- dist\\FormatForgeWeb.exe
- dist\\FormatForgeDesktop.exe

### Differenze tra i due EXE

- FormatForgeWeb.exe: avvia il server locale in background e apre il browser di sistema.
- FormatForgeDesktop.exe: avvia l'app in finestra desktop Windows (senza browser esterno).
- In FormatForgeDesktop.exe la console e integrata nell'app: pannello in basso, nascosto di default, apribile con CTRL+\\ e ridimensionabile trascinando il bordo superiore.

### Personalizzazione icona e titolo finestra

- Per usare un'icona personalizzata, aggiungi il file assets\\formatforge.ico.
- Per cambiare il titolo della finestra desktop imposta APP_WINDOW_TITLE.

```bash
set APP_WINDOW_TITLE=Format Forge Pro
FormatForgeDesktop.exe
```

### Avvio web opzionale

Puoi controllare l'apertura automatica del browser:

```bash
python app.py --open-browser
python app.py --no-open-browser
```

Oppure via variabile ambiente:

```bash
set AUTO_OPEN_BROWSER=0
python app.py
```

### Metodo manuale

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
pyinstaller --noconsole --onefile --name FormatForgeWeb --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg app.py
pyinstaller --noconsole --onefile --name FormatForgeDesktop --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg --collect-all webview desktop_app.py
```

## Note

- Il formato sorgente puo essere scelto manualmente o rilevato dall'estensione file.
- Se esporti in CSV, i dati devono rappresentare una tabella (lista di oggetti).
- Le conversioni audio/video usano FFmpeg tramite il pacchetto imageio-ffmpeg.
- La selezione formati usa due dropdown separati, uno per sorgente e uno per destinazione, con chip organizzati per tab.
- Dove finiscono i file convertiti:
   - Browser web: nella cartella Download configurata del browser (o percorso scelto dal browser).
   - Desktop app: in Downloads\\FormatForge, con pulsante Locate file? per aprire la cartella file.
