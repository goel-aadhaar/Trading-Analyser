---
title: Trading Data Analyzer
sdk: docker
app_port: 7860
---

# Trading Data Analyzer - OCR Version

A Python tool that extracts trading data from images using OCR (Optical Character Recognition), performs calculations, and generates professional Excel reports.

## Features

✅ **Image OCR**: Automatically extracts trading data from JPG, PNG, JPEG, TIFF images  
✅ **Data Calculation**: Computes `(Quantity ÷ 250) × Market Rate` for all trades  
✅ **Group Analysis**: Separates and sums BUY and SELL transactions  
✅ **Excel Reports**: Generates formatted Excel files with detailed analysis  
✅ **Multiple Documents**: Processes multiple images and creates individual sheets  
✅ **Professional Output**: Color-coded summaries with borders and formatting  

## Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pytesseract pillow openpyxl opencv-python
```

### Step 2: Install Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (default location: `C:\Program Files\Tesseract-OCR`)
3. If installed in non-default location, update the script:
   ```python
   pytesseract.pytesseract.pytesseract_cmd = r'C:\path\to\tesseract.exe'
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (Fedora/RedHat):**
```bash
sudo yum install tesseract
```

## Usage

### Method 1: Interactive Mode (Recommended)

Simply run the script and follow the prompts:

```bash
python trading_data_analyzer.py
```

The script will:
1. Ask you to input image file paths
2. Process each image and extract trading data
3. Generate an Excel file with analysis
4. Display summary statistics

Example:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     TRADING DATA ANALYSIS TOOL - OCR VERSION                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Enter image file paths (one per line, press Enter twice to finish):
(Supported formats: JPG, PNG, JPEG, TIFF)

Image 1: /path/to/image1.jpg
Image 2: /path/to/image2.jpg
Image 3: 

============================================================
TRADING DATA EXTRACTION
============================================================
Processing: /path/to/image1.jpg
  ✓ Found 28 trades
Processing: /path/to/image2.jpg
  ✓ Found 26 trades

✓ Total trades extracted: 54

============================================================
GENERATING EXCEL REPORT
============================================================

✓ Excel report generated: trading_analysis_20240522_145030.xlsx

============================================================
ANALYSIS SUMMARY
============================================================
BUY Total:  118.4000
SELL Total: 181.6000
NET (BUY - SELL): -63.2000
============================================================

✓ Analysis complete! File saved as: trading_analysis_20240522_145030.xlsx
```

### Method 2: Batch Processing (Advanced)

Modify the script to process a folder of images:

```python
from pathlib import Path
from trading_data_analyzer import TradingDataExtractor

# Create extractor
extractor = TradingDataExtractor()

# Process all JPG files in a folder
image_folder = Path("./trading_images")
image_paths = list(image_folder.glob("*.jpg")) + list(image_folder.glob("*.png"))

# Process images
if extractor.process_images(image_paths):
    extractor.generate_excel("batch_analysis.xlsx")
```

## How It Works

### 1. Image Processing
- Converts image to grayscale
- Applies thresholding for better contrast
- Denoises the image for cleaner text

### 2. Text Extraction (OCR)
- Uses Tesseract to recognize text in images
- Extracts trading records (BUY/SELL, Quantity, Rate)

### 3. Data Parsing
- Identifies BUY and SELL transactions
- Extracts quantities and market rates
- Validates data for accuracy

### 4. Calculation
- Applies formula: `(Quantity ÷ 250) × Market Rate`
- Groups transactions by type (BUY/SELL)
- Calculates totals and net values

### 5. Excel Generation
- Creates summary sheet with overall totals
- Creates individual sheets for each document
- Applies professional formatting and styling

## Output

The script generates an Excel file with:

**Summary Sheet:**
- Overall BUY total
- Overall SELL total
- NET (BUY - SELL) calculation
- Transaction counts

**Detail Sheets (one per document):**
- All transactions with calculated values
- Document-specific summaries
- BUY and SELL subtotals

## Supported Image Formats

- ✅ JPG / JPEG
- ✅ PNG
- ✅ TIFF / TIF
- ✅ BMP

## Tips for Best Results

1. **Image Quality**: Use clear, high-resolution images (300+ DPI recommended)
2. **Lighting**: Ensure good lighting - avoid shadows and glare
3. **Orientation**: Images should be upright and properly aligned
4. **Contrast**: High contrast between text and background works best
5. **Resolution**: Larger images generally produce better OCR results

## Troubleshooting

**"Tesseract is not installed" error:**
- Make sure Tesseract OCR is installed (see Installation Step 2)
- Windows users: Verify the installation path

**"No trades extracted" error:**
- Check image quality and clarity
- Ensure the image contains clear trading table data
- Try preprocessing the image in an image editor first

**"Could not read image" error:**
- Verify the file path is correct
- Check that the image file is not corrupted
- Supported formats are JPG, PNG, JPEG, TIFF

**Inaccurate data extraction:**
- Improve image quality and resolution
- Ensure proper lighting and contrast
- Try different image preprocessing techniques

## Example Output

### Summary Sheet Output:
```
TRADING ANALYSIS SUMMARY

OVERALL TOTALS
Type        Total Value    Count
BUY         118.4000       30
SELL        181.6000       28
NET         -63.2000
```

### Calculation Examples:
- BUY 250 @ 2.75 → (250÷250) × 2.75 = 2.75
- SELL 500 @ 3.30 → (500÷250) × 3.30 = 6.60
- BUY 1000 @ 2.35 → (1000÷250) × 2.35 = 9.40

## Performance

- **Single image**: ~2-5 seconds
- **10 images**: ~20-50 seconds
- **Processing time** depends on image resolution and system performance

## Advanced Usage

### Custom Image Processing

Modify preprocessing parameters in the script:

```python
def preprocess_image(self, image_path):
    # Adjust threshold value (150 by default)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Adjust denoising strength (h=10 by default)
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
```

### Custom Output Path

```python
extractor.generate_excel("/custom/path/output.xlsx")
```

## License

This script is provided as-is for personal and commercial use.

## Support

For issues or improvements, check:
- Tesseract documentation: https://github.com/tesseract-ocr/tesseract
- OpenPyXL documentation: https://openpyxl.readthedocs.io/
- Python OCR guides: https://realpython.com/pytesseract-ocr-python/

---

**Version**: 1.0  
**Last Updated**: 2026-05-22  
**Python Version**: 3.7+
