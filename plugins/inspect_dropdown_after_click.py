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
        
        # Click the "Explorer" button to open the sidebar
        print("Clicking 'Explorer' button...")
        await page.locator("button:has-text('Explorer')").first.click()
        await page.wait_for_timeout(2000)
        
        # Click the project combobox trigger (text='llm_wiki')
        print("Clicking project trigger...")
        # Let's target the exact button with role=combobox and text=llm_wiki
        trigger = page.locator("button[role='combobox']:has-text('llm_wiki')").first
        await trigger.click()
        await page.wait_for_timeout(2000)
        
        # Let's find all visible items in the body that appeared after click
        print("Finding all elements containing 'Research-Stack' or 'Research Stack' or 'llm_wiki' in the page:")
        elements = await page.locator("*:has-text('Research')").all()
        for idx, el in enumerate(elements):
            try:
                # Check if visible
                if await el.is_visible():
                    tag = await el.evaluate("e => e.tagName")
                    text = await el.inner_text()
                    html = await el.evaluate("e => e.outerHTML.slice(0, 150)")
                    print(f"  Visible El {idx}: tag={tag}, text='{text.strip()[:40]}', HTML={html}")
            except Exception:
                pass
                
        screenshot_path = "/home/allaun/.gemini/antigravity/scratch/inspect_dropdown.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
