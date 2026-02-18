def daysplitter(days):
    if days == 1:
        return ["rest","rest","rest","full","rest","rest","rest"]
    elif days == 2:
        return ["rest","rest","upper","rest","rest","lower","rest"]
    elif days == 3:
        return ["rest","push","rest","pull","rest","legs","rest"]
    elif days == 4:
        return ["upper","rest","lower","rest","upper","rest","lower"]
    elif days == 5:
        return ["push","pull","legs","rest","upper","lower","rest"]
    elif days == 6:
        return ["push","pull","legs","rest","push","pull","legs"]
    elif days == 7:
        return ["push","pull","legs","cardio","push","pull","legs"]
    else:
        return "Not a valid number of days!"