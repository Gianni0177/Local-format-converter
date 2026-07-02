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

### Immagini

- PNG
- JPG / JPEG
- WEBP
- BMP
- GIF
- TIFF
- ICO

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

### Firma del binario per ridurre SmartScreen

Per evitare o ridurre l'avviso SmartScreen in modo corretto, firma gli EXE con un certificato Authenticode.

Nel workflow GitHub Actions il supporto e attivo se imposti questi secret del repository:

- `CODE_SIGN_CERT_BASE64`: contenuto del file `.pfx` codificato in base64.
- `CODE_SIGN_CERT_PASSWORD`: password del certificato.

Con questi secret, il release workflow firma automaticamente `FormatForgeWeb.exe` e `FormatForgeDesktop.exe` prima di pubblicarli.

Anche il build locale puo firmare gli EXE se esporti le stesse variabili ambiente prima di eseguire `build_exe.bat`.

#### Procedura rapida

1. Procurati un certificato di code signing valido e esportalo in formato `.pfx` con la chiave privata inclusa.
2. Se vuoi solo provare il meccanismo in locale, puoi creare un certificato autofirmato di test, ma non eliminerai SmartScreen per una distribuzione pubblica.

Esempio con PowerShell per creare un certificato autofirmato di test:

```powershell
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Format Forge Test" -CertStoreLocation "Cert:\CurrentUser\My"
$password = Read-Host "Password per il PFX" -AsSecureString
Export-PfxCertificate -Cert $cert -FilePath .\codesign-test.pfx -Password $password
```

Per convertire il `.pfx` in base64 da usare in GitHub Secrets:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\export-codesign-base64.ps1 -PfxPath .\codesign-test.pfx -CopyToClipboard
```

Se preferisci salvare il base64 in un file di testo:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\export-codesign-base64.ps1 -PfxPath .\codesign-test.pfx -OutFile .\codesign-test.txt
```

Per preparare i secret e aprire direttamente la pagina GitHub:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\prepare-codesign-secrets.ps1 -PfxPath .\codesign-test.pfx -CopyToClipboard -OpenSecretsPage
```

Lo script mostra anche l'URL della pagina secret del repository, utile se vuoi incollare il base64 manualmente.

3. In GitHub vai in `Settings` > `Secrets and variables` > `Actions` e crea questi secret:

1. `CODE_SIGN_CERT_BASE64` con il contenuto base64 del file `.pfx`
2. `CODE_SIGN_CERT_PASSWORD` con la password del PFX

4. Se vuoi fare una prova locale, puoi impostare le stesse variabili ambiente prima di eseguire il batch:

```bat
set CODE_SIGN_CERT_BASE64=...
set CODE_SIGN_CERT_PASSWORD=...
build_exe.bat
```

5. Quando fai un tag di release, il workflow usera automaticamente quei secret per firmare `FormatForgeWeb.exe` e `FormatForgeDesktop.exe` prima della pubblicazione.

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
