import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

load_dotenv()


async def main():
    # Step 1: Connect to our MCP server
    # This describes HOW to start it, same as before
    mcp_client = MultiServerMCPClient({
        "spendsnap": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "http"
        },

        "currency": {
            "url": "http://127.0.0.1:8001/mcp",
            "transport": "http"
        }
    })


    # Step 2: Actually fetch the tools from that server
    # This starts the server as a subprocess and asks it
    # "what tools do you have?" - getting back extract_receipt,
    # validate_receipt, and write_excel as usable tool objects
    mcp_tools = await mcp_client.get_tools()

    print(f"Connected to MCP server. Found {len(mcp_tools)} tools:")
    for tool in mcp_tools:
        print(f"  - {tool.name}")

    # Step 3: Create the deep agent, passing in the MCP tools
    # exactly like we would with any custom Python tool
    agent = create_deep_agent(
        tools=mcp_tools,
        model="openai:gpt-4o-mini",
        system_prompt="""You are SpendSnap, a helpful assistant that processes 
receipt images and adds them to the user's budget tracker. 
You have access to a receipt-processing skill that tells you exactly 
how to handle receipt uploads. Always follow that skill's instructions 
precisely, in order. You also have access to a convert_currency tool 
if the user asks you to convert an amount between currencies.""",
    )

    # Step 4: Run the agent with our task
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent.py receipts/your_image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    user_message = f"Here's a receipt, can you add it? {image_path}"

    print(f"\nUser: {user_message}\n")
    print("Agent is thinking...\n")

    result = await agent.ainvoke({
        "messages": [
            {"role": "user", "content": user_message}
        ]
    })

    final_message = result["messages"][-1]
    print("--- Agent's Final Reply ---")
    print(final_message.content)


if __name__ == "__main__":
    asyncio.run(main())