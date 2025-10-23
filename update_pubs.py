import json, asyncio, re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

async def fetch_publications_page(page):
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
        print("⚠️ Timeout waiting for publications table.")
    return await page.content()

async def fetch_full_abstract(page, index):
    try:
        selector = f"#gsc_a_b .gsc_a_tr:nth-child({index}) .gsc_a_at"
        elem = page.locator(selector)
        await elem.first.click()
        await page.wait_for_selector("#gsc_vcd_title", timeout=10000)
        html = await page.inner_html("#gsc_vcd")
        soup = BeautifulSoup(html, "html.parser")
        abs_tag = soup.find("div", class_="gsh_csp")
        abstract = abs_tag.get_text(" ", strip=True) if abs_tag else ""
        await page.click("#gsc_md_titlebar button", timeout=5000)
        await asyncio.sleep(0.3)
        return abstract
    except Exception:
        return ""

def clean_venue(venue: str, year: str) -> str:
    """Remove the year or commas at the end of the venue text."""
    if not venue:
        return ""
    v = venue.replace(" ", " ")  # replace non-breaking spaces
    if year:
        v = re.sub(rf"[, ]*\b{re.escape(year)}\b[, ]*$", "", v).strip(" ,")
    return v

def parse_list(soup):
    rows = soup.select("#gsc_a_b .gsc_a_tr")
    pubs = []
    for row in rows:
        title_tag = row.select_one(".gsc_a_at")
        title = title_tag.text.strip() if title_tag else ""
        authors_tag = row.select_one(".gs_gray")
        authors = authors_tag.text.strip() if authors_tag else ""
        meta_tags = row.select(".gs_gray")
        venue = ""
        if len(meta_tags) > 1:
            venue = meta_tags[1].text.strip()
        year_tag = row.select_one(".gsc_a_y span")
        year = year_tag.text.strip() if year_tag else ""
        pubs.append({"title": title, "authors": authors, "venue": venue, "year": year})
    return pubs

async def main():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&view_op=list_works"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        print(f"Fetching: {url}")
        await page.goto(url, timeout=90000)
        html = await fetch_publications_page(page)
        soup = BeautifulSoup(html, "html.parser")
        pubs = parse_list(soup)

        # Add full abstracts
        print(f"Retrieving abstracts for {len(pubs)} items...")
        for i, pub in enumerate(pubs, 1):
            abs_text = await fetch_full_abstract(page, i)
            pub["abstract"] = abs_text
            await asyncio.sleep(0.3)

        await browser.close()

    # Clean author lists and venues
    for p in pubs:
        p["authors"] = [a.strip() for a in re.split(",| and ", p["authors"]) if a.strip()]
        p["venue"] = clean_venue(p.get("venue", ""), p.get("year", ""))

    # Sort by newest year
    def year_key(pub):
        try:
            return int(re.search(r"\d{4}", pub.get("year", "")).group())
        except:
            return 0
    pubs.sort(key=year_key, reverse=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": pubs}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(pubs)} publications to {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
