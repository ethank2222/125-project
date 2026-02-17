import search 

# typical user setup for testing
# no preferences, no injuries
TEST_USER = { 
    'user_id': 1, 
    'intent': "gain muscle", 
    'avail_days': 4,
    'avail_mins': 60,
    'weight': 180, 
    'height': 70, 
    'age': 21, 
    'gender' : 'male', 
    'previous_injuries' : "",
}

def main():
    # search.initScoring(TEST_USER)
    exercisesPush = search.buildDay(day='upper')
    print(exercisesPush)
    # exercises = search.topN(10)
    # for e in exercises:
    #     print(e)


if __name__ == "__main__":
    main()
    