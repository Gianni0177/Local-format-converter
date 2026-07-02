# Format Forge

Web app per convertire file tra piu formati con una GUI semplice.

## Formati supportati

### Dati/testo

- JSON
- CSV
- YAML
- TOML
- XML
- TXT
- MD

### Audio

- MP3
- WAV
- FLAC
- AAC
- OGG
- M4A

### Video

- MP4
- MKV
- MOV
- AVI
- WEBM

## Regole conversione

- Dati/testo: conversioni tra i formati strutturati elencati sopra.
- Media: consentite audio -> audio, video -> video e video -> audio.
- Non sono consentite conversioni miste tra media e testo/strutturati.

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

- dist\\FormatForge.exe
- L'exe apre automaticamente il browser sulla pagina dell'app.
- L'exe non mostra la console (build GUI).

### Metodo manuale

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
pyinstaller --noconsole --onefile --name FormatForge --add-data "templates;templates" --add-data "static;static" --collect-all imageio_ffmpeg app.py
```

## Note

- Il formato sorgente puo essere scelto manualmente o rilevato dall'estensione file.
- Se esporti in CSV, i dati devono rappresentare una tabella (lista di oggetti).
- Le conversioni audio/video usano FFmpeg tramite il pacchetto imageio-ffmpeg.
