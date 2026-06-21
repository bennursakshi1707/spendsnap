from fastmcp import FastMCP
mcp = FastMCP("CurrencyTools")

@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) ->dict:
    """
    Converts an amount from one currency to another using fixed exchange
    rates. Use this when a receipt's currency needs to be 
    converted to user's preferred reporting currency.\

    Args:
        amount: The amount to convert.
        from_currency: The currency code to convert from, e.g. USD.
        to_currency: The currency code to convert to, e.g. INR.

    Returns:
        A dictionary with the converted amount and the rate used.
    """
    #Fixed exchange rates for this exercise - not live data 
    rates_to_usd = {
        "USD": 1.0,
        "INR": 0.012,
        "EUR": 1.09,
        "GBP": 1.27,

    }

    if from_currency not in rates_to_usd or to_currency not in rates_to_usd:
        return {
            "success": False,
            "reason": f"Unsupported currency. Supported: {list(rates_to_usd.keys())}"
        }

    amount_in_usd = amount * rates_to_usd[from_currency]
    converted_amount = amount_in_usd / rates_to_usd[to_currency]

    return {
        "success": True,
        "original_amount": amount,
        "from_currency": from_currency,
        "converted_amount": round(converted_amount, 2),
        "to_currency": to_currency
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8001)
