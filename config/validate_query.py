def validate_query(query):
    if query is None:
        return False,"Query is required!!"
    if not isinstance(query,str):
        return False,"Query must be a string."
    query = query.strip()
    length = len(query)
    if length==0:
        return False,"Query can not be empty."
    if length > 500:
        return False,"Query exceeded 500 char"

    return True,query