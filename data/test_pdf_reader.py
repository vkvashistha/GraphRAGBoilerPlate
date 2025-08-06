from pathlib import Path
import PyPDF2

def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PyPDF2.PdfReader(str(pdf_path))
    all_text = []
    for i, page in enumerate(reader.pages, start=1):
        print(f"Extracting text from page {i}")
        text = page.extract_text() or f"[Page {i}: no extractable text]\n"
        all_text.append(text)
    return "\n\n".join(all_text)

def main():
    # PDF as a Path
    # pdf_file = Path("Dell Pro Max 14 Premium owners manual.pdf")
    pdf_file = Path("dell-pro-max-14-ma14250-owners-manual-en-us.pdf")
    
    # Extract
    text = extract_text_from_pdf(pdf_file)
    
    # Change suffix for your output Path
    out_file = pdf_file.with_suffix(".txt")
    out_file.write_text(text, encoding="utf-8")
    
    print(f"Extracted text written to {out_file}")

if __name__ == "__main__":
    main()
