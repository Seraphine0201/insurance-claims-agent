import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image = Image.open("test_image.png")
extracted_text = pytesseract.image_to_string(image)

print("Extracted text:")
print(extracted_text)