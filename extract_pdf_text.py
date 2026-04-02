#!/usr/bin/env python3
"""
Extract text from McGuire PDF files for analysis.
Usage: python3 extract_pdf_text.py
Outputs .txt files alongside source PDFs.
"""

import subprocess
import sys
import os

# Install pdfplumber if not present
try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

PDF_DIR = os.path.join(os.path.dirname(__file__), "Martin_McGuire_GC_Publication")

# Files to extract — add or remove as needed
TARGET_FILES = [
    "Chapter 4 Page 183-210.pdf",
    "First Nation land surrenders on the Prairies - Chapter 1.pdf",
    "First Nation land surrenders on the Prairies - Chapter 2.pdf",
    "First Nation land surrenders on the Prairies - Chapter 6.pdf",
    "First Nation land surrenders on the Prairies - Chapter 7.pdf",
]

def extract(pdf_filename):
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    txt_filename = os.path.splitext(pdf_filename)[0] + ".txt"
    txt_path = os.path.join(PDF_DIR, txt_filename)

    if not os.path.exists(pdf_path):
        print(f"  SKIPPED (not found): {pdf_filename}")
        return

    print(f"  Extracting: {pdf_filename}")
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages_text.append(f"--- Page {i} ---\n{text}")
            else:
                pages_text.append(f"--- Page {i} --- [no text layer]")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(pages_text))

    size_kb = os.path.getsize(txt_path) // 1024
    print(f"  Written: {txt_filename} ({size_kb} KB, {len(pages_text)} pages)")

if __name__ == "__main__":
    print(f"PDF directory: {PDF_DIR}\n")
    for filename in TARGET_FILES:
        extract(filename)
    print("\nDone.")
