-- Fix userSplits table to have proper primary key
-- Since PRIMARY KEY is only userid, we need to drop and recreate

DROP TABLE IF EXISTS userSplits;

CREATE TABLE userSplits (
    userid TEXT,
    day TEXT,
    exercises TEXT,
    time INTEGER CHECK (time > 0),
    exerciseCount INTEGER CHECK (exerciseCount > 0),
    PRIMARY KEY (userid, day)
);