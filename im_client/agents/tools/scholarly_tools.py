def scholarly_search_author(
    query: str = "",
) -> str:
    """a wrapper for scholarly.search_author"""
    from scholarly import scholarly

    search_query = scholarly.search_author(query)

    result = ""
    for item in search_query:
        result += "{"
        for k, v in item.items():
            if k not in ["container_type", "filled", "source", "scholar_id"]:
                result += f"{k}: {v}\n"
        result += "}"
        result += "\n"
    return result


def scholarly_search_keyword(
    query: str = "",
) -> str:
    """a wrapper for scholarly.search_keyword"""
    from scholarly import scholarly

    search_query = scholarly.search_keyword(query)
    result = ""
    for item in search_query:
        result += "{"
        for k, v in item.items():
            if k not in ["container_type", "filled", "source", "scholar_id"]:
                result += f"{k}: {v}\n"
        result += "}"
        result += "\n"
    return result


def scholarly_search_pubs(
    query: str = "",
) -> str:
    """a wrapper for scholarly.search_pubs"""
    from scholarly import scholarly

    search_query = scholarly.search_pubs(query)
    result = ""
    for item in search_query:
        result += "{"
        for k, v in item.items():
            if k not in ["container_type", "filled", "source", "scholar_id"]:
                result += f"{k}: {v}\n"
        result += "}"
        result += "\n"
    return result
