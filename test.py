import search 
import genPlan
# typical user setup for testing
# no preferences, no injuries
TEST_USER = { 
    'user_id': 1, 
    'intent': "gain muscle", 
    'avail_days': 7,
    'avail_mins': 60,
    'weight': 180, 
    'height': 70, 
    'age': 21, 
    'gender' : 'male', 
    'previous_injuries' : "",
}
#
# DESPERATE CONSIDERATIONS
# 6. Weight max on lifts/ suggestions
# 7. 
def main():
    print(genPlan.buildPlan(TEST_USER))
    # # search.initScoring(TEST_USER)
    # exercisesPush = search.buildDay(day='upper')
    # print(exercisesPush)
    # # exercises = search.topN(10)
    # # for e in exercises:
    # #     print(e)
    
    # search.createUserSplitsTable()
    # print("created table")
    print(genPlan.cardioDay(60))

if __name__ == "__main__":
    main()
    