from fastmcp import FastMCP
from tools.extract import extract_receipt_data
from tools.validate import validate_and_flag
from tools.write_excel import write_to_excel


# Create the MCP server, give it a name
mcp = FastMCP("SpendSnap")


@mcp.tool()
def extract_receipt(image_path: str) -> dict:
    """
    Looks at a receipt image and extracts merchant name, date, total amount,
    tax, currency, payment method, items, and category.
    Use this first when a user uploads a receipt image.

    Args:
        image_path: The file path to the receipt image (jpg or png).

    Returns:
        A dictionary with all extracted receipt details, or is_receipt: false
        if the image is not a receipt.
    """
    return extract_receipt_data(image_path)


@mcp.tool()
def validate_receipt(extracted_data: dict) -> dict:
    """
    Checks extracted receipt data for problems: duplicates, missing fields,
    or unusually large amounts. Use this after extract_receipt.

    Args:
        extracted_data: The dictionary returned by extract_receipt.

    Returns:
        The same data with is_valid, is_duplicate, and flags added.
    """
    return validate_and_flag(extracted_data)


@mcp.tool()
def write_excel(validated_data: dict) -> dict:
    """
    Writes a validated receipt as a new row in the SpendSnap budget Excel file.
    Use this last, only after validate_receipt confirms is_valid is true.

    Args:
        validated_data: The dictionary returned by validate_receipt.

    Returns:
        A dictionary confirming success and the receipt_id, or a reason
        for failure if the receipt was not valid.
    """
    return write_to_excel(validated_data)


# This runs the server when you execute this file directly
if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)