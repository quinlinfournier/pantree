import requests
import json

from fastapi import UploadFile, File

from image_utils import RECEIPT_PIC_DIR, process_receipt_image


class OCRError(Exception):
    pass


def ocr(receipt_image: UploadFile = File(...)):
    receiptOcrEndPoint = 'https://ocr.asprise.com/api/v1/receipt'
    content = receipt_image.file.read()
    filename = process_receipt_image(content)
    file_bytes = (RECEIPT_PIC_DIR / filename).read_bytes()
    try: 
        r = requests.post(receiptOcrEndPoint, data={ \
            'api_key': 'TEST',
            'recognizer': 'auto',
            'ref_no': 'ocr_python_123',
           
            },
            files={
            "file": (filename, file_bytes, "image/jpeg")
            },
            timeout=30 
            )
        # Check for sucessful image reading
        r.raise_for_status()
        data = r.json()
        if not data.get("success") or not data.get("receipts"):
            raise OCRError("Couldnt read the receipt.")
    except requests.RequestException as e:
        raise OCRError("The OCR service is unavailable right now.") from e

    with open("receipt.json", "w", encoding="utf-8") as file:
        json.dump(r.json(), file, indent=4)

    return data["receipts"][0]

