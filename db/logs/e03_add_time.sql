ALTER TABLE userSplits 
ADD COLUMN time INTEGER 
CHECK (time > 0);

-- time value to better match with user needs