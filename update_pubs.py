import json, time
from scholarly import scholarly

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def get_author_with_retry(scholar_id, retries=3, delay=5):
    for i in range(retries):
        try:
            print(f"Attempt {i+1}: Searching for author {scholar_id}")
            author = scholarly.search_author_id(scholar_id)
            return scholarly.fill(author, sections=["publications"])
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(delay)
    raise RuntimeError("Failed to fetch author data after retries")

def main():
    author = get_author_with_retry(SCHOLAR_ID)
    items = []
    for pub in author.get("publications", []):
        try:
            p = scholarly.fill(pub)
            bib = p.get("bib", {})
            items.append({
                "title": bib.get("title", ""),
                "authors": bib.get("author", "").split(" and "),
                "venue": bib.get("venue") or bib.get("journal") or bib.get("booktitle") or "",
                "year": str(bib.get("year") or p.get("pub_year") or ""),
                "abstract": bib.get("abstract", ""),
            })
        except Exception as e:
            print("⚠️ Skipped a publication:", e)
            continue

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(items)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
