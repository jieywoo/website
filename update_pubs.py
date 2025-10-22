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
        pub_filled = scholarly.fill(pub)
        bib = pub_filled.get("bib", {})
        items.append({
            "title": bib.get("title"),
            "authors": bib.get("author", "").split(" and "),
            "venue": bib.get("venue"),
            "year": bib.get("year"),
            "abstract": bib.get("abstract", ""),
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(items)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
