# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import os
import asyncio
from coinbase.rest import RESTClient
from dotenv import load_dotenv

async def test_auth():
    load_dotenv()
    api_key = os.getenv("COINBASE_API_KEY_NAME")
    api_secret = os.getenv("COINBASE_API_KEY_PRIVATE_KEY", "").replace("\\n", "\n")
    
    print(f"[*] Testing Coinbase Auth with Key: {api_key}")
    
    try:
        client = RESTClient(api_key=api_key, api_secret=api_secret)
        # List all accounts
        accounts = client.get_accounts()
        for a in accounts.accounts:
            # Handle both object and dict access for available_balance
            balance = getattr(a.available_balance, 'value', a.available_balance.get('value', '0'))
            currency = getattr(a.available_balance, 'currency', a.available_balance.get('currency', ''))
            
            if a.currency in ['BTC', 'ETH', 'USD', 'USDC']:
                print(f"[*] Account: {a.name} ({a.currency}) | Balance: {balance} {currency}")
            elif float(balance) > 0:
                # Still show non-zero balances
                print(f"[*] Account: {a.name} ({a.currency}) | Balance: {balance} {currency}")
        
        product = client.get_product("ZEC-USD")
        print(f"[+] SUCCESS: Auth verified. ZEC Price: {product.price}")
    except Exception as e:
        print(f"[!] Auth Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
