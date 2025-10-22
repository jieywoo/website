import json
from scholarly import scholarly

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def main():
    print(f"Fetching data for Scholar ID: {SCHOLAR_ID} ...")
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    items = []
    for pub in author.get("publications", []):
        try:
            pub_filled = scholarly.fill(pub)
            bib = pub_filled.get("bib", {})

            # Try multiple fallbacks for venue and year
            venue = (
                bib.get("venue")
                or bib.get("journal")
                or bib.get("conference")
                or bib.get("booktitle")
                or ""
            )
            year = (
                bib.get("year")
                or pub_filled.get("pub_year")
                or bib.get("publication_year")
                or ""
            )

            items.append({
                "title": bib.get("title", ""),
                "authors": bib.get("author", "").split(" and "),
                "venue": venue,
                "year": str(year),
                "abstract": bib.get("abstract", ""),
            })
        except Exception as e:
            print(f"⚠️ Skipped one publication: {e}")
            continue

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(items)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
