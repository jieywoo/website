import json
from scholarly import scholarly, ProxyGenerator

SCHOLAR_ID = "GOCSqdUAAAAJ"
OUTPUT = "publications.json"

def main():
    pg = ProxyGenerator()
    pg.FreeProxies()
    scholarly.use_proxy(pg)

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])

    items = []
    for pub in author["publications"]:
        pub = scholarly.fill(pub)
        bib = pub.get("bib", {})
        items.append({
            "title": bib.get("title"),
            "authors": bib.get("author", "").split(" and "),
            "venue": bib.get("venue"),
            "year": bib.get("year"),
            "citations": pub.get("num_citations", 0),
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(items)} publications to {OUTPUT}")

if __name__ == "__main__":
    main()
