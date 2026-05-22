# Hugging Face Spaces Deployment

Hugging Face Spaces is a good free host for this OCR app because Docker Spaces can run Tesseract and OpenCV inside the container.

## 1. Create A Space

1. Go to https://huggingface.co/spaces
2. Click `Create new Space`.
3. Choose a Space name, for example `trading-analyser`.
4. Select `Docker` as the SDK.
5. Choose `Public`.
6. Choose the free CPU hardware.
7. Create the Space.

## 2. Add This App To The Space

Open the Space, then use the `Files` tab to upload these files from this folder:

```text
Dockerfile
requirements.txt
web_app.py
trading_data_analyzer.py
README.md
```

You can also push by Git if you prefer:

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME
copy C:\Users\laptop\Desktop\scr\Dockerfile .
copy C:\Users\laptop\Desktop\scr\requirements.txt .
copy C:\Users\laptop\Desktop\scr\web_app.py .
copy C:\Users\laptop\Desktop\scr\trading_data_analyzer.py .
copy C:\Users\laptop\Desktop\scr\README.md .
git add .
git commit -m "Deploy trading analyzer"
git push
```

Replace `YOUR_USERNAME` and `YOUR_SPACE_NAME`.

## 3. Space Configuration

If the Space asks for config, use:

```yaml
---
title: Trading Data Analyzer
sdk: docker
app_port: 7860
---
```

The Dockerfile already exposes port `7860`.

## 4. Wait For Build

Hugging Face will build the Docker image. When it finishes, open the Space URL and upload your images.

## Notes

- Free CPU Spaces can pause after inactivity.
- First load after pause can be slow.
- OCR still takes time, but free Hugging Face CPU hardware is usually better suited to this than Render free.
- If you deploy from the GitHub repo instead, make sure Hugging Face uses the latest `Dockerfile`.

## 5. Where To See The Pipeline Logs

The app emits a step-by-step log for every uploaded file:

```
preprocess -> ocr -> table -> parse -> done
```

You can view these in two places on a deployed Space:

1. **In the page itself (per-file)**
   - Open the Space URL, upload one or more images / PDFs.
   - Under each file's result (or under the error box if it failed) you will see a
     coloured step list with the message and elapsed milliseconds for every stage.
   - This comes back inside the JSON response, so it works on any host.

2. **In the Hugging Face Space "Logs" tab (live stdout)**
   - Open your Space page.
   - Click the `Logs` tab (top of the Space, next to `App`, `Files`, `Community`,
     `Settings`). On some Space layouts it is exposed as a `Logs` button on the
     right side of the header.
   - You will see two sub-views:
     - `Build` -> shown while the Docker image is building. Useful for catching
       missing apt packages or pip install errors.
     - `Container` (sometimes labelled `App` or `Runtime`) -> the running app's
       stdout/stderr. Every step prints a line like:
       ```
       [ok] [ocr] page_1.png: OCR returned 142 words (avg conf 87, ...) (812 ms)
       [ok] [table] page_1.png: Built 17 rows from 142 words (1 ms)
       [ok] [parse] page_1.png: Tabular parser kept 6 trade(s) ... (3 ms)
       ```
   - The Dockerfile already sets `PYTHONUNBUFFERED=1`, and the app re-asserts
     line-buffered stdout on startup, so these lines appear as the work happens
     (no need to wait for the request to finish).

If your Space sleeps and then takes a while to wake up, the first request after
wake-up will show extra build/boot lines in `Container` before the pipeline
log lines start streaming.
