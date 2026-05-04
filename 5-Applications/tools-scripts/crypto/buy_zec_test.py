# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os
import asyncio
import json
import time
from coinbase.rest import RESTClient
from dotenv import load_dotenv

async def buy_zec_test():
    load_dotenv()
    key_name = os.getenv("COINBASE_API_KEY_NAME")
    key_secret = os.getenv("COINBASE_API_KEY_PRIVATE_KEY", "").replace("\\n", "\n")
    client = RESTClient(api_key=key_name, api_secret=key_secret)
    
    amount_usd = 0.05
    print(f"[*] Attempting to BUY ${amount_usd:.2f} worth of ZEC...")
    
    try:
        # Create a market order
        # Note: Advanced Trade market orders usually require quote_size (USD amount)
        order = client.create_order(
            client_order_id=f"ZEC-TEST-BUY-{int(time.time())}",
            product_id="ZEC-USD",
            side="BUY",
            order_configuration={
                "market_market_ioc": {
                    "quote_size": str(amount_usd)
                }
            }
        )
        print(f"[+] Order Response: {order}")
        
        if order.success:
            print(f"[+] SUCCESS: Purchased ${amount_usd:.2f} of ZEC.")
        else:
            print(f"[!] Order failed: {order.error_response}")
            
    except Exception as e:
        print(f"[!] Error executing buy: {e}")

if __name__ == "__main__":
    asyncio.run(buy_zec_test())
