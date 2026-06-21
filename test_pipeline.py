from tools.extract import extract_receipt_data
from tools.validate import validate_and_flag
from tools.write_excel import write_to_excel
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python test_pipeline.py receipts/your_image.jpg")
    sys.exit(1)

image_path = sys.argv[1]

print("STEP 1: Extracting...")
extracted = extract_receipt_data(image_path)
print(json.dumps(extracted, indent=2))

print("\nSTEP 2: Validating...")
validated = validate_and_flag(extracted)
print(json.dumps(validated, indent=2))

print("\nSTEP 3: Writing to Excel...")
result = write_to_excel(validated)
print(json.dumps(result, indent=2))