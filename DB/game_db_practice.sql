USE game_db;
SELECT * FROM game_table;
SELECT * FROM date_platform_table;

DELETE FROM game_table WHERE game_id = 34;
DELETE FROM date_platform_table WHERE game_id = 9;

DROP TABLE game_table;
DROP TABLE date_platform_table;
USE game_db;
SELECT * FROM game_table WHERE LCASE(title) = LCASE('Dynasty Warriors: Origins') OR LCASE(aliases) LIKE CONCAT('%', LCASE('Dynasty Warriors: Origins'), '%');

CREATE FULLTEXT INDEX titles ON game_table (title, aliases);

SELECT * FROM game_table WHERE MATCH(title, aliases) AGAINST('god of war ragnarok valhalla' IN NATURAL LANGUAGE MODE);