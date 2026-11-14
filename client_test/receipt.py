import json

# print("=== Python Receipt OCR ===")

# receiptOcrEndPoint = 'https://ocr.asprise.com/api/v1/receipt'
# imageFile = "image.png"
# r = requests.post(receiptOcrEndPoint, data = { \
#     'api_key': 'TEST',
#     'recognizer': 'auto',
#     'ref_no': 'ocr_python_123',
#     },
#     files = {"file": open(imageFile, "rb")}) 

# # data = json.loads(r.text)

# with open("receipt.json", "w", encoding="utf-8") as file:
#     json.dump(r.json(), file, indent=4)

raw = json.load(open("receipt.json", encoding="utf-8"))
# print(raw.keys(), raw["receipts"][0].keys())
src = raw["receipts"][0]
new = {
    "retailer": src.get("merchant_name"),
    "purchase_date": src.get("date"),
    "currency": src.get("currency"),
    "total": src.get("total"),
    }

new["items"] = [{"description": i.get("description"), "amount": i.get("amount")} for i in src.get("items", [])]

json.dump(new, open("pantree_receipt.json", "w", encoding="utf-8"), indent=4)