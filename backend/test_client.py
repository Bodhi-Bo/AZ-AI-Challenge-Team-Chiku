import asyncio
import websockets
import json
import sys


async def chat():
    """Simple WebSocket client to chat with the calendar assistant."""
    user_id = "6915408f5d210a8bbafdb8c7"
    uri = f"ws://localhost:8000/ws/{user_id}"

    while True:  # Auto-reconnect loop
        try:
            print("🤖 Connecting to Calendar Assistant...")

            async with websockets.connect(uri) as websocket:
                print("✅ Connected! Type 'quit' to exit.\n")

                # Receive welcome message
                welcome = await websocket.recv()
                data = json.loads(welcome)
                print(f"Assistant: {data['text']}\n")

                # Chat loop
                while True:
                    # Get user input
                    try:
                        user_message = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: input("You: ")
                        )
                    except EOFError:
                        print("\n👋 Input closed. Exiting...")
                        return

                    if user_message.lower() in ["quit", "exit", "q"]:
                        print("👋 Goodbye!")
                        return

                    if not user_message.strip():
                        continue

                    # Send message
                    await websocket.send(
                        json.dumps({"type": "message", "text": user_message})
                    )

                    # Receive response
                    response = await websocket.recv()
                    data = json.loads(response)
                    print(f"\nAssistant: {data['text']}\n")

        except websockets.exceptions.ConnectionClosed:
            print("\n⚠️  Connection closed. Reconnecting in 2 seconds...")
            await asyncio.sleep(2)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Retrying in 2 seconds...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("\n💡 Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
