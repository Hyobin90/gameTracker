CREATE TABLE IF NOT EXISTS game_table (
	game_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    aliases VARCHAR(1024),
	wikidata_code VARCHAR(100) UNIQUE,
    genres VARCHAR(1024),
    developers VARCHAR(255),
    publishers VARCHAR(255),
    pro_enhanced BOOLEAN,
    meta_critic_score INT UNSIGNED,
    meta_user_score FLOAT UNSIGNED,
	open_critic_score INT UNSIGNED,
    open_user_score FLOAT UNSIGNED,
    my_score INT UNSIGNED
);

CREATE TABLE IF NOT EXISTS date_platform_table (
	release_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    game_id INT NOT NULL,
	release_date DATE,
    released BOOLEAN,
    platforms VARCHAR(255),
    regions VARCHAR(255),
    FOREIGN KEY (game_id) REFERENCES game_table(game_id)
);