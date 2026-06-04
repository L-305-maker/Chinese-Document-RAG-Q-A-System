from collections import defaultdict


def enhance_documents(documents, top_k, max_per_source=2):
    selected = []
    source_count = defaultdict(int)

    for doc in documents:
        source = (doc.get("metadata") or {}).get("source", "unknown")

        if source_count[source] >= max_per_source:
            continue

        selected.append(doc)
        source_count[source] += 1

        if top_k <= len(selected):
            break

    return selected
