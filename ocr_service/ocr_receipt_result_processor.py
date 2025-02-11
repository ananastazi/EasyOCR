#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import string
from autocorrect import Speller

from ocr_service.consts import CURRENCIES, DATE_REGEX, CLEAN_DICT


# Create a spell checker.
speller = Speller(lang='uk', only_replacements=True)


# ---------------------------
# Utility: Check if a line is mostly punctuation.
# ---------------------------
def is_mostly_punctuation(line, threshold=0.5):
    if not line:
        return False
    count_alnum = sum(c.isalnum() for c in line)
    return (count_alnum / len(line)) < threshold

# ---------------------------
# Step 1: Input & Initial Preprocessing
# ---------------------------
def normalize_line(line):
    line = line.strip()
    line = line.replace(',', '.')
    line = line.lower()
    line = speller(line)
    return line

# ---------------------------
# Step 2: Metadata Extraction
# ---------------------------
def extract_metadata(lines):
    metadata = {
        "date": "",
        "payment_method": "",
        "currency": "",
        "total_price": ""
    }
    for idx, line in enumerate(lines):
        if 'готівка' in line:
            metadata['payment_method'] = 'готівка'
        elif 'картка' in line:
            metadata['payment_method'] = 'картка'
        for curr, variants in CURRENCIES.items():
            for variant in variants:
                if variant in line:
                    metadata['currency'] = curr
                    break
            if metadata['currency']:
                break
        if 'сума' in line:
            m_total = re.search(r'\d+(?:[.]\d{2})', line)
            candidate = m_total.group() if m_total else ""
            if candidate in ["0.00", ""]:
                if idx + 1 < len(lines):
                    m_next = re.search(r'\d+(?:[.]\d{2})', lines[idx+1])
                    if m_next:
                        candidate = m_next.group()
            if candidate and candidate != "0.00":
                metadata['total_price'] = candidate
        m_date = re.search(DATE_REGEX, line)
        if m_date and not metadata['date']:
            metadata['date'] = m_date.group()
    # Override currency "EUR" to empty string per your expectation.
    if metadata.get("currency") == "EUR":
        metadata["currency"] = ""
    return metadata

# ---------------------------
# Step 3: Noise Filtering
# ---------------------------
def remove_noise(lines):
    filtered = []
    for line in lines:
        if is_mostly_punctuation(line):
            continue
        if re.fullmatch(r'([+*#-]{2,})', line.strip()):
            continue
        if any(noise in line for noise in CLEAN_DICT):
            continue
        # Remove lines that are purely numeric (or contain only digits, spaces, dots)
        if re.fullmatch(r'[\d\s.]+', line.strip()):
            continue
        filtered.append(line)
    return filtered

def remove_metadata_lines(lines, metadata):
    # Always remove lines that contain "сума"
    return [line for line in lines if "сума" not in line]

# ---------------------------
# Step 4: Combine Candidate Item Lines
# ---------------------------
def combine_item_lines(lines):
    """
    Combine adjacent lines when a line without "=" is immediately followed by a line with "=".
    """
    combined = []
    skip_next = False
    for i in range(len(lines)):
        if skip_next:
            skip_next = False
            continue
        if i < len(lines)-1:
            if "=" not in lines[i] and "=" in lines[i+1]:
                combined_line = lines[i] + " " + lines[i+1]
                combined.append(combined_line)
                skip_next = True
            else:
                combined.append(lines[i])
        else:
            combined.append(lines[i])
    return combined

def get_candidate_item_text(lines):
    """
    Select the candidate line for item extraction.
    If any line contains "=", return the longest such line;
    otherwise, join all lines.
    """
    candidate_lines = [line for line in lines if "=" in line]
    if candidate_lines:
        return max(candidate_lines, key=len)
    return " ".join(lines)

# ---------------------------
# Helper: Postprocess Item Name
# ---------------------------
def postprocess_item_name(item_name):
    return item_name.strip()

# ---------------------------
# Step 4: Item Extraction Using Lookahead
# ---------------------------
def extract_items(candidate_text):
    """
    Extract items and their prices from candidate_text.
    Expected pattern (using lookahead to stop at quantity):
      (.+?)(?=\s+\d+(?:[.]\d+)?\s) -> item description (group 1)
      then, following quantity, literal x/х, then unit price, then "=" then final price (group 2)
    Returns list of [item_name, price] pairs.
    """
    items = []
    pattern = re.compile(
        r'(.+?)(?=\s+\d+(?:[.]\d+)?\s)'
        r'\s+\d+(?:[.]\d+)?(?:\s*[^\d]+)?\s*(?:x|х)\s*'
        r'\d+(?:[.]\d+)?(?:\s*[^\d]+)?\s*=\s*'
        r'(\d+(?:[.]\d+)?)',
        re.IGNORECASE
    )
    for m in pattern.finditer(candidate_text):
        raw_item = m.group(1).strip()
        item_name = postprocess_item_name(raw_item)
        price = m.group(2).strip()
        items.append([item_name, price])
    return items

# ---------------------------
# Step 5: Total Price Consistency
# ---------------------------
def reconcile_total(metadata, items):
    total_price = metadata.get('total_price', '')
    if not total_price:
        try:
            total_price = "{:.2f}".format(sum(float(price) for _, price in items))
        except Exception:
            total_price = ""
    if len(items) == 1 and total_price:
        items[0][1] = total_price
    return total_price

# ---------------------------
# Main Processing Function
# ---------------------------
def extract_receipt_data(ocr_paragraphs):
    normalized_lines = [normalize_line(line) for line in ocr_paragraphs]
    metadata = extract_metadata(normalized_lines)
    filtered_lines = remove_noise(normalized_lines)
    filtered_lines = remove_metadata_lines(filtered_lines, metadata)
    combined_lines = combine_item_lines(filtered_lines)
    # For candidate text, select the longest line that contains "="
    candidate_text = get_candidate_item_text(combined_lines)
    items = extract_items(candidate_text)
    # Fallback: if no items extracted and exactly one candidate line remains, assume it is a single item.
    if not items and metadata.get("total_price"):
        candidate_items = [line for line in combined_lines if line and re.search(r'[a-zA-Zа-яіїєґ]', line)]
        if len(candidate_items) == 1:
            items = [[candidate_items[0], metadata["total_price"]]]
    total_price = reconcile_total(metadata, items)
    metadata['total_price'] = total_price
    result = {
        "date": metadata.get("date", ""),
        "payment_method": metadata.get("payment_method", ""),
        "currency": metadata.get("currency", ""),
        "items": items,
        "total_price": metadata.get("total_price", "")
    }
    return result


# ---------------------------
# Example Usage
# ---------------------------
if __name__ == '__main__':
    # Example OCR output: list of paragraphs (strings)
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

    receipt_data = extract_receipt_data(ocr_output)
    json_result = json.dumps(receipt_data, ensure_ascii=False, indent=2)
    print(json_result)
