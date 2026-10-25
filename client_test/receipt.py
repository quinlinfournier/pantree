import json
import requests

print("=== Python Receipt OCR ===")

receiptOcrEndPoint = 'https://ocr.asprise.com/api/v1/receipt'
imageFile = "image.png"
r = requests.post(receiptOcrEndPoint, data = { \
    'api_key': 'TEST',
    'recognizer': 'auto',
    'ref_no': 'ocr_python_123',
    },
    files = {"file": open(imageFile, "rb")}) 

# data = json.loads(r.text)

with open("receipt.json", "w", encoding="utf-8") as file:
    json.dump(r.json(), file, indent=4)