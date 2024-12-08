CREATE DATABASE attendance_system;

USE attendance_system;

DROP TABLE IF EXISTS `admin`;
DROP TABLE IF EXISTS `attendance`;
DROP TABLE IF EXISTS `users`;

DROP TABLE IF EXISTS `reports`;

-- User Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    enrollment_no VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    college_name VARCHAR(200) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Attendance Table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    status VARCHAR(10) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- Admin Table
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    enrollment_number VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    problem_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('solved', 'unsolved') DEFAULT 'unsolved' -- new column
);

