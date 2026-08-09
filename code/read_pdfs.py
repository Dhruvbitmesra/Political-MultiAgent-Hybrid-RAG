import pymupdf
from pathlib import Path


DOCUMENTS_FOLDER = Path("documents")


def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF page by page.

    Returns:
        list: Each item contains the page number and extracted text.
    """

    doc = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text().strip()

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    doc.close()

    return pages


def save_extracted_text(pdf_path, pages):
    """
    Save extracted PDF text into a .txt file.
    """

    output_path = pdf_path.with_suffix(".txt")

    with open(output_path, "w", encoding="utf-8") as file:

        for page in pages:

            file.write("=" * 80 + "\n")
            file.write(f"PAGE {page['page']}\n")
            file.write("=" * 80 + "\n\n")

            file.write(page["text"])
            file.write("\n\n")

    return output_path


def process_pdf(pdf_path):
    """
    Extract text from one PDF and save it.
    """

    print(f"Processing: {pdf_path.name}")

    pages = extract_pdf_text(pdf_path)

    output_path = save_extracted_text(pdf_path, pages)

    print(f"Pages extracted: {len(pages)}")
    print(f"Saved to: {output_path}")

    return pages


if __name__ == "__main__":

    pdf_files = list(DOCUMENTS_FOLDER.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_path in pdf_files:
        process_pdf(pdf_path)

    print("\nExtraction completed.")