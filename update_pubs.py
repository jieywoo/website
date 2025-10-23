import json
import re
from scholarly import scholarly

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def clean_venue(venue, year):
    """Remove duplicated year from venue text."""
    if not venue:
        return ""
    v = venue.replace("\xa0", " ").strip()
    if year:
        v = re.sub(rf"(,?\s*\b{re.escape(year)}\b)+$", "", v).strip(" ,")
    return v

def main():
    print(f"Fetching publications for Scholar ID: {SCHOLAR_ID}")
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        author = scholarly.fill(author, sections=["publications"])
    except Exception as e:
        print("⚠️ Error accessing Scholar:", e)
        return

    pubs = []
    for i, pub in enumerate(author.get("publications", []), 1):
        try:
            pub_filled = scholarly.fill(pub)
            bib = pub_filled.get("bib", {})
            title = bib.get("title", "")
            authors = bib.get("author", "")
            authors_list = [a.strip() for a in re.split(",| and ", authors) if a.strip()]
            venue = clean_venue(bib.get("venue", ""), bib.get("year", ""))
            year = bib.get("year", "")
            abstract = bib.get("abstract", "")
            pubs.append({
                "title": title,
                "authors": authors_list,
                "venue": venue,
                "year": year,
                "abstract": abstract
            })
            print(f"  ✓ {title[:60]}...")
        except Exception as e:
            print("⚠️ Skipped one publication:", e)
            continue

    # Sort by year descending
    def year_key(p):
        try:
            return int(re.search(r"\d{4}", p.get("year", "")).group())
        except:
            return 0
    pubs.sort(key=year_key, reverse=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": pubs}, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(pubs)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
