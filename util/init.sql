DROP DATABASE IF EXISTS pool_list;
DROP DATABASE IF EXISTS pool_list_testing;
CREATE USER pool_list WITH PASSWORD 'testing';
CREATE DATABASE pool_list;
GRANT ALL PRIVILEGES ON DATABASE pool_list to pool_list;
-- Create a testing database to be different than dev
CREATE DATABASE pool_list_testing;
GRANT ALL PRIVILEGES ON DATABASE pool_list_testing to pool_list;
\c pool_list
CREATE EXTENSION hstore;
\c pool_list_testing
CREATE EXTENSION hstore;
