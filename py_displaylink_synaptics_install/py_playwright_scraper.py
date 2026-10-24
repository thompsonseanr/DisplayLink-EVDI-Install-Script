import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError

def py_scraper():
    retry: int = 3
    delay: int = 5
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto("https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu")
        except Exception:
            sys.exit(1)
        download_link = page.locator("a.download-link").nth(1)
        download_link.click()

        for a in range(retry):
            try:
                with page.expect_download(timeout=60000) as download_info:
                    page.locator("a.no-link").click()

                download = download_info.value
                dlPath = f"/tmp/{download.suggested_filename}"
                download.save_as(dlPath)
                return dlPath
            
            except:
                if a < retry - 1:
                    time.sleep(delay)
                else:
                    raise RuntimeError("Error")

        browser.close()

if __name__ == "__main__":
    py_scraper()
