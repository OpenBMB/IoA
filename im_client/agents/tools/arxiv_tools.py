import requests
import time


def arxiv_search(
    query: str = "",
    max_results: int | None = None,
) -> str:
    """a wrapper for xplorer arxiv search based on OpenAI's embedding"""

    max_p = max_results // 10

    result = ""
    cnt = 0
    for i in range(max_p + 1):
        resp = requests.get(
            "https://us-west1-semanticxplorer.cloudfunctions.net/semantic-xplorer-db",
            params={"query": query, "p": i},
        )
        data = resp.json()
        for item in data:
            title = item["metadata"]["title"]
            abstract = item["metadata"]["abstract"]
            id = item["id"]
            authors = item["metadata"]["authors"]
            result += f"Arxiv ID: {id}\nPaper Title: {title}\nAuthors: {authors}\nAbstract: {abstract}\n\n"
            cnt += 1
            if cnt == max_results:
                break
        time.sleep(2)

    return result.rstrip()


def arxiv_search_official(
    query: str = "",
    max_results: int | None = None,
) -> str:
    """a wrapper for arxiv.search"""

    import arxiv

    max_results = min(10, max_results)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
    )

    result = ""
    for item in arxiv.Client().results(search):
        abstract = item.summary.replace("\n", " ")
        authors = ", ".join([author.name for author in item.authors])
        result += f"Paper Title: {item.title}\nAuthors: {authors}\nAbstract: {abstract}\npdf_url:{item.pdf_url}\n\n"

    return result
