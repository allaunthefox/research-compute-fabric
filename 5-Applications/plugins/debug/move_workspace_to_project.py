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
        await page.locator("button[role='combobox']:has-text('llm_wiki')").first.click()
        await page.wait_for_timeout(2000)
        
        print("Selecting 'Research-Stack' project...")
        await page.locator("[role='option']:has-text('Research-Stack')").first.click()
        await page.wait_for_timeout(3000)
        
        # Now change the filter dropdown from 'Account' to 'Workspace'
        print("Clicking scope filter dropdown (currently 'Account')...")
        await page.locator("button[role='combobox']:has-text('Account')").first.click()
        await page.wait_for_timeout(1000)
        
        # Click "Workspace" or "This workspace only" option in dropdown list
        print("Selecting 'Workspace' filter...")
        # Let's find and click the option with text Workspace
        await page.locator("[role='option']:has-text('Workspace'), [role='menuitem']:has-text('Workspace')").first.click()
        await page.wait_for_timeout(3000)
        
        # Print text content to verify skills are listed
        text = await page.evaluate("() => document.body.innerText")
        print("\nPage text content after filtering:")
        print(text[:2000])
        
        # Let's find the links or buttons for the skills
        skills_links = await page.locator("a, button").all()
        print("\nAvailable links/buttons containing skill names:")
        for idx, el in enumerate(skills_links):
            t = await el.inner_text()
            if "Lean" in t or "Servo" in t or "CAD" in t or "URDF" in t:
                print(f"  El {idx}: tag={await el.evaluate('e => e.tagName')}, text='{t.strip()}'")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
