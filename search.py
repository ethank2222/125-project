import sqlite3

DB_PATH = "./db/FIT.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
    
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


def initScoring(user_data: dict): 
    """
    :param user_data: dict containing user goals + prefernce
    a initial scoring given user answer to intro form
    """
    
    # INCOMPLETE, INTI SCORING
    match user_data['intent']:
        case 'gain muscle':
            init_score = """
UPDATE exercises 
SET score = CASE category
    WHEN 'strength' THEN score + 10
    WHEN 'powerlifting' THEN score + 8
    WHEN 'strongman' THEN score + 6
    WHEN 'pylometrics' THEN score + 6
    WHEN 'olympic weightlifting' THEN score + 4
    WHEN 'stretching' THEN score + 0
    WHEN 'cardio' THEN score - 6
END
"""
        case 'lose weight':
            init_score = """
UPDATE exercises 
SET score = CASE category
    WHEN 'strength' THEN score + 4
    WHEN 'powerlifting' THEN score - 2
    WHEN 'strongman' THEN score - 2
    WHEN 'pylometrics' THEN score + 8
    WHEN 'olympic weightlifting' THEN score - 2
    WHEN 'stretching' THEN score + 0
    WHEN 'cardio' THEN score + 10
END
"""
    cursor.execute(init_score)
    conn.commit()


def topN(n: int):
    selectN = f"""
    SELECT name
    FROM exercises
    ORDER BY score DESC
    LIMIT {n};
"""
    cursor.execute(selectN)
    return cursor.fetchall()
