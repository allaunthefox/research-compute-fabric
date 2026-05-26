import asyncio
from playwright.async_api import async_playwright
import os
import glob
import re

PASSWORD = "v1D7TtupOMq8pK"
IMPORT_DIR = "/home/allaun/.gemini/antigravity/scratch/imports"
SCREENSHOT_DIR = "/home/allaun/.gemini/antigravity/scratch/screenshots/multi_import"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# List of account files to import and their original names
IMPORT_ACCOUNTS = [
    {"file": "Chime-Chime_account.csv", "name": "Chime account"},
    {"file": "Chime-Chime_Secured_Credit.csv", "name": "Chime Secured Credit"},
    {"file": "Capital_One-Quicksilver.csv", "name": "Quicksilver"},
    {"file": "Credit_One_Bank-Visa.csv", "name": "Visa"},
    {"file": "Venmo_-_Personal-Personal_Profile.csv", "name": "Personal Profile"},
    {"file": "Capital_One-credit_Account_8214.csv", "name": "credit Account 8214"},
    {"file": "Capital_One-depository_Account_8109.csv", "name": "depository Account 8109"},
    {"file": "Capital_One-depository_Account_9461.csv", "name": "depository Account 9461"},
    {"file": "Capital_One-depository_Account_9555.csv", "name": "depository Account 9555"},
]

async def import_account(page, file_info):
    csv_path = os.path.join(IMPORT_DIR, file_info["file"])
    acc_name = file_info["name"]
    
    if not os.path.exists(csv_path):
        print(f"[-] Warning: CSV file {csv_path} does not exist. Skipping.")
        return
        
    print(f"\n[*] Processing account '{acc_name}' from {file_info['file']}...")
    
    # 1. Check if account already exists in the sidebar
    sidebar_text = await page.evaluate("document.body.innerText")
    if acc_name in sidebar_text:
        print(f"[+] '{acc_name}' already exists in sidebar. Clicking it...")
        # To avoid clicking random text, let's find the navigation element or link matching the name
        # In Actual, sidebar items are links or text
        await page.click(f"text='{acc_name}'")
        await page.wait_for_timeout(3000)
    else:
        print(f"[*] Creating '{acc_name}' account...")
        # Click Add account button (sidebar or main page)
        add_account_buttons = page.locator("text=Add account")
        await add_account_buttons.first.click()
        await page.wait_for_timeout(2000)
        
        # Click Create local account
        await page.click("button:has-text('Create local account')")
        await page.wait_for_timeout(2000)
        
        # Fill form (On-budget by default)
        await page.fill("input[name='name']", acc_name)
        
        # Click Create (using the last button to avoid clicking parent hidden button)
        await page.locator("button:has-text('Create')").last.click()
        await page.wait_for_timeout(5000)
        
    # 2. Trigger Import
    print(f"[*] Triggering import for '{acc_name}'...")
    import_btn = page.locator("button:has-text('Import'), a:has-text('Import'), span:has-text('Import')")
    count = await import_btn.count()
    if count == 0:
        print(f"[-] Error: Could not find Import button for '{acc_name}'")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/error_{acc_name.replace(' ', '_')}.png")
        return
        
    # Trigger file chooser
    async with page.expect_file_chooser() as fc_info:
        await import_btn.first.click()
    file_chooser = await fc_info.value
    print(f"[+] Selecting file {csv_path}...")
    await file_chooser.set_files(csv_path)
    await page.wait_for_timeout(5000)
    
    # 3. Confirm mapping and import
    print("[*] Confirming import mapping...")
    # Locate the button that finishes the import
    final_btn = page.locator("button:has-text('transactions'), button:has-text('Import')")
    final_count = await final_btn.count()
    print(f"[*] Found {final_count} final import buttons")
    
    if final_count > 0:
        await final_btn.last.click()
        print("[*] Finalizing import...")
        await page.wait_for_timeout(5000)
        
        # Take a screenshot to document success
        safe_name = acc_name.replace(' ', '_')
        await page.screenshot(path=f"{SCREENSHOT_DIR}/{safe_name}_imported.png")
        print(f"[+] Import of '{acc_name}' completed. Screenshot saved.")
    else:
        print(f"[-] Error: No final import button found for '{acc_name}'")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/error_confirm_{acc_name.replace(' ', '_')}.png")

async def main():
    async with async_playwright() as p:
        print("[*] Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        # Login
        print("[*] Navigating to login page...")
        await page.goto("https://budget.researchstack.info/login")
        await page.wait_for_selector("input[type='password']")
        await page.fill("input[type='password']", PASSWORD)
        await page.click("button:has-text('Sign in')")
        await page.wait_for_timeout(5000)
        
        # Open Budget File
        print("[*] Opening 'My Finances' budget...")
        await page.click("text=My Finances")
        await page.wait_for_timeout(8000)
        
        # Loop through accounts and import them
        for file_info in IMPORT_ACCOUNTS:
            try:
                await import_account(page, file_info)
            except Exception as e:
                print(f"[-] Exception occurred while processing '{file_info['name']}': {e}")
                # Save screenshot of failure
                safe_name = file_info["name"].replace(' ', '_')
                await page.screenshot(path=f"{SCREENSHOT_DIR}/exception_{safe_name}.png")
                
        # Final screenshot of budget sidebar
        # Click budget menu to go to main dashboard or budget overview
        try:
            await page.click("text=Budget")
            await page.wait_for_timeout(5000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/final_sidebar_overview.png")
            print("[+] Saved final budget overview screenshot.")
        except Exception as e:
            print(f"[-] Failed to capture final overview: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
