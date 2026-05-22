# Deployment

The easiest reliable deployment is Docker because this app needs both Python packages and the Tesseract OCR system package.

## Local Docker Test

Build the image:

```bash
docker build -t trading-data-analyzer .
```

Run it:

```bash
docker run --rm -p 5000:5000 trading-data-analyzer
```

Open:

```text
http://127.0.0.1:5000
```

## Deploy To A Cloud Host

Use any host that supports Docker web services, such as Render, Railway, Fly.io, DigitalOcean App Platform, AWS, Azure, or a VPS.

General steps:

1. Push this folder to a GitHub repository.
2. Create a new web service on your host.
3. Choose Docker as the environment/runtime.
4. Set the service port to `5000` if the platform asks.
5. Deploy.

The Docker image installs:

- Python dependencies from `requirements.txt`
- Tesseract OCR
- Linux libraries needed by OpenCV

## Production Command

The Dockerfile starts the app with:

```bash
gunicorn --bind 0.0.0.0:${PORT:-5000} web_app:app
```

Most hosting platforms set `PORT` automatically.

## Important

Do not use `python web_app.py` for production hosting. That is fine for laptop/mobile testing, but deployment should use Gunicorn through Docker.
