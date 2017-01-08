CREATE TABLE IF NOT EXISTS "projects"
    ("id" INTEGER PRIMARY KEY NOT NULL ,  -- 0
     "type" INTEGER NOT NULL ,            -- 1
     "submit_date" INTEGER NOT NULL ,     -- 2
     "budget_min" INTEGER NOT NULL ,      -- 3
     "budget_max" INTEGER NOT NULL ,      -- 4
     "technologies" TEXT NOT NULL ,       -- 5
     "developers" TEXT NOT NULL ,         -- 6
     "winner" INTEGER NOT NULL );         -- 7
