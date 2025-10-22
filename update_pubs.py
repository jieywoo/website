import json
from scholarly import scholarly

# === CONFIG ===
SCHOLAR_ID = "GOCSqdUAAAAJ"  # <-- change this to your Scholar ID
OUTPUT = "publications.json"
# ==============

def main():
    print(f"Fetching data for Google Scholar user: {SCHOLAR_ID}")
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    publications = []
    for pub in author.get("publications", []):
        pub_filled = scholarly.fill(pub)
        bib = pub_filled.get("bib", {})
        publications.append({
            "title": bib.get("title"),
            "authors": bib.get("author", "").split(" and "),
            "venue": bib.get("venue"),
            "year": bib.get("year"),
            "citations": pub_filled.get("num_citations", 0),
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": publications}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(publications)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
