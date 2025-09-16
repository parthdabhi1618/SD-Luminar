# Hephaestus - Local Run Instructions

This README covers how to run the Hephaestus Flask app locally, install dependencies, and perform a quick smoke test.

## 1) Create a virtual environment

Use Python 3.10+ (your environment shows Python 3.13).

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2) Install Python dependencies

```bash
pip install -r requirements.txt
```

If you run into issues installing some optional packages (e.g., `google-api-python-client`), you can still run the app without them — the code falls back to `pytube` for video metadata.

## 3) Environment variables

Optional environment variables:

- `YOUTUBE_API_KEY` - (optional) API key for YouTube Data API to improve metadata reliability.

You can export in your shell:

```bash
export YOUTUBE_API_KEY="your_api_key_here"
```

## 4) Run the app (development)

```bash
cd "path/to/your/project/root"
source venv/bin/activate
python app.py
```

The server will run on `http://127.0.0.1:5000` by default.

## 5) Quick smoke tests

- Open the homepage: http://127.0.0.1:5000
- Upload a small PDF via the Highlight Extractor feature and confirm preview/extraction runs.
- Test the IPYNB upload: upload a `.ipynb` file and confirm the UI shows "Processing" then becomes Ready (nbconvert must be installed).
- Video Downloader: paste a YouTube URL and click "Fetch Video" to see preview metadata. If `YOUTUBE_API_KEY` is not set the code falls back to `pytube`.

## 6) Troubleshooting

- If you see `ModuleNotFoundError` for `googleapiclient`, install the package explicitly:

```bash
pip install google-api-python-client
```

- For notebook conversion (`nbconvert`) you may need chromium. On macOS, install Chrome or Chromium and ensure `chromium` is on PATH. Alternatively, install `pyppeteer` or allow nbconvert to download Chromium.

## 7) Notes and next steps

- The YouTube downloader has a preview-first flow; downloading streams uses `pytube` which may be rate-limited for some videos.
- The highlight extractor now uses a more robust heuristic; edge cases may still exist for complex PDFs.

If you want, I can run the server here and perform a smoke test for you, or adjust any of the features further.
