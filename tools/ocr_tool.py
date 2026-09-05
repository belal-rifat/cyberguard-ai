import pytesseract
from PIL import Image

# Windows-এ Tesseract সাধারণত এই path-এ install হয়।
# যদি তোমার install path আলাদা হয়, নিচের path পরিবর্তন করো।
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_path: str) -> str:
    """
    Given a path to an image file, returns the text extracted from it using OCR.
    """
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image)
    return extracted_text.strip()


if __name__ == "__main__":
    # টেস্ট করার জন্য: data/ folder-এ একটা sample screenshot রেখে path বসাও
    sample_path = "test_image.png"
    text = extract_text_from_image(sample_path)
    print("Extracted text:\n")
    print(text)
