from flask import Flask, request, jsonify
import json
# import easyocr
from ocr_receipt_result_processor import extract_receipt_data

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

app = Flask(__name__)
# reader = easyocr.Reader(['uk', 'en'])

@app.route('/api/receipt/processing', methods=['POST'])
def process_receipt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image = request.files['image']
    print('FILE NAME + NAME')
    print(image.filename)

    try:
        # result = reader.readtext(image, detail=0, paragraph=True)
        result = ocr_output
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    receipt_data = extract_receipt_data(result)

    json_result = json.dumps(receipt_data, ensure_ascii=False, indent=2)

    return json_result

@app.route('/api/receipt/test', methods=['POST'])
def test_receipt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image = request.files['image']
    # Hardcoded response
    hardcoded_response = {
        'status': 'success',
        'message': 'This is a test response',
        'image_name': image.filename
    }

    return jsonify(hardcoded_response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
