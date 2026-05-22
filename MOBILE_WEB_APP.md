# Mobile Web App

This project can run on your computer and be used from your phone browser.

## Start the app

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the web app:

```bash
python web_app.py
```

On the computer, open:

```text
http://127.0.0.1:5000
```

## Open from your phone

Keep the app running on your computer. Make sure your phone and computer are on the same Wi-Fi network.

Find your computer IP address:

```powershell
ipconfig
```

Look for the IPv4 address under your Wi-Fi adapter, then open this on your phone:

```text
http://YOUR_COMPUTER_IP:5000
```

Example:

```text
http://192.168.1.25:5000
```

## Use it

1. Select one or more trading images from your phone.
2. Tap `Generate Excel Report`.
3. Download the generated `.xlsx` file.

Tesseract OCR still needs to be installed on the computer running the app.
