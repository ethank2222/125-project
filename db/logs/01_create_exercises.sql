CREATE TABLE IF NOT EXISTS exercises (
        id TEXT PRIMARY KEY,
        name TEXT,
        force TEXT,
        level TEXT,
        mechanic TEXT,
        equipment TEXT,
        primaryMuscles TEXT,
        secondaryMuscles TEXT,
        instructions TEXT,
        category TEXT,
        images TEXT
)

-- Initial table to store db of exercises