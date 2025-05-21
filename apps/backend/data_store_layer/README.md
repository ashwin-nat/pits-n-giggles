+---------------------+
|       Team          |
|---------------------|
| id (PK)             |
| canonical_name      |
+---------------------+

         1
         |
         | has many
         |
+---------------------+
|    TeamAlias        |
|---------------------|
| id (PK)             |
| team_id (FK)        |
| game_title          |
| alias_name          |
+---------------------+

         1
         |
         | has many
         |
+-------------------------------+
|       DrivingSession          |
|-------------------------------|
| id (PK)                       |
| team_id (FK)                  |
| title                         |
| track                         |
| game_mode                     |
| car                           |
| distance_km                   |
| distance_laps                 |
| session_date                  |
+-------------------------------+
         |           |
         |           |
         |           +---------------------+
         |                             has many
         |
+----------------------------+      +-----------------------------+
|   SessionTyreDistance      |      | SessionWeatherDistance      |
|----------------------------|      |-----------------------------|
| id (PK)                    |      | id (PK)                     |
| session_id (FK)            |      | session_id (FK)             |
| actual_compound            |      | weather_type                |
| visual_compound            |      | distance_km                 |
| distance_km                |      | distance_laps               |
| distance_laps              |      +-----------------------------+
+----------------------------+
