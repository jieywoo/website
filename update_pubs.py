import json
from scholarly import scholarly

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def extract_value(pub, *keys):
    for k in keys:
        if k in pub and pub[k]:
            return pub[k]
    return ""

def main():
    print(f"Fetching data for Scholar ID: {SCHOLAR_ID} ...")
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    results = []
    for p in author.get("publications", []):
        try:
            full = scholarly.fill(p)
            bib = full.get("bib", {})

            title = bib.get("title", "")
            authors = bib.get("author", "").split(" and ")
            abstract = extract_value(bib, "abstract", "description")
            venue = extract_value(
                bib, "venue", "journal", "conference", "booktitle", "publisher"
            )
            year = (
                extract_value(bib, "year", "pub_year", "publication_year")
                or extract_value(full, "year", "pub_year")
            )

            results.append({
                "title": title,
                "authors": authors,
                "venue": venue,
                "year": str(year),
                "abstract": abstract,
            })
        except Exception as e:
            print("⚠️ Skipped one publication:", e)
            continue

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": results}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(results)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
