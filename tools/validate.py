import os
import json
from datetime import datetime


# This is where we keep a record of every receipt we've already processed
MEMORY_FILE = "output/processed_receipts.json"


def load_memory() -> list:
    """
    Reads the memory file and returns a list of past receipts.
    If the file doesn't exist yet, returns an empty list.
    """
    if not os.path.exists(MEMORY_FILE):
        return []

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory: list) -> None:
    """
    Writes the updated memory list back to disk.
    """
    os.makedirs("output", exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def validate_and_flag(extracted_data: dict) -> dict:
    """
    Takes the JSON from extract.py and checks it for problems.
    Adds 'is_valid', 'is_duplicate', and 'flags' fields to the data.
    """

    flags = []

    # Step 1: If it wasn't even a receipt, stop here immediately
    if not extracted_data.get("is_receipt"):
        extracted_data["is_valid"] = False
        extracted_data["is_duplicate"] = False
        extracted_data["flags"] = ["not_a_receipt"]
        return extracted_data

    # Step 2: Check for missing critical fields
    merchant = extracted_data.get("merchant_name")
    date = extracted_data.get("date")
    amount = extracted_data.get("total_amount")

    if not merchant:
        flags.append("missing_merchant_name")
    if not date:
        flags.append("missing_date")
    if amount is None:
        flags.append("missing_total_amount")

    # Step 3: Load past receipts and check for duplicates
    memory = load_memory()
    is_duplicate = False

    for past_receipt in memory:
        same_merchant = past_receipt.get("merchant_name") == merchant
        same_date = past_receipt.get("date") == date
        same_amount = past_receipt.get("total_amount") == amount

        if same_merchant and same_date and same_amount:
            is_duplicate = True
            flags.append("duplicate_receipt")
            break

    # Step 4: Check for unusually large amounts (anomaly detection)
    if amount is not None:
        category = extracted_data.get("category")
        category_amounts = [
            r.get("total_amount") for r in memory
            if r.get("category") == category and r.get("total_amount") is not None
        ]

        if len(category_amounts) >= 3:
            average = sum(category_amounts) / len(category_amounts)
            if amount > average * 3:
                flags.append("unusually_large_amount")

    # Step 5: Decide overall validity
    # Valid means: not a duplicate AND no missing critical fields
    critical_issues = ["missing_merchant_name", "missing_total_amount", "duplicate_receipt"]
    is_valid = not any(flag in critical_issues for flag in flags)

    # Step 6: Attach results to the data
    extracted_data["is_valid"] = is_valid
    extracted_data["is_duplicate"] = is_duplicate
    extracted_data["flags"] = flags

    # Step 7: If valid and not duplicate, save it to memory for future duplicate checks
    if is_valid and not is_duplicate:
        memory.append(extracted_data)
        save_memory(memory)

    return extracted_data


# Run this block only when testing this file directly
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tools/validate.py <path_to_json_or_test>")
        print("This is meant to be tested with sample data below.")

        # A sample receipt to test with, since this tool needs JSON input, not an image
        sample_receipt = {
            "is_receipt": True,
            "merchant_name": "Walmart",
            "date": "2020-09-21",
            "total_amount": 46.42,
            "tax_amount": 3.5,
            "currency": "USD",
            "payment_method": "Card",
            "items": ["Yogurt", "Bananas"],
            "category": "Shopping",
            "confidence": 0.95,
            "notes": None,
            "image_path": "receipts/test.jpg"
        }

        print("\nTesting with sample receipt...\n")
        result = validate_and_flag(sample_receipt)
        print(json.dumps(result, indent=2))