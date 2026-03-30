import fitz


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts: list[str] = []

    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            page_text = page.get_text().strip()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts)
