# Trading Data Analyzer - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Tesseract OCR (First Time Only)

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Run the installer
- Restart your terminal

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or run the setup script:
```bash
python setup.py
```

### 3. Run the Analyzer

```bash
python trading_data_analyzer.py
```

## 📋 Usage

1. Start the script: `python trading_data_analyzer.py`
2. Enter your image file paths when prompted
3. Press Enter twice to finish
4. Wait for analysis to complete
5. Excel file is generated with results

## 📊 Output Files

The script generates an Excel file named:
```
trading_analysis_YYYYMMDD_HHMMSS.xlsx
```

Contains:
- ✅ Summary sheet with overall totals
- ✅ Detail sheets for each document
- ✅ Calculated values (Qty÷250 × Rate)
- ✅ BUY and SELL groupings

## 📸 Image Requirements

- **Format**: JPG, PNG, JPEG, TIFF
- **Quality**: Clear and legible text
- **Resolution**: 300+ DPI recommended
- **Content**: Trading table with BUY/SELL, Quantity, Rate

## ⚡ Quick Example

```
Input Images:
- trading_doc_1.jpg
- trading_doc_2.jpg

Output:
trading_analysis_20260522_150000.xlsx
├── Summary (Overall totals)
├── trading_doc_1 (Detail sheet 1)
└── trading_doc_2 (Detail sheet 2)
```

## 🔧 Troubleshooting

**Script won't start:**
```bash
python setup.py
```

**OCR not working:**
- Tesseract not installed? Install it from the link above
- Image quality too low? Use clearer images

**No trades extracted:**
- Check image clarity
- Make sure image has trading table data
- Verify text is readable

## 📞 Need Help?

1. Run setup script: `python setup.py`
2. Check README.md for detailed instructions
3. Verify Tesseract is installed
4. Try with a test image of good quality

## 💡 Tips

- Use high-quality, clear images
- Good lighting prevents OCR errors
- Properly aligned images work best
- Process multiple documents at once
- Check the Excel output format

## 📁 Files Included

```
├── trading_data_analyzer.py   ← Main script (run this)
├── setup.py                   ← Setup helper
├── requirements.txt           ← Python dependencies
├── README.md                  ← Full documentation
└── QUICKSTART.md             ← This file
```

---

**Version**: 1.0  
**Last Updated**: 2026-05-22

Ready to go! Run: `python trading_data_analyzer.py`
