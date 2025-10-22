import json, asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

async def fetch_publications():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("#gsc_a_b")
        html = await page.content()
        await browser.close()
        return html

def parse_publications(html):
    soup = BeautifulSoup(html, "html.parser")
    pubs = []
    for row in soup.select("#gsc_a_b .gsc_a_tr"):
        title_tag = row.select_one(".gsc_a_at")
        title = title_tag.text.strip() if title_tag else ""
        authors = row.select_one(".gs_gray")
        author_str = authors.text.strip() if authors else ""
        venue_tag = row.select(".gs_gray")
        venue = ""
        if len(venue_tag) > 1:
            venue = venue_tag[1].text.strip()
        year_tag = row.select_one(".gsc_a_y span")
        year = year_tag.text.strip() if year_tag else ""
        pubs.append({
            "title": title,
            "authors": author_str.split(", "),
            "venue": venue,
            "year": year,
            "abstract": ""  # abstracts can be added later if you want
        })
    # Sort by year descending
    pubs.sort(key=lambda x: x.get("year", ""), reverse=True)
    return pubs

async def main():
    print(f"Fetching data for Scholar ID: {SCHOLAR_ID}")
    html = await fetch_publications()
    pubs = parse_publications(html)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": pubs}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(pubs)} publications to {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
