ALTER TABLE userSplits 
ADD COLUMN exerciseCount INTEGER
CHECK (exerciseCount > 0);

-- potential col value for cute ui stuff, might drop later