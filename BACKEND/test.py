from PIL import Image
from pytesseract import pytesseract

pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
complete_text = pytesseract.image_to_string(Image.open(r"COMPLETE_SCREENSHOT_0.png"))
#Filter image text - replace all newlink/;pes and special characters
# complete_text = complete_text.replace("\n", "")
# complete_text = complete_text.replace("@", "")
# complete_text = complete_text.replace("©", "")
print("COMPLETED TEXT:", complete_text)