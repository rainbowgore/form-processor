#!/usr/bin/env python3
"""
Debug script to see raw OCR output from JPG
"""
import sys
from extractor import run_ocr, run_plain_ocr_raw

def debug_jpg_ocr(jpg_path: str):
    """Show raw OCR output to debug extraction issues"""
    
    print(f"Debugging OCR for: {jpg_path}")
    print("=" * 60)
    
    # Read the JPG file
    try:
        with open(jpg_path, 'rb') as f:
            file_bytes = f.read()
        print(f"File loaded: {len(file_bytes)} bytes")
    except Exception as e:
        print(f"Failed to load file: {e}")
        return
    
    # Run OCR and show raw text
    try:
        print("\n1. LAYOUT OCR (prebuilt-layout):")
        print("-" * 40)
        ocr_text, ocr_raw = run_ocr(file_bytes)
        print(ocr_text)
        
        print(f"\n2. READ OCR (prebuilt-read):")
        print("-" * 40)
        plain_text, read_raw = run_plain_ocr_raw(file_bytes)
        print(plain_text)
        
        # Look for phone-like patterns
        import re
        print(f"\n3. PHONE-LIKE PATTERNS FOUND:")
        print("-" * 40)
        phone_patterns = re.findall(r'\b\d{8,10}\b', ocr_text + " " + plain_text)
        for i, pattern in enumerate(set(phone_patterns)):
            print(f"  Pattern {i+1}: {pattern}")
        
        # Look for ID-like patterns
        print(f"\n4. ID-LIKE PATTERNS FOUND:")
        print("-" * 40)
        id_patterns = re.findall(r'\b\d{9,10}\b', ocr_text + " " + plain_text)
        for i, pattern in enumerate(set(id_patterns)):
            print(f"  Pattern {i+1}: {pattern}")
            
    except Exception as e:
        print(f"OCR failed: {e}")
        return

if __name__ == "__main__":
    jpg_path = "/Users/noasasson/Dev-projects/ha-alternative/phase1_data/form.jpg"
    if len(sys.argv) > 1:
        jpg_path = sys.argv[1]
    
    debug_jpg_ocr(jpg_path)