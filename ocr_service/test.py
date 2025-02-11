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

ocr_output = [
        "#x+*+++++++++",
        "САНТЕХСЕРВІС ШЕВЧЕРКІВСЬЮОВСЬКА_ ОБЛ  M: ДНІПРО P-H; Запорізьке шосе, 27 *xx*x***** Касир: **********",
        "Бойлер Allantic OPROP VM 080 0400-1-M",
        "7 2859,00 2859,00",
        "Сума Без ПДВ (0.0035) Готівка",
        "2859.00",
        "2859.00",
        "Валюта: Грн Чек N? qSБPKpKyBNW ФН ПРРО 4000057642 ОНЛАЙН 11,01 2021 09 51.16 ФІСКАЛЬНИЙ ЧЕК checkbox"
    ]
