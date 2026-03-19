import sqlite3
import json
import os
import re

DB_PATH = "./db/FIT.db"
RAW_EXERCISES_PATH = os.path.join(os.path.dirname(__file__), "raw_data", "exercises.json")
_EXERCISES_CACHE = None


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def _normalize_exercise_id(name: str) -> str:
    if not name:
        return ""
    cleaned = name.replace("'", "").replace("’", "")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", cleaned).strip("_")


def load_exercises():
    global _EXERCISES_CACHE
    if _EXERCISES_CACHE is not None:
        return _EXERCISES_CACHE
    with open(RAW_EXERCISES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for ex in data:
        ex["id"] = _normalize_exercise_id(ex.get("name", ""))
    _EXERCISES_CACHE = data
    return data


def get_exercise_by_id(exercise_id: str):
    if not exercise_id:
        return None
    data = load_exercises()
    for ex in data:
        if ex.get("id") == exercise_id:
            return ex
    return None


def get_exercise_name_map(exercise_ids):
    data = load_exercises()
    index = {ex.get("id"): ex.get("name") for ex in data}
    return {ex_id: index.get(ex_id, ex_id) for ex_id in exercise_ids}


# HAVE TO UPDATE DB
# front and middle shoulder for push
# back shoulder for pull

# seperate chest exercises into upper chest, lower chest 
PUSH = ['chest', 'shoulders', 'triceps']
PULL = ['biceps', 'shoulders', 'lower back', 'middle back', 'traps', 'lats']
ABS = ['abdominals', 'adductors', 'abductors']
LEGS = ['hamstrings', 'quadriceps', 'calves', 'glutes']


def searchDocuments(query):
    q = (query or "").strip().lower()
    if not q:
        return ([], 0)

    data = load_exercises()
    results = []

    for ex in data:
        name = ex.get("name") or ""
        primary = ", ".join(ex.get("primaryMuscles") or [])
        secondary = ", ".join(ex.get("secondaryMuscles") or [])
        equipment = ex.get("equipment") or ""
        level = ex.get("level") or ""
        category = ex.get("category") or ""
        mechanic = ex.get("mechanic") or ""

        haystack = " ".join([name, primary, secondary, equipment, level, category, mechanic]).lower()
        if q in haystack:
            parts = []
            if primary:
                parts.append(f"Primary: {primary}")
            if secondary:
                parts.append(f"Secondary: {secondary}")
            if equipment:
                parts.append(f"Equipment: {equipment}")
            if level:
                parts.append(f"Level: {level}")
            if category:
                parts.append(f"Category: {category}")
            if mechanic:
                parts.append(f"Mechanic: {mechanic}")
            desc = " | ".join(parts) if parts else "Exercise details"
            results.append({
                "id": ex.get("id"),
                "url": "#",
                "title": name or f"Exercise {ex.get('id')}",
                "desc": desc
            })

    results = results[:30]
    return (results, len(results))


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
