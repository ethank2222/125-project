import sqlite3
import json

DB_PATH = "./db/FIT.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

# TODO DB updates:
# 1. bin shoulders into shoulders interior, shoulders exterior (pull and push)
# *2. Seperate chest into legs, upper, middle
# 3. Add back 'legs back'
PUSH = ['chest', 'shoulders', 'triceps']
PULL = ['biceps', 'shoulders', 'middle back', 'traps', 'lats']
ABS  = ['abdominals', 'adductors', 'abductors']
# REMOVED TEMPORARILY: 'legs back'
LEGS = ['hamstrings', 'quadriceps', 'glutes','calves']

# TODO 
# 1. Flesh out fullA and fullB 
# *1. Alternativly keep as just "full" and diversify at query time
# 2. Flesh out cardio
# 3. Flesh out rest
# *3. convert to stretch?
def getMuscleGroups(day) -> list:
    # should return appropriate muscle groups based on day split
    match day:
        case 'push':  return PUSH
        case 'pull':  return PULL
        case 'upper': return PUSH + PULL
        case 'legs': return LEGS
        case 'fullA': pass
        case 'fullB': pass
        case 'fullC': pass
        case 'cardio': pass
        case 'rest': pass

    print(f"NOT a valid day: {day}")
    return None

# TODO
# 1. Refine Split suggestions
# ex: 3-day split with limited time --> push,pull,legs
# ex: 3-day split with extra time --> fulla, fullb, fullc
# 2. Utalize rest days better (stretching, cardio)
# 3. Specify to user plans 
# ex: if user wants weight loss, add programing for weight loss 
def daysplitter(days):
    if days == 1:
        return ["rest","rest","rest","full","rest","rest","rest"]
    elif days == 2:
        return ["rest","rest","upper","rest","rest","legs","rest"]
    elif days == 3:
        return ["rest","push","rest","pull","rest","legs","rest"]
    elif days == 4:
        return ["upper","rest","legs","rest","upper","rest","legs"]
    elif days == 5:
        return ["push","pull","legs","rest","upper","legs","rest"]
    elif days == 6:
        return ["push","pull","legs","rest","push","pull","legs"]
    elif days == 7:
        return ["push","pull","legs","cardio","push","pull","legs"]
    else:
        return "Not a valid number of days!"
    

# TODO buildDay updates:
# 1. Error handling: muscle groups that are not in compounds
# 2. Isolation exercise round
def buildDay(day, time):
    conn = get_db_connection()
    cursor = conn.cursor()
    exercises  = ['']
    musclesAll  = getMuscleGroups(day)
    musclesLeft = musclesAll.copy()

    # First iteration
    # print(f"INITIAL Muscles: {musclesLeft}")
    while time > 0 and musclesLeft:
        musclePQL  = ", ".join(["?"] * len(musclesLeft))
        musclePQA  = ", ".join(["?"] * len(musclesAll))
        skipIdPQ   = ", ".join(["?"] * len(exercises))
        selectQ    = f"""
        SELECT id, primaryMuscles, secondaryMuscles
        FROM exercises
        WHERE (
            primaryMuscles in ({musclePQL})
            OR EXISTS (
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
        
        if res is None:
            break  # No more exercises found
        
        time -= 15
        exercises.append(res[0])
        
        # Remove primary muscle if it's in the list
        primary = res[1]
        if primary in musclesLeft:
            musclesLeft.remove(primary)
        
        # Remove secondary muscles if they're in the list
        secondaryMuscles = json.loads(res[2])
        for e in secondaryMuscles:
            if e in musclesLeft:
                musclesLeft.remove(e)
        # print(f"Remaining {musclesLeft}")
    # Second iteration, focus on isolations

    conn.close()
    return exercises[1:]


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


def dayExist(day)-> bool:
    cursor.execute("SELECT 1 FROM userSplits WHERE day  = ? LIMIT 1", (day,))
    return cursor.fetchone() is not None


def buildPlan(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    fullPlan = {}
    splitList = daysplitter(user['avail_days'])
    dayNames = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for i, day in enumerate(splitList):
        dayName = dayNames[i]
        if day == 'rest':
            fullPlan[dayName] = []
            continue
        
        cursor.execute("SELECT exercises FROM userSplits WHERE userid = ? AND day = ?;", (str(user['id']), day))
        res = cursor.fetchone()
        if res is None:
            dayPlan = buildDay(day, time=user['avail_mins'])
            # Store the plan for future use
            cursor.execute("INSERT OR REPLACE INTO userSplits (userid, day, exercises, time, exerciseCount) VALUES (?, ?, ?, ?, ?);",
                          (str(user['id']), day, json.dumps(dayPlan), user['avail_mins'], len(dayPlan)))
            conn.commit()
        else:
            dayPlan = json.loads(res[0])
        fullPlan[dayName] = dayPlan
    
    conn.close()
    return fullPlan
