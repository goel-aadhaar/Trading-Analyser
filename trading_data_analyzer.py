#!/usr/bin/env python3
"""
Trading Data Analysis Tool
Extracts trading data from images using OCR, performs calculations, and generates Excel reports.

Requirements:
pip install pytesseract pillow openpyxl opencv-python

Also requires Tesseract OCR to be installed:
- Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- macOS: brew install tesseract
- Linux: sudo apt-get install tesseract-ocr
"""

import os
import sys
import re
from pathlib import Path
from PIL import Image
import cv2
import pytesseract
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

MAX_OCR_IMAGE_DIMENSION = int(os.environ.get("MAX_OCR_IMAGE_DIMENSION", "3200"))
OCR_TIMEOUT_SECONDS = int(os.environ.get("OCR_TIMEOUT_SECONDS", "60"))

# Configure Tesseract path for Windows
if sys.platform == 'win32':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class TradingDataExtractor:
    def __init__(self):
        self.trading_data = []
        self.documents = {}
        
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR accuracy"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                print(f"  ✗ Could not read image: {image_path}")
                print(f"    (Verify file path with spaces/parentheses is valid)")
                print(f"    (Verify file format is supported: jpg, png, jpeg, tiff)")
                raise ValueError(f"Could not read image: {image_path}")

            height, width = img.shape[:2]
            largest_dimension = max(width, height)
            if largest_dimension > MAX_OCR_IMAGE_DIMENSION:
                scale = MAX_OCR_IMAGE_DIMENSION / largest_dimension
                new_size = (int(width * scale), int(height * scale))
                img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale - works best with Tesseract config
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            return gray
        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            processed_img = self.preprocess_image(image_path)
            if processed_img is None:
                return None
            
            # Convert numpy array to PIL Image for pytesseract
            pil_img = Image.fromarray(processed_img)
            
            # Use optimized Tesseract config for trading data
            # --oem 3: Legacy + LSTM
            # --psm 6: Block of text
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(
                pil_img,
                config=custom_config,
                timeout=OCR_TIMEOUT_SECONDS,
            )
            return text
        except FileNotFoundError as e:
            print(f"Error: Could not find Tesseract. Please install it:")
            print(f"  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"  macOS: brew install tesseract")
            print(f"  Linux: sudo apt-get install tesseract-ocr")
            return None
        except Exception as e:
            print(f"Error extracting text from {image_path}: {e}")
            return None
    
    def parse_trading_data(self, text):
        """Parse trading data from extracted text"""
        if not text:
            return []
        
        trades = []
        lines = text.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line:
                continue
            
            # Look for lines containing BUY or SELL
            if 'BUY' in line.upper() or 'SELL' in line.upper():
                # Extract direction
                direction = 'BUY' if 'BUY' in line.upper() else 'SELL'
                
                # Try to extract numbers from this line
                numbers = re.findall(r'\d+\.?\d*', line)
                
                if len(numbers) >= 2:
                    try:
                        quantity = int(float(numbers[0]))
                        market_rate = float(numbers[1])
                        
                        if quantity > 0 and market_rate > 0:
                            trades.append({
                                'direction': direction,
                                'quantity': quantity,
                                'rate': market_rate
                            })
                    except (ValueError, IndexError):
                        pass
            
            # Alternative format: Look for lines that are just numbers (rates/quantities)
            # and lines with BUY/SELL separated
            elif re.match(r'^[\d\s]+$', line.replace('.', '')):
                # This line contains numbers - check if previous line had BUY/SELL
                if i >= 2:
                    prev_line = lines[i-2].upper()
                    if 'BUY' in prev_line or 'SELL' in prev_line:
                        direction = 'BUY' if 'BUY' in prev_line else 'SELL'
                        numbers = re.findall(r'\d+\.?\d*', line)
                        
                        if len(numbers) >= 2:
                            try:
                                quantity = int(float(numbers[0]))
                                market_rate = float(numbers[1])
                                
                                if quantity > 0 and market_rate > 0:
                                    trades.append({
                                        'direction': direction,
                                        'quantity': quantity,
                                        'rate': market_rate
                                    })
                            except (ValueError, IndexError):
                                pass
        
        return trades
    
    def process_image(self, image_path):
        """Process a single image and extract trading data"""
        print(f"Processing: {image_path}")
        
        text = self.extract_text_from_image(image_path)
        if not text:
            print(f"  ⚠ Could not extract text from image")
            return 0
        
        trades = self.parse_trading_data(text)
        if not trades:
            print(f"  ⚠ Could not parse trading data from text")
            return 0
        
        print(f"  ✓ Found {len(trades)} trades")
        
        # Store trades with document info
        doc_name = Path(image_path).stem
        self.documents[doc_name] = trades
        self.trading_data.extend(trades)
        
        return len(trades)
    
    def process_images(self, image_paths):
        """Process multiple images"""
        print("=" * 60)
        print("TRADING DATA EXTRACTION")
        print("=" * 60)
        
        total_trades = 0
        for image_path in image_paths:
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            if not image_path.exists():
                print(f"⚠ File not found: {image_path}")
                print(f"  (Check that spaces and special characters are correct)")
                continue
            
            if not image_path.is_file():
                print(f"⚠ Not a file: {image_path}")
                continue
            
            trades = self.process_image(image_path)
            total_trades += trades
        
        print(f"\n✓ Total trades extracted: {total_trades}")
        return total_trades > 0
    
    def calculate_values(self):
        """Calculate (Quantity/250) * Rate for all trades"""
        results = {
            'buy': [],
            'sell': []
        }
        
        for trade in self.trading_data:
            calculated = (trade['quantity'] / 250) * trade['rate']
            trade['calculated'] = calculated
            
            if trade['direction'] == 'BUY':
                results['buy'].append(trade)
            else:
                results['sell'].append(trade)
        
        return results
    
    def generate_excel(self, output_path='trading_analysis_output.xlsx'):
        """Generate Excel file with analysis"""
        print("\n" + "=" * 60)
        print("GENERATING EXCEL REPORT")
        print("=" * 60)
        
        # Calculate values
        results = self.calculate_values()
        
        buy_total = sum(t['calculated'] for t in results['buy'])
        sell_total = sum(t['calculated'] for t in results['sell'])
        
        # Create workbook
        wb = openpyxl.Workbook()
        
        # Create summary sheet first
        summary_ws = wb.active
        summary_ws.title = "Summary"
        
        self._create_summary_sheet(summary_ws, results, buy_total, sell_total)
        
        # Create detail sheets for each document
        for doc_name, trades in self.documents.items():
            if trades:
                ws = wb.create_sheet(doc_name[:31])  # Excel sheet name limit is 31 chars
                self._create_detail_sheet(ws, trades)
        
        # Save
        wb.save(output_path)
        print(f"\n✓ Excel report generated: {output_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"BUY Total:  {buy_total:,.4f}")
        print(f"SELL Total: {sell_total:,.4f}")
        print(f"NET (BUY - SELL): {buy_total - sell_total:,.4f}")
        print("=" * 60)
        
        return output_path
    
    def _create_summary_sheet(self, ws, results, buy_total, sell_total):
        """Create summary sheet"""
        ws['A1'] = "TRADING ANALYSIS SUMMARY"
        ws['A1'].font = Font(bold=True, size=14)
        
        # Overall summary
        ws['A3'] = "OVERALL TOTALS"
        ws['A3'].font = Font(bold=True, size=12)
        
        ws['A4'] = "Type"
        ws['B4'] = "Total Value"
        ws['C4'] = "Count"
        
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}4']
            cell.fill = header_fill
            cell.font = header_font
            cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                               top=Side(style='thin'), bottom=Side(style='thin'))
        
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                           top=Side(style='thin'), bottom=Side(style='thin'))
        
        # BUY row
        ws['A5'] = "BUY"
        ws['B5'] = buy_total
        ws['C5'] = len(results['buy'])
        ws['B5'].number_format = '0.0000'
        ws['B5'].font = Font(color="008000", bold=True)
        
        for col in ['A', 'B', 'C']:
            ws[f'{col}5'].border = thin_border
        
        # SELL row
        ws['A6'] = "SELL"
        ws['B6'] = sell_total
        ws['C6'] = len(results['sell'])
        ws['B6'].number_format = '0.0000'
        ws['B6'].font = Font(color="FF0000", bold=True)
        
        for col in ['A', 'B', 'C']:
            ws[f'{col}6'].border = thin_border
        
        # NET row
        ws['A7'] = "NET (BUY - SELL)"
        ws['B7'] = buy_total - sell_total
        ws['B7'].number_format = '0.0000'
        ws['B7'].font = Font(bold=True)
        
        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}7']
            cell.border = thin_border
            if col in ['A', 'B']:
                cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 15
    
    def _create_detail_sheet(self, ws, trades):
        """Create detail sheet for a document"""
        # Headers
        headers = ["Sell/Buy", "Quantity", "Market Rate", "Calculated Value (Qty/250 × Rate)"]
        ws.append(headers)
        
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                               top=Side(style='thin'), bottom=Side(style='thin'))
        
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                           top=Side(style='thin'), bottom=Side(style='thin'))
        
        buy_total = 0
        sell_total = 0
        
        # Add data
        for trade in trades:
            ws.append([
                trade['direction'],
                trade['quantity'],
                trade['rate'],
                trade['calculated']
            ])
            
            if trade['direction'] == 'BUY':
                buy_total += trade['calculated']
            else:
                sell_total += trade['calculated']
        
        # Format data
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=4):
            for cell in row:
                cell.border = thin_border
                if cell.column in [3, 4]:
                    cell.number_format = '0.0000'
        
        # Add summary
        summary_row = ws.max_row + 2
        ws[f'A{summary_row}'] = "DOCUMENT SUMMARY"
        ws[f'A{summary_row}'].font = Font(bold=True)
        
        summary_row += 1
        ws[f'A{summary_row}'] = "Type"
        ws[f'B{summary_row}'] = "Total"
        
        for cell in [ws[f'A{summary_row}'], ws[f'B{summary_row}']]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            cell.border = thin_border
        
        summary_row += 1
        ws[f'A{summary_row}'] = "BUY"
        ws[f'B{summary_row}'] = buy_total
        ws[f'B{summary_row}'].number_format = '0.0000'
        ws[f'B{summary_row}'].font = Font(bold=True, color="008000")
        
        for cell in [ws[f'A{summary_row}'], ws[f'B{summary_row}']]:
            cell.border = thin_border
        
        summary_row += 1
        ws[f'A{summary_row}'] = "SELL"
        ws[f'B{summary_row}'] = sell_total
        ws[f'B{summary_row}'].number_format = '0.0000'
        ws[f'B{summary_row}'].font = Font(bold=True, color="FF0000")
        
        for cell in [ws[f'A{summary_row}'], ws[f'B{summary_row}']]:
            cell.border = thin_border
        
        summary_row += 1
        ws[f'A{summary_row}'] = "NET (BUY - SELL)"
        ws[f'B{summary_row}'] = buy_total - sell_total
        ws[f'B{summary_row}'].number_format = '0.0000'
        ws[f'B{summary_row}'].font = Font(bold=True)
        
        for cell in [ws[f'A{summary_row}'], ws[f'B{summary_row}']]:
            cell.border = thin_border
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 30


