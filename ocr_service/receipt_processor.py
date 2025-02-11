from flask import Flask, request, jsonify
import json
import easyocr
from ocr_service.ocr_receipt_result_processor import extract_receipt_data

app = Flask(__name__)
reader = easyocr.Reader(['uk', 'en'])

@app.route('/api/receipt/processing', methods=['POST'])
def process_receipt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image = request.files['image']

    try:
        result = reader.readtext(image, detail=0, paragraph=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    receipt_data = extract_receipt_data(result)

    json_result = json.dumps(receipt_data, ensure_ascii=False, indent=2)

    return json_result


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
