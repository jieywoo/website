import json, asyncio, re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

async def fetch_html(page, url):
    print(f"Loading {url}")
    await page.goto(url, timeout=120000)
    # Wait until publications appear or timeout
    for _ in range(15):
        rows = await page.locator("#gsc_a_b .gsc_a_tr").count()
        if rows > 0:
            break
        print("⏳ Waiting for publications to appear...")
        await asyncio.sleep(2)
        await page.mouse.wheel(0, 20000)
    html = await page.content()
    return html

def clean_venue(venue, year):
    if not venue:
        return ""
    v = venue.replace("\xa0", " ").strip()
    if year:
        v = re.sub(rf"(,?\s*\b{re.escape(year)}\b)+$", "", v).strip(" ,")
    return v

def parse_publications(html):
    soup = BeautifulSoup(html, "html.parser")
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
        pubs.append({
            "title": title,
            "authors": authors,
            "venue": venue,
            "year": year,
            "abstract": ""
        })
    return pubs

async def fetch_abstracts(page, pubs):
    for i, pub in enumerate(pubs, 1):
        try:
            selector = f"#gsc_a_b .gsc_a_tr:nth-child({i}) .gsc_a_at"
            if await page.locator(selector).count() == 0:
                continue
            await page.locator(selector).first.click()
            await page.wait_for_selector("#gsc_vcd_title", timeout=10000)
            html = await page.inner_html("#gsc_vcd")
            soup = BeautifulSoup(html, "html.parser")
            abs_tag = soup.find("div", class_="gsh_csp")
            abstract = abs_tag.get_text(" ", strip=True) if abs_tag else ""
            pubs[i - 1]["abstract"] = abstract
            await page.click("#gsc_md_titlebar button", timeout=5000)
            await asyncio.sleep(0.3)
        except Exception:
            continue
    return pubs

async def main():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en&view_op=list_works"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        html = await fetch_html(page, url)
        pubs = parse_publications(html)

        if not pubs:
            print("⚠️ No publications detected. Google may be serving a CAPTCHA or blocking automation.")
        else:
            print(f"✅ Found {len(pubs)} publications")

        # Fetch full abstracts
        pubs = await fetch_abstracts(page, pubs)

        await browser.close()

    # Clean and format
    for p in pubs:
        p["authors"] = [a.strip() for a in re.split(",| and ", p["authors"]) if a.strip()]
        p["venue"] = clean_venue(p.get("venue", ""), p.get("year", ""))

    # Sort by newest year
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