def main():
    """Main function"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  TRADING DATA ANALYSIS TOOL - OCR VERSION".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Get image paths from user
    print("\nEnter image file paths (one per line, press Enter twice to finish):")
    print("(Supported formats: JPG, PNG, JPEG, TIFF)")
    print("(Note: Paths with spaces and special characters are supported)")
    print()
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    image_paths = []
    while True:
        path = input(f"Image {len(image_paths) + 1}: ").strip()
        if not path:
            if image_paths:
                break
            else:
                print("Please enter at least one image path.")
                continue
        
        # Remove quotes if present (handles copy-paste from Windows Explorer)
        path = path.strip('"').strip("'")
        
        # Validate file exists
        if not os.path.exists(path):
            print(f"  ⚠ File not found: {path}")
            print(f"    Please verify the path is correct (including spaces and parentheses)")
            continue
        
        # Validate file format
        file_ext = Path(path).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            print(f"  ⚠ Unsupported format: {file_ext}")
            print(f"    Supported formats: {', '.join(SUPPORTED_FORMATS)}")
            continue
        
        image_paths.append(path)
        print(f"  ✓ Added: {Path(path).name}")
    
    if not image_paths:
        print("No images provided. Exiting.")
        return
    
    # Create extractor
    extractor = TradingDataExtractor()
    
    # Process images
    if not extractor.process_images(image_paths):
        print("Failed to extract trading data from images.")
        return
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"trading_analysis_{timestamp}.xlsx"
    
    # Generate Excel
    output_path = extractor.generate_excel(output_file)
    
    print(f"\n✓ Analysis complete! File saved as: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
