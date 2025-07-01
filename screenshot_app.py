import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def take_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Take screenshots of different states
        screenshots_dir = "data/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            print("📸 Taking screenshots of the current UI...")
            
            # 1. Setup Screen
            await page.goto('http://localhost:3001')
            await page.wait_for_load_state('networkidle')
            await page.screenshot(path=f'{screenshots_dir}/ui_setup_screen_{timestamp}.png')
            print("✅ Setup screen screenshot saved")
            
            # Wait a bit for any animations
            await page.wait_for_timeout(2000)
            
            # 2. Try to navigate through the app if possible
            # Look for navigation elements
            await page.screenshot(path=f'{screenshots_dir}/ui_full_page_{timestamp}.png', full_page=True)
            print("✅ Full page screenshot saved")
            
            # 3. Try mobile view
            await page.set_viewport_size({'width': 375, 'height': 667})
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f'{screenshots_dir}/ui_mobile_{timestamp}.png')
            print("✅ Mobile view screenshot saved")
            
            # 4. Tablet view
            await page.set_viewport_size({'width': 768, 'height': 1024})
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f'{screenshots_dir}/ui_tablet_{timestamp}.png')
            print("✅ Tablet view screenshot saved")
            
        except Exception as e:
            print(f"❌ Error taking screenshots: {e}")
            await page.screenshot(path=f'{screenshots_dir}/ui_error_{timestamp}.png')
        
        await browser.close()
        print(f"📁 Screenshots saved in {screenshots_dir}/")

if __name__ == "__main__":
    asyncio.run(take_screenshot()) 