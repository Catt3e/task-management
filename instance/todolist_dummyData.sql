use todolist;
INSERT INTO user (username, hash_password, email)
VALUES
('man', 'hash_man_123', 'man@example.com'),
('alice', 'hash_alice_456', 'alice@example.com'),
('bob', 'hash_bob_789', 'bob@example.com');

-- Tasks for user "man" (id = 1)
INSERT INTO task (user_id, title, description, expire_time, recurrent_type, reminder, repeat_interval, destination)
VALUES
(1, 'Morning workout', '15-minute stretch routine', NOW() + INTERVAL 1 DAY, 0, 30, NULL, 'Home'),
(1, 'Pay electricity bill', 'Check email for invoice', NOW() + INTERVAL 5 DAY, -1, 120, NULL, NULL),
(1, 'Clean desk', 'Finally deal with those cables', NULL, -1, NULL, NULL, 'Home'),
(1, 'Daily journal', 'Write something, anything', NOW() + INTERVAL 2 DAY, 0, 10, NULL, NULL),
(1, 'Buy groceries', 'Milk, eggs, bread', NOW() + INTERVAL 3 HOUR, -1, 20, NULL, 'Supermarket');

-- Tasks for user "alice" (id = 2)
INSERT INTO task (user_id, title, description, expire_time, recurrent_type, reminder, repeat_interval, destination)
VALUES
(2, 'Weekly meeting', 'Team sync-up', NOW() + INTERVAL 7 DAY, 1, 60, 15, 'Office'),
(2, 'Dentist appointment', 'Cleaning session', NOW() + INTERVAL 30 DAY, -1, 1440, NULL, 'Dental Clinic'),
(2, 'Buy birthday gift', 'For mom', NOW() - INTERVAL 2 DAY, -1, NULL, NULL, 'Mall'), -- expired
(2, 'Laundry', 'Don’t mix colors this time', NOW() + INTERVAL 8 HOUR, -1, 30, NULL, 'Home');

-- Tasks for user "bob" (id = 3)
INSERT INTO task (user_id, title, description, expire_time, recurrent_type, reminder, repeat_interval, destination)
VALUES
(3, 'Annual tax filing', 'Get documents ready', '2026-04-01 00:00:00', 2, 43200, NULL, NULL),
(3, 'Guitar practice', 'Scales + 2 songs', NOW() + INTERVAL 1 DAY, 0, 15, NULL, 'Home'),
(3, 'Car maintenance', 'Oil change', NULL, -1, NULL, NULL, 'Auto Shop'),
(3, 'Call parents', 'Weekly check-in', NOW() + INTERVAL 7 DAY, 1, 60, 30, NULL);
