-- Insert a user
INSERT INTO users (login, name, email, password, created_at)
VALUES ('test', 'Test User', 'test@example.com', '$argon2id$v=19$m=65536,t=3,p=4$pz9kCkMzfLL4bRDpt/+NnQ$VIjKxYkecADg7aQ3zDEEOCOqmbPHSR6sj0v0kIysshg', CURRENT_TIMESTAMP);

-- Insert bundles
INSERT INTO bundles (name, description, created_at)
VALUES ('Hob Project', 'Everything related to the Hob project', CURRENT_TIMESTAMP),
       ('Personal', 'Everything relateds to me', CURRENT_TIMESTAMP);

-- Insert artifacts
INSERT INTO artifacts (name, type, origin, bundle_id, created_at)
VALUES 
    ('Prompt Template', 'text', 'Stored in DB', 1, CURRENT_TIMESTAMP),
    ('Personal Text', 'text', 'Stored in DB', 2, CURRENT_TIMESTAMP);

-- Link user to bundles
INSERT INTO user_bundle (user_id, bundle_id)
VALUES 
    (1, 1),  -- User with id 1 linked to bundle with id 1
    (1, 2);  -- User with id 1 linked to bundle with id 2
