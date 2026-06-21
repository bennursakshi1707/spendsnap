---
name: receipt-processing
description: Use this skill when a user uploads or mentions a receipt image that needs to be processed into the SpendSnap budget tracker. Handles extracting receipt details, validating them, and writing them to an Excel file.
---

# Receipt Processing Skill

## Purpose

This skill takes a receipt image and turns it into a row in the user's budget Excel file. It runs three tools in a strict order, and stops early if any step fails.

## When to use this skill

Use this skill whenever the user:
- Uploads an image and asks you to process it as a receipt
- Mentions "add this receipt", "track this expense", "update my budget"
- Provides a file path to an image and asks for it to be logged

## The flow — follow these steps in exact order

### Step 1: Extract
Call the `extract_receipt` tool with the image path the user provided.

This tool will tell you if the image is even a receipt. Check the `is_receipt` field in the response.

- If `is_receipt` is `false`: STOP HERE. Tell the user this doesn't look like a receipt, and ask them to check the image or upload a different one. Do not proceed to Step 2.
- If `is_receipt` is `true`: continue to Step 2.

### Step 2: Validate
Call the `validate_receipt` tool, passing it the FULL dictionary you got back from `extract_receipt` in Step 1.

Check the `is_valid` field in the response.

- If `is_valid` is `false`: STOP HERE. Look at the `flags` field to understand why (for example: `missing_total_amount`, `duplicate_receipt`). Explain the specific reason to the user in plain language. Do not proceed to Step 3.
- If `is_valid` is `true`: continue to Step 3.

### Step 3: Write to Excel
Call the `write_excel` tool, passing it the FULL dictionary you got back from `validate_receipt` in Step 2.

Check the `success` field in the response.

- If `success` is `true`: tell the user the receipt was added successfully. Mention the `receipt_id` and the category it was filed under.
- If `success` is `false`: tell the user something went wrong and share the `reason` field.

## Important rules

- Never skip a step. Always go extract → validate → write_excel in that exact order.
- Never call write_excel directly without validating first, even if you think the data looks fine.
- Always pass the COMPLETE dictionary from one tool into the next. Do not pick out only some fields — pass everything forward.
- If a tool's output has flags or warnings beyond the critical ones (like `unusually_large_amount`), still proceed, but mention the warning to the user after writing to Excel.
- Speak to the user in plain, friendly language. Don't show them raw JSON. Summarize what happened.

## Example interaction

User: "Here's a receipt, can you add it? receipts/walmart.jpg"

You should:
1. Call extract_receipt(image_path="receipts/walmart.jpg")
2. See is_receipt: true, proceed
3. Call validate_receipt(extracted_data=<the full result from step 1>)
4. See is_valid: true, proceed
5. Call write_excel(validated_data=<the full result from step 3>)
6. See success: true
7. Reply: "Added! Your $46.42 Walmart purchase was logged as RCP-0003 under Shopping."