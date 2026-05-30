import os
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
        print("Opening sidebar...")
        await page.locator("button:has-text('Explorer')").first.click()
        await page.wait_for_timeout(2000)
        
        # Click the project combobox trigger (text='llm_wiki')
        print("Clicking project trigger...")
        await page.locator("button[role='combobox']:has-text('llm_wiki')").first.click()
        await page.wait_for_timeout(2000)
        
        print("Selecting 'Research-Stack' project...")
        await page.locator("[role='option']:has-text('Research-Stack')").first.click()
        
        # Let's wait for navigation or state change
        print("Waiting for page change...")
        await page.wait_for_timeout(5000)
        
        print(f"URL after project selection: {page.url}")
        print(f"Title after project selection: {await page.title()}")
        
        # Let's print out the body innerText to see if it shows the dashboard or skills page
        text = await page.evaluate("() => document.body.innerText")
        print("\nPage text content after project selection:")
        print(text[:2000])
        
        screenshot_path = "/home/allaun/.gemini/antigravity/scratch/after_project_selection.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
