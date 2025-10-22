import json, asyncio, re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

async def fetch_publications_page(page):
    # Scroll to ensure all papers are loaded
    last_height = 0
    for _ in range(10):
        await page.mouse.wheel(0, 20000)
        await asyncio.sleep(1)
        height = await page.evaluate("document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height
    try:
        await page.wait_for_selector("#gsc_a_b", timeout=60000)
    except PlaywrightTimeout:
        print("⚠️ Timeout waiting for #gsc_a_b; continuing anyway.")
    return await page.content()

async def fetch_full_abstract(page, element_selector):
    """Open popup for one publication and extract its abstract."""
    try:
        await element_selector.click()
        await page.wait_for_selector("#gsc_vcd_title", timeout=15000)
        html = await page.inner_html("#gsc_vcd")
        soup = BeautifulSoup(html, "html.parser")
        # Extract abstract (it may be under multiple <div class="gsh_csp"> tags)
        abstract_tag = soup.find("div", class_="gsh_csp")
        abstract = abstract_tag.text.strip() if abstract_tag else ""
        # Clean up popup
        await page.click("#gsc_md_titlebar button", timeout=5000)
        await asyncio.sleep(0.5)
        return abstract
    except Exception as e:
        print("⚠️ Could not fetch abstract:", e)
        return ""

def parse_publications_list(soup):
    """Extract all visible rows from the list table."""
    pubs = []
    rows = soup.select("#gsc_a_b .gsc_a_tr")
    for row in rows:
        title_tag = row.select_one(".gsc_a_at")
        title = title_tag.text.strip() if title_tag else ""
        # authors line (first gray line)
        authors_tag = row.select_one(".gs_gray")
        authors = authors_tag.text.strip() if authors_tag else ""
        # second gray line → venue and possibly year
        meta_tags = row.select(".gs_gray")
        venue = ""
        if len(meta_tags) > 1:
            venue = meta_tags[1].text.strip()
        # year column
        year_tag = row.select_one(".gsc_a_y span")
        year = year_tag.text.strip() if year_tag else ""
        pubs.append({
            "title": title,
            "authors": authors,
            "venue": venue,
            "year": year,
            "abstract": "",
        })
    return pubs

async def main():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&view_op=list_works"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        print(f"Loading {url}")
        await page.goto(url, timeout=90000)

        html = await fetch_publications_page(page)
        soup = BeautifulSoup(html, "html.parser")
        pubs = parse_publications_list(soup)

        # Fetch full abstracts by clicking each publication
        print(f"Fetching abstracts for {len(pubs)} publications...")
        for i, pub in enumerate(pubs, 1):
            try:
                selector = f"#gsc_a_b .gsc_a_tr:nth-child({i}) .gsc_a_at"
                elem = page.locator(selector)
                if await elem.count() == 0:
                    continue
                abstract = await fetch_full_abstract(page, elem)
                pub["abstract"] = abstract
            except Exception as e:
                print("⚠️ Skipped abstract:", e)

        await browser.close()

    # Clean and format data
    for p in pubs:
        # split authors into list
        p["authors"] = [a.strip() for a in re.split(",| and ", p["authors"]) if a.strip()]
        # ensure only one year field and remove duplicates in venue string
        p["venue"] = re.sub(r"\\b\\d{4}\\b", "", p["venue"]).strip()
        p["venue"] = re.sub(r"\\s{2,}", " ", p["venue"]).strip()

    # Sort by year (descending numeric if possible)
    def year_key(pub):
        try:
            return int(re.search(r"\\d{4}", pub.get("year", "")).group())
        except:
            return 0
    pubs.sort(key=year_key, reverse=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": pubs}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(pubs)} publications to {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
