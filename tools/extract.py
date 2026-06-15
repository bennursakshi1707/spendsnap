import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_receipt_data(image_path: str) -> dict:
    """
    Sends a receipt image to GPT-5.5 vision.
    In ONE call it:
      1. Checks if this is actually a receipt
      2. Extracts all receipt details
      3. Assigns a spending category
    Returns everything as a clean dictionary.
    """

    # Step 1: Read the image and convert to base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Step 2: Detect file type
    extension = image_path.split(".")[-1].lower()
    mime_type = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"

    # Step 3: Send to GPT-5.5 with one smart prompt
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """You are a receipt extraction assistant.

Look at this image carefully and do the following:

STEP 1 - CLASSIFY:
First decide: is this a receipt or invoice? 
A receipt has: store/merchant name, date, items or services, and a total amount.
If it is NOT a receipt, set is_receipt to false and stop.

STEP 2 - EXTRACT (only if it is a receipt):
Extract every detail you can see.

STEP 3 - CATEGORISE:
Assign exactly one category from this list:
Food, Travel, Shopping, Utilities, Healthcare, Entertainment, Other

Reply ONLY with a valid JSON object. No explanation. No markdown. Just raw JSON.

Use this exact structure:
{
  "is_receipt": true or false,
  "merchant_name": "store name or null",
  "date": "YYYY-MM-DD format or null",
  "total_amount": number or null,
  "tax_amount": number or null,
  "currency": "currency code like INR or USD or null",
  "payment_method": "Cash or Card or UPI or null",
  "items": ["item1", "item2"] or [],
  "category": "one of the categories above or null",
  "confidence": number between 0 and 1,
  "notes": "anything unusual about this receipt or null"
}"""
                    }
                ]
            }
        ],
        max_completion_tokens=500
    )

    # Step 4: Get the raw text response from GPT-5.5
    raw_text = response.choices[0].message.content.strip()
    

    # Step 5: Parse the JSON GPT-5.5 returned
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # If GPT-5.5 returned something we can't parse, return a safe error dict
        result = {
            "is_receipt": False,
            "error": "Could not parse GPT response",
            "raw_response": raw_text
        }

    # Step 6: Always attach the image path so the next tools know which file this was
    result["image_path"] = image_path

    return result


# Run this block only when you run this file directly for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tools/extract.py receipts/your_image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    print(f"\nProcessing: {image_path}")
    print("Sending to GPT-4o-mini vision...\n")

    result = extract_receipt_data(image_path)

    print("--- Extraction Result ---")
    print(json.dumps(result, indent=2))