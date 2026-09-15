#import sys
from playwright.sync_api import sync_playwright, TimeoutError

def py_scraper():
    with sync_playwright() as p:
        # browser = p.chromium.launch(headless=True)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto("https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu")
        downloadLink = page.locator("a.download-link").nth(1)
        downloadLink.click()

        with page.expect_download() as downloadInfo:
            page.locator("a.no-link").click()

        download = downloadInfo.value
        downloadUrl = download.url
        print(f"Download URL: {downloadUrl}")


if __name__ == "__main__":
    py_scraper()
