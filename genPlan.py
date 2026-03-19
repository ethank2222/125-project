import sqlite3
import json

DB_PATH = "./db/FIT.db"
DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def resolve_user_id(user):
    if isinstance(user, dict):
        if user.get('user_id') is not None:
            return user.get('user_id')
        if user.get('id') is not None:
            return user.get('id')
    return user


def ensure_usersplits_schema(conn=None):
    close_after = False
    if conn is None:
        conn = get_db_connection()
        close_after = True
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='userSplits';")
    if cursor.fetchone() is None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS userSplits (
                userid TEXT,
                day TEXT,
                exercises TEXT,
                time INTEGER CHECK (time > 0),
                exerciseCount INTEGER CHECK (exerciseCount > 0),
                PRIMARY KEY (userid, day)
            );
        """)
        conn.commit()
        if close_after:
            conn.close()
        return

    cursor.execute("PRAGMA table_info(userSplits);")
    columns = cursor.fetchall()
    pk_map = {col[1]: col[5] for col in columns}
    day_pk = pk_map.get('day', 0)
    user_pk = pk_map.get('userid', 0)

    if day_pk == 0 or user_pk == 0:
        col_names = {col[1] for col in columns}
        day_col = 'day' if 'day' in col_names else ('musclegroup' if 'musclegroup' in col_names else None)
        exercises_col = 'exercises' if 'exercises' in col_names else None
        time_col = 'time' if 'time' in col_names else None
        count_col = 'exerciseCount' if 'exerciseCount' in col_names else None

        cursor.execute("ALTER TABLE userSplits RENAME TO userSplits_old;")
        cursor.execute("""
            CREATE TABLE userSplits (
                userid TEXT,
                day TEXT,
                exercises TEXT,
                time INTEGER CHECK (time > 0),
                exerciseCount INTEGER CHECK (exerciseCount > 0),
                PRIMARY KEY (userid, day)
            );
        """)
        cursor.execute(f"""
            INSERT INTO userSplits (userid, day, exercises, time, exerciseCount)
            SELECT
                userid,
                {day_col if day_col else "NULL"},
                {exercises_col if exercises_col else "NULL"},
                {time_col if time_col else "NULL"},
                {count_col if count_col else "NULL"}
            FROM userSplits_old;
        """)
        cursor.execute("DROP TABLE userSplits_old;")
        conn.commit()

    if close_after:
        conn.close()

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
        case 'upper': return PUSH+PULL
        case 'legs': return PUSH+PULL+LEGS+ABS
        case 'cardio': return LEGS
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
    


# special case
def cardioDay(time, exclude_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    exercises = []
    skip_ids = [''] + (exclude_ids or [])
    musclesAll  = getMuscleGroups('cardio')
    musclesLeft = musclesAll.copy()
    
    # only leg muscles
    # only when mechanic is NULL and force is NULL
    print(f"IN CARDIODAY: TIME = {time}")

    while time > 14:
        musclePQA  = ", ".join(["?"] * len(musclesAll))
        skipIdPQ   = ", ".join(["?"] * len(skip_ids))
        selectQ    = f"""
        SELECT id, primaryMuscles, secondaryMuscles
        FROM exercises
        WHERE (
            primaryMuscles in ({musclePQA})
            OR EXISTS (
                SELECT 1
                FROM json_each(exercises.secondaryMuscles)
                WHERE json_each.value in ({musclePQA})
            )
        )
        AND mechanic IS NULL
        AND force IS NULL
        AND ID NOT IN ({skipIdPQ})
        ORDER BY score DESC
        LIMIT 1;
        """
        queryFill = (*musclesAll, *musclesAll, *skip_ids)

        cursor.execute(selectQ, queryFill)
        res = cursor.fetchone()
        
        if res is None:
            break  # No more exercises found
        
        time -= 15
        exercises.append(res[0])
        skip_ids.append(res[0])

    conn.close()
    return exercises
    

    # return list of exercise id's exactly as buildDay does.


def buildDay(day, time, exclude_ids=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    exercises = []
    skip_ids = [''] + (exclude_ids or [])
    musclesAll  = getMuscleGroups(day)
    musclesLeft = musclesAll.copy()

    if(day=='cardio'):
        return cardioDay(time, exclude_ids=exclude_ids)
    # First iteration
    # print(f"INITIAL Muscles: {musclesLeft}")
    while time > 15 and musclesLeft:
        musclePQL  = ", ".join(["?"] * len(musclesLeft))
        musclePQA  = ", ".join(["?"] * len(musclesAll))
        skipIdPQ   = ", ".join(["?"] * len(skip_ids))
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
        queryFill = (*musclesLeft, *musclesAll, *skip_ids)

        cursor.execute(selectQ, queryFill)
        res = cursor.fetchone()
        
        if res is None:
            break  # No more exercises found
        
        time -= 15
        exercises.append(res[0])
        skip_ids.append(res[0])
        
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
    # print(exercises)
    i_curr = 0
    tail = len(musclesAll)
    bad_queries = 0
    while time > 9:
        musclePQA  = ", ".join(["?"] * len(musclesAll))
        skipIdPQ   = ", ".join(["?"] * len(skip_ids))
        selectQ    = f"""
        SELECT id, primaryMuscles, secondaryMuscles
        FROM exercises
        WHERE primaryMuscles = ?
        AND mechanic = 'isolation'
        AND ID NOT IN ({skipIdPQ})
        ORDER BY score DESC
        LIMIT 1;
        """
        queryFill = (musclesAll[i_curr], *skip_ids)

        cursor.execute(selectQ, queryFill)
        res = cursor.fetchone()
        
        # circular buffer style
        i_curr = (i_curr+1)%tail
        
        if res is None:
            # isolation of that exercise doesn't exist
            bad_queries += 1
            if bad_queries == tail:
                # hacky way of checking that we completely depleted all viable exercises
                break

        else:
            time -= 10
            exercises.append(res[0])
            skip_ids.append(res[0])

    conn.close()
    return exercises


def createUserSplitsTable():
    e01_create_usersplits = f"""
    CREATE TABLE IF NOT EXISTS userSplits (
        userid TEXT,
        day TEXT,
        exercises TEXT,
        time INTEGER CHECK (time > 0),
        exerciseCount INTEGER CHECK (exerciseCount > 0),
        PRIMARY KEY (userid, day)
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


def buildPlan(user, force_new=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_usersplits_schema(conn)
    fullPlan = {}
    user_id = resolve_user_id(user)
    if user_id is None:
        conn.close()
        raise ValueError("Missing user id for plan generation.")
    splitList = daysplitter(user['avail_days'])
    dayNames = DAY_NAMES
    
    for i, day in enumerate(splitList):
        dayName = dayNames[i]
        if day == 'rest':
            fullPlan[dayName] = []
            continue

        cursor.execute("SELECT exercises FROM userSplits WHERE userid = ? AND day = ?;", (str(user_id), day))
        res = cursor.fetchone()

        if force_new:
            if res is not None:
                old_plan = json.loads(res[0])
                if old_plan:
                    pq_id = ", ".join(["?"] * len(old_plan))
                    cursor.execute(f"""
                        UPDATE exercises
                        SET score = score - 4
                        WHERE id IN ({pq_id});
                    """, old_plan)
                    conn.commit()
            dayPlan = buildDay(day, time=user['avail_mins'], exclude_ids=old_plan if res is not None else None)
            print(dayPlan)
            cursor.execute(
                "INSERT OR REPLACE INTO userSplits (userid, day, exercises, time, exerciseCount) VALUES (?, ?, ?, ?, ?);",
                (str(user_id), day, json.dumps(dayPlan), user['avail_mins'], len(dayPlan))
            )
            conn.commit()
        else:
            if res is None:
                dayPlan = buildDay(day, time=user['avail_mins'])
                print(dayPlan)
                # Store the plan for future use
                cursor.execute("INSERT OR REPLACE INTO userSplits (userid, day, exercises, time, exerciseCount) VALUES (?, ?, ?, ?, ?);",
                              (str(user_id), day, json.dumps(dayPlan), user['avail_mins'], len(dayPlan)))
                conn.commit()
            else:
                dayPlan = json.loads(res[0])
        fullPlan[dayName] = dayPlan
    
    conn.close()
    return fullPlan


def reroll_day(user, day):
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_usersplits_schema(conn)
    user_id = resolve_user_id(user)
    if user_id is None:
        conn.close()
        raise ValueError("Missing user id for reroll.")

    splitList = daysplitter(user['avail_days'])
    if day in DAY_NAMES and isinstance(splitList, list):
        day_idx = DAY_NAMES.index(day)
        day = splitList[day_idx]
    if day == 'rest':
        conn.close()
        return []
 
    # Fetch current exercises and saved time for this day
    select_exercises_q = """
    SELECT exercises 
    FROM userSplits
    WHERE userid = ? AND day = ?;
"""
    cursor.execute(select_exercises_q, (str(user_id), day))
    res = cursor.fetchone()
 
    if res is None:
        print(f"No existing plan found for user {user_id} on day '{day}'")
        dayPlan = []
    else:
        dayPlan = json.loads(res[0])
    print(f"Rerolling '{day}' for user {user_id}: {dayPlan}")
 
    # Decrement score for each exercise in the current plan so they rank lower next time
    if dayPlan:
        pq_id = ", ".join(["?"] * len(dayPlan))
        cursor.execute(f"""
            UPDATE exercises
            SET score = score - 4
            WHERE id IN ({pq_id});
        """, dayPlan)
        conn.commit()
 
    # Regenerate the day
    avail_mins = user['avail_mins']
    newDayPlan = buildDay(day, time=avail_mins, exclude_ids=dayPlan if dayPlan else None)
    # REROLLED PLAN CREATED HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print(f"New plan for '{day}': {newDayPlan}")

    # Update userSplits DB
    cursor.execute("""
        INSERT OR REPLACE INTO userSplits (userid, day, exercises, time, exerciseCount)
        VALUES (?, ?, ?, ?, ?);
    """, (str(user_id), day, json.dumps(newDayPlan), avail_mins, len(newDayPlan)))
    conn.commit()

    conn.close()
    return newDayPlan



