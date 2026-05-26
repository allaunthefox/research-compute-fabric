import asyncio
from playwright.async_api import async_playwright
import os

PASSWORD = "v1D7TtupOMq8pK"
CSV_PATH = "/home/allaun/.gemini/antigravity/scratch/affirm_loans_import.csv"
SCREENSHOT_DIR = "/home/allaun/.gemini/antigravity/scratch/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def main():
    async with async_playwright() as p:
        print("[*] Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        
        # 1. Login
        print("[*] Navigating to login page...")
        await page.goto("https://budget.researchstack.info/login")
        await page.wait_for_selector("input[type='password']")
        await page.fill("input[type='password']", PASSWORD)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/01_login_filled.png")
        await page.click("button:has-text('Sign in')")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/02_after_login.png")
        
        # 2. Open Budget File
        print("[*] Opening 'My Finances' budget...")
        await page.click("text=My Finances")
        await page.wait_for_timeout(8000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_budget_loaded.png")
        
        # 3. Check if 'Affirm Loans' already exists in the sidebar
        sidebar_text = await page.evaluate("document.body.innerText")
        if "Affirm Loans" in sidebar_text:
            print("[+] 'Affirm Loans' account already exists in sidebar. Clicking it...")
            await page.click("text=Affirm Loans")
            await page.wait_for_timeout(4000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_account_opened.png")
        else:
            print("[*] Creating 'Affirm Loans' account...")
            # Click Add account button (sidebar or main page)
            add_account_buttons = page.locator("text=Add account")
            await add_account_buttons.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_add_account_modal.png")
            
            # Click Create local account
            await page.click("button:has-text('Create local account')")
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/05_local_account_form.png")
            
            # Fill form
            await page.fill("input[name='name']", "Affirm Loans")
            await page.check("input[type='checkbox']#offbudget")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/06_form_filled.png")
            
            # Click Create
            await page.locator("button:has-text('Create')").last.click()
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/07_after_account_created.png")
        
        # 4. Trigger Import
        print("[*] Triggering import...")
        # Look for the Import button
        import_btn = page.locator("button:has-text('Import'), a:has-text('Import'), span:has-text('Import')")
        count = await import_btn.count()
        print(f"[*] Found {count} potential import elements")
        
        # Let's try to click the first visible/available Import button
        async with page.expect_file_chooser() as fc_info:
            await import_btn.first.click()
        file_chooser = await fc_info.value
        print(f"[+] Selecting file {CSV_PATH}...")
        await file_chooser.set_files(CSV_PATH)
        await page.wait_for_timeout(6000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/08_after_file_selected.png")
        
        # 5. Confirm mapping and import
        print("[*] Confirming import mapping...")
        # Locate the button that finishes the import
        # Usually it says "Import 21 transactions" or "Import"
        final_btn = page.locator("button:has-text('transactions'), button:has-text('Import')")
        final_count = await final_btn.count()
        print(f"[*] Found {final_count} final import buttons")
        
        await final_btn.last.click()
        print("[*] Finalizing import...")
        await page.wait_for_timeout(6000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/09_import_finished.png")
        
        # Get final status
        final_text = await page.evaluate("document.body.innerText")
        print("\n--- Final Page Body Text ---")
        print(final_text[:2000])
        print("----------------------------")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
