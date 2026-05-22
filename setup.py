#!/usr/bin/env python3
"""
Quick Setup Script for Trading Data Analyzer
Helps with initial setup and troubleshooting
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("\n" + "="*60)
    print("INSTALLING PYTHON DEPENDENCIES")
    print("="*60)
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def check_tesseract():
    """Check if Tesseract is installed"""
    print("\n" + "="*60)
    print("CHECKING TESSERACT OCR")
    print("="*60)
    
    try:
        result = subprocess.run(["tesseract", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Tesseract found: {version_line}")
            return True
    except FileNotFoundError:
        pass
    
    # Check Windows default installation path
    if sys.platform == "win32":
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(tesseract_path).exists():
            print(f"✓ Tesseract found at: {tesseract_path}")
            print("  You may need to add this path to your system PATH")
            return True
        
        tesseract_path_x86 = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        if Path(tesseract_path_x86).exists():
            print(f"✓ Tesseract found at: {tesseract_path_x86}")
            return True
    
    print("❌ Tesseract OCR not found")
    print("\n📝 Installation Instructions:")
    
    if sys.platform == "win32":
        print("""
  Windows:
  1. Download installer from: 
     https://github.com/UB-Mannheim/tesseract/wiki
  2. Run the installer (accept default location)
  3. Restart your terminal/IDE
  4. Run this script again
        """)
    elif sys.platform == "darwin":
        print("""
  macOS:
  1. Install Homebrew (if not installed):
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  2. Run: brew install tesseract
  3. Run this script again
        """)
    else:
        print("""
  Linux (Ubuntu/Debian):
  1. Run: sudo apt-get update
  2. Run: sudo apt-get install tesseract-ocr
  3. Run this script again
  
  Linux (Fedora/RedHat):
  1. Run: sudo yum install tesseract
  2. Run this script again
        """)
    
    return False


def test_ocr():
    """Test OCR functionality"""
    print("\n" + "="*60)
    print("TESTING OCR FUNCTIONALITY")
    print("="*60)
    
    try:
        import pytesseract
        from PIL import Image
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        
        # Try to extract text
        text = pytesseract.image_to_string(img)
        print("✓ OCR test successful")
        return True
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False


def check_dependencies():
    """Check if all Python dependencies are installed"""
    print("\n" + "="*60)
    print("CHECKING PYTHON DEPENDENCIES")
    print("="*60)
    
    dependencies = {
        'pytesseract': 'PyTesseract',
        'PIL': 'Pillow',
        'cv2': 'OpenCV',
        'openpyxl': 'OpenPyXL'
    }
    
    all_installed = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} - not installed")
            all_installed = False
    
    return all_installed


def main():
    """Main setup function"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  TRADING DATA ANALYZER - SETUP".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check existing dependencies
    if not check_dependencies():
        print("\n⚠ Some dependencies are missing")
        print("Installing dependencies...")
        if not install_dependencies():
            sys.exit(1)
    else:
        print("\n✓ All Python dependencies are installed")
    
    # Check Tesseract
    tesseract_ok = check_tesseract()
    
    # Test OCR if Tesseract is available
    if tesseract_ok:
        test_ocr()
    
    # Final summary
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    if check_dependencies() and tesseract_ok:
        print("""
✓ All systems ready!

You can now run the trading data analyzer:
  python trading_data_analyzer.py

📚 For detailed instructions, see: README.md
        """)
    else:
        print("""
⚠ Setup incomplete

Issues found:
- Tesseract OCR needs to be installed

Please follow the installation instructions above,
then run this setup script again.
        """)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
