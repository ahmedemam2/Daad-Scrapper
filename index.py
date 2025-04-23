from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www2.daad.de/deutschland/studienangebote/international-programmes/en/detail/7169"
    "/")

    # Accept the biscuit     
    page.wait_for_selector("button:has-text('Accept')")
    page.click("button:has-text('Accept')")

    page.wait_for_load_state("networkidle")
    
    page.click("#costs-tab")

    #Bitte kostenloses Stipendium
    funding_label = page.locator("dt:has-text('Funding opportunities within the university')").nth(0)
    funding_value = funding_label.locator("xpath=following-sibling::dd[1]")
    print(funding_value.inner_text())

    browser.close()
