USE game_db;
SELECT * FROM game_table;
SELECT * FROM date_platform_table;

DELETE FROM game_table WHERE game_id = 1;
DELETE FROM date_platform_table WHERE game_id = 1;

DROP TABLE game_table;

USE game_db;
SELECT * FROM game_table WHERE LCASE(title) = LCASE('Dynasty Warriors: Origins') OR LCASE(aliases) LIKE CONCAT('%', LCASE('Dynasty Warriors: Origins'), '%');

