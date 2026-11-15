import requests
import json

from fastapi import Request, UploadFile, File

from image_utils import RECEIPT_PIC_DIR, process_receipt_image


def ocr(request: Request, receipt_image: UploadFile = File(...)):
    receiptOcrEndPoint = 'https://ocr.asprise.com/api/v1/receipt'
    content = receipt_image.file.read()
    filename = process_receipt_image(content)
    file_bytes = (RECEIPT_PIC_DIR / filename).read_bytes()

    r = requests.post(receiptOcrEndPoint, data={ \
        'api_key': 'TEST',
        'recognizer': 'auto',
        'ref_no': 'ocr_python_123',
        },
        files={
          "file": (filename, file_bytes, "image/jpeg")
        },
        )
    with open("receipt.json", "w", encoding="utf-8") as file:
        json.dump(r.json(), file, indent=4)

    return r 
    