-- schema.sql
CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

-- Employee now includes optional company_id and location_id (home branch).
CREATE TABLE IF NOT EXISTS employee (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  idp_id VARCHAR(255),
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  gender BOOLEAN NOT NULL,
  birth_date DATETIME NOT NULL,
  id_picture VARCHAR(255),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  company_id BIGINT NULL,
  location_id BIGINT NULL
);

CREATE TABLE IF NOT EXISTS availability_slots (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  employee_id BIGINT NOT NULL,
  day_of_week INT NOT NULL,
  time_from TIME NOT NULL,
  time_to TIME NOT NULL,
  location_id BIGINT,
  FOREIGN KEY (employee_id) REFERENCES employee(id)
);

CREATE TABLE IF NOT EXISTS employee_skills (
  employee_id BIGINT NOT NULL,
  service_id BIGINT NOT NULL,
  PRIMARY KEY (employee_id, service_id),
  FOREIGN KEY (employee_id) REFERENCES employee(id)
);

-- If you already had the old table, and need to migrate, run once:
-- ALTER TABLE employee ADD COLUMN company_id BIGINT NULL;
-- ALTER TABLE employee ADD COLUMN location_id BIGINT NULL;
