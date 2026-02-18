import sqlite3
import json

DB_PATH = "./db/FIT.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# HAVE TO UPDATE DB
# front and middle shoulder for push
# back shoulder for pull

# seperate chest exercises into upper chest, lower chest 
PUSH = ['chest', 'shoulders', 'triceps']
PULL = ['biceps', 'shoulders', 'lower back', 'middle back', 'traps', 'lats']
ABS = ['abdominals', 'adductors', 'abductors']
LEGS = ['hamstrings', 'quadriceps', 'calves', 'glutes']

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
    WHEN 'plyometrics' THEN score + 6
    WHEN 'olympic weightlifting' THEN score + 4
    WHEN 'stretching' THEN score + 0
    WHEN 'cardio' THEN score - 6
END;
"""
        case 'lose weight':
            init_score = """
UPDATE exercises 
SET score = CASE category
    WHEN 'strength' THEN score + 4
    WHEN 'powerlifting' THEN score - 2
    WHEN 'strongman' THEN score - 2
    WHEN 'plyometrics' THEN score + 8
    WHEN 'olympic weightlifting' THEN score - 2
    WHEN 'stretching' THEN score + 0
    WHEN 'cardio' THEN score + 10
END;
"""
    cursor.execute(init_score)
    conn.commit()

# TODO 
# 1. Error handling: muscle group isn't in compounds
# 2. Error handling: muscle group isn't primary
# 3. Isolation exercise "round"
# 4. seperate shoulders into push and pull varients
# 5. have fun :D
def buildDay(day="push"):
    exercises = ['']
    time = 90
    musclesAll = getMuscleGroups(day)
    musclesLeft = musclesAll.copy()
    
    # First iteration
    # print(f"Remaining {musclesLeft}")
    while time > 0 and musclesLeft:  
        musclePQL = ", ".join(["?"] * len(musclesLeft))
        musclePQA = ", ".join(["?"] * len(musclesAll))
        skipIdPQ =  ", ".join(["?"] * len(exercises))
        selectQ = f"""
        SELECT id, primaryMuscles, secondaryMuscles
        FROM exercises
        WHERE (
            primaryMuscles in ({musclePQL})
            AND EXISTS (
                SELECT 1 
                FROM json_each(exercises.secondaryMuscles) 
                WHERE json_each.value in ({musclePQA})
            )
        )
        AND mechanic = 'compound'
        AND ID NOT IN ({skipIdPQ})
        ORDER BY score DESC
        LIMIT 1;
        """
        queryFill = (*musclesLeft, *musclesAll, *exercises)
        
        cursor.execute(selectQ, queryFill) 
        res = cursor.fetchone()
        
        time -= 15
        exercises.append(res[0])
        musclesLeft.remove(res[1])
        secondaryMuscles = json.loads(res[2])

        for e in secondaryMuscles:
            if e in musclesLeft:
                musclesLeft.remove(e)
        # print(f"Remaining {musclesLeft}")
    # Second iteration, allowing for isolations

    return exercises[1:]


def getMuscleGroups(day) -> list:
    # should return appropriate muscle groups based on day split
    match day:
        case 'push':
            return PUSH
        case 'pull':
            return PULL
        case 'upper':
            return PUSH + PULL
        case 'lower':
            return LEGS
        case 'full2':
            pass
        case 'full3':
            pass
    print(f"NOT a valid day: {day}")
    return None




def topN(n: int):
    selectN = f"""
    SELECT name, score
    FROM exercises
    ORDER BY score DESC
    LIMIT {n};
"""
    cursor.execute(selectN)
    return cursor.fetchall()


def createUserSplitsTable():
    e01_create_usersplits = f"""
    CREATE TABLE IF NOT EXISTS userSplits (
        userid TEXT PRIMARY KEY,
        musclegroup TEXT,
        exercises TEXT
        );
"""
    print(DB_PATH)
    import os
    print(os.path.abspath('.'))
        # create a database connection
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # create a cursor
            cursor = conn.cursor()

            # execute statements
            cursor.execute(e01_create_usersplits)

            # commit the changes
            conn.commit()
    
            print("Tables created successfully.")
    except sqlite3.OperationalError as e:
        print("Failed to create tables:", e)



