create database todolist;
use todolist;

CREATE TABLE user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    deleted_at DATETIME DEFAULT NULL
);


CREATE TABLE task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    time_set DATETIME DEFAULT CURRENT_TIMESTAMP,
    expire_time DATETIME DEFAULT NULL,
    recurrent_type INT DEFAULT -1,   -- -1 = no repeat
    reminder BIGINT DEFAULT NULL,
    repeat_interval BIGINT DEFAULT NULL,   -- renamed to avoid confusion with SQL keyword "REPEAT"
    destination VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL,
    deleted_at DATETIME DEFAULT NULL,

    CONSTRAINT fk_task_user FOREIGN KEY (user_id)
        REFERENCES user(id)
        ON DELETE CASCADE
);

