import json, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(options=opts)

def parse_profile(html):
    soup = BeautifulSoup(html, "html.parser")
    pubs = []
    rows = soup.select("#gsc_a_b .gsc_a_tr")
    for row in rows:
        title_tag = row.select_one(".gsc_a_at")
        title = title_tag.text.strip() if title_tag else ""
        authors = row.select_one(".gs_gray").text.strip() if row.select_one(".gs_gray") else ""
        meta_tags = row.select(".gs_gray")
        venue = ""
        if len(meta_tags) > 1:
            venue = meta_tags[1].text.strip()
        year_tag = row.select_one(".gsc_a_y span")
        year = year_tag.text.strip() if year_tag else ""
        # open publication popup for abstract
        abstract = ""
        if title_tag and title_tag.get("data-href"):
            pass  # skip popup retrieval for speed
        pubs.append({
            "title": title,
            "authors": authors.split(", "),
            "venue": venue,
            "year": year,
            "abstract": abstract
        })
    return pubs

def main():
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en"
    print("Fetching:", url)
    driver = init_driver()
    driver.get(url)
    time.sleep(3)
    html = driver.page_source
    driver.quit()

    publications = parse_profile(html)
    publications.sort(key=lambda p: p.get("year", ""), reverse=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": publications}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(publications)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
