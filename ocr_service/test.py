import json
import easyocr
from ocr_service.ocr_receipt_result_processor import extract_receipt_data

reader = easyocr.Reader(['uk', 'en'], gpu=True)

result = reader.readtext('D:/Personal/Uni/4_point/thesis/projects/EasyOCR/examples/4.png', detail=0, paragraph=True)

print(result)

# Process the receipt and get a structured result.
receipt_data = extract_receipt_data(result)

# Output the result as formatted JSON.
json_result = json.dumps(receipt_data, ensure_ascii=False, indent=2)
print(json_result)

