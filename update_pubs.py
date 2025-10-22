import json, asyncio, time
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

async def fetch_html():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&view_op=list_works"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        print(f"Loading {url}")
        await page.goto(url, timeout=90000)
        # Scroll repeatedly to load all publications
        last_height = 0
        for _ in range(10):
            await page.mouse.wheel(0, 20000)
            await asyncio.sleep(1)
            height = await page.evaluate("document.body.scrollHeight")
            if height == last_height:
                break
            last_height = height
        # Wait for table if visible
        try:
            await page.wait_for_selector("#gsc_a_b", timeout=60000)
        except PlaywrightTimeout:
            print("⚠️ Timeout waiting for #gsc_a_b, continuing anyway.")
        html = await page.content()
        await browser.close()
        return html

def parse_publications(html):
    soup = BeautifulSoup(html, "html.parser")
    pubs = []
    rows = soup.select("#gsc_a_b .gsc_a_tr")
    for row in rows:
        title_tag = row.select_one(".gsc_a_at")
        title = title_tag.text.strip() if title_tag else ""
        authors = row.select_one(".gs_gray")
        authors_text = authors.text.strip() if authors else ""
        meta_tags = row.select(".gs_gray")
        venue = ""
        if len(meta_tags) > 1:
            venue = meta_tags[1].text.strip()
        year_tag = row.select_one(".gsc_a_y span")
        year = year_tag.text.strip() if year_tag else ""
        pubs.append({
            "title": title,
            "authors": authors_text.split(", "),
            "venue": venue,
            "year": year,
            "abstract": ""
        })
    # Sort newest first
    pubs.sort(key=lambda x: x.get("year", ""), reverse=True)
    return pubs

async def main():
    html = await fetch_html()
    pubs = parse_publications(html)
    if not pubs:
        print("⚠️ No publications parsed; possible CAPTCHA or private profile.")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": pubs}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(pubs)} publications to {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
