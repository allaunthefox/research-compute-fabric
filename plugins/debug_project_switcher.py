import sqlite3
import shutil
import asyncio
from playwright.async_api import async_playwright

def get_tokens():
    db_path = "/run/user/1000/psd/allaun-firefox-tobv72sv.default-release/storage/default/https+++contextstream.io/ls/data.sqlite"
    temp_db = "/home/allaun/.gemini/antigravity/scratch/ls_temp.sqlite"
    shutil.copy(db_path, temp_db)
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM data WHERE key IN ('auth_token', 'refresh_token');")
    tokens = {}
    for key, val in cursor.fetchall():
        tokens[key] = val.decode('utf-8', errors='ignore')
    conn.close()
    return tokens

async def main():
    tokens = get_tokens()
    auth_token = tokens.get("auth_token")
    refresh_token = tokens.get("refresh_token")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://contextstream.io")
        await page.wait_for_timeout(2000)
        
        await page.evaluate("""([auth, refresh]) => {
            localStorage.setItem('auth_token', auth);
            localStorage.setItem('refresh_token', refresh);
        }""", [auth_token, refresh_token])
        
        await page.goto("https://contextstream.io/dashboard?stage=skills")
        await page.wait_for_timeout(4000)
        
        # Let's find all elements containing 'llm_wiki'
        print("Finding elements with 'llm_wiki':")
        elements = await page.locator("*:has-text('llm_wiki')").all()
        print(f"Found {len(elements)} elements.")
        for idx, el in enumerate(elements):
            tag = await el.evaluate("e => e.tagName")
            html = await el.evaluate("e => e.outerHTML.slice(0, 200)")
            text = await el.inner_text()
            print(f"  Element {idx}: tag={tag}, text='{text[:50].strip()}', HTML={html}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
