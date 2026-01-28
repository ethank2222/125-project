def searchDocuments(query):
    results = {
        0: {
            'url': '#',
            'title': 'No results found',
            'desc': f'Your query: {query}'
        },
        1: {
            'url': '#',
            'title': 'No results found',
            'desc': f'Your query: {query}'
        }
    }
    return (results, 2)