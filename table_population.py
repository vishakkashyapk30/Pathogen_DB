import pymysql

db = pymysql.connect(
    host="localhost",
    user="root",
    password="agn1705mY5ql",
    database="pathogen"
)

cursor = db.cursor()

create_table_sql = """
CREATE TABLE IF NOT EXISTS Pathogen (
    id VARCHAR(255) PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    type ENUM('Virus', 'Bacteria', 'Protozoa', 'Fungus') NOT NULL,
    lethality_rate DECIMAL(5,2) NOT NULL CHECK (lethality_rate BETWEEN 0 AND 100),
    transmission_method ENUM('Airborne', 'Waterborne', 'Bloodborne', 'Droplet', 'Contact', 'Sexual') NOT NULL,
    predecessor VARCHAR(255),
    incubation_period INT NOT NULL CHECK (incubation_period >= 0),
    mutation_probability DECIMAL(5,2) NOT NULL CHECK (mutation_probability BETWEEN 0 AND 100),
    FOREIGN KEY (predecessor) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_table_sql)

pathogen_data = [
    ("101", "Influenza A", "Virus", 0.30, "Airborne", None, 14, 0.10),
    ("102", "Mycobacterium tuberculosis", "Bacteria", 0.50, "Airborne", None, 21, 0.05),
    ("103", "Plasmodium falciparum", "Protozoa", 0.20, "Bloodborne", None, 12, 0.15),
    ("104", "Candida albicans", "Fungus", 0.10, "Contact", None, 7, 0.20),
    ("105", "Ebola virus", "Virus", 50.00, "Contact", None, 21, 0.30),
]

for pathogen in pathogen_data:
    sql = "INSERT IGNORE INTO Pathogen (id, scientific_name, type, lethality_rate, transmission_method, predecessor, incubation_period, mutation_probability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, pathogen)

db.commit()

create_country_table_sql = """
CREATE TABLE IF NOT EXISTS Country (
    country_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    population INT NOT NULL,
    health_quality_index INT,
    climate ENUM('Temperate', 'Tropical', 'Arid', 'Polar') NOT NULL,
    borders_open BOOLEAN
)
"""

cursor.execute(create_country_table_sql)

country_data = [
    (201, "India", 1_380_004_000, 55, "Tropical", True),
    (202, "United States", 328_200_000, 89, "Temperate", False),
    (203, "Brazil", 212_559_000, 70, "Tropical", True),
    (204, "Russia", 145_934_000, 80, "Temperate", False),
    (205, "Australia", 25_499_000, 85, "Arid", True),
    (206, "Canada", 37_742_000, 90, "Polar", False),
    (207, "Nigeria", 206_139_000, 50, "Tropical", True),
]

for country in country_data:
    sql = "INSERT IGNORE INTO Country (country_id, name, population, health_quality_index, climate, borders_open) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, country)

db.commit()

create_research_lab_table_sql = """
CREATE TABLE IF NOT EXISTS Research_lab (
    lab_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location INT NOT NULL,
    total_funding FLOAT,
    FOREIGN KEY (location) REFERENCES Country(country_id)
)
"""

cursor.execute(create_research_lab_table_sql)

research_lab_data = [
    ("301", "Kaspersky PathoLabs", 201, 1_000_000.00),
    ("302", "Lab Berkshire", 202, 2_000_000.00),
    ("303", "Chandrakant Labs for Pathogen Research", 203, 1_500_000.00),
    ("304", "Avery Institute for Biological Sciences", 204, 3_000_000.00),
    ("305", "Indian Institute of Science", 205, 2_500_000.00),
    ("306", "Center for Computational Natural Sciences & Bioinformatics, IIIT Hyderabad", 206, 1_200_000.00),
]

for lab in research_lab_data:
    sql = "INSERT IGNORE INTO Research_lab (lab_id, name, location, total_funding) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, lab)

db.commit()

create_research_project_table_sql = """
CREATE TABLE IF NOT EXISTS Research_project (
    project_id VARCHAR(255) PRIMARY KEY,
    pathogen_id VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    current_status VARCHAR(255),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_research_project_table_sql)

populate_research_project_table_sql = """
INSERT IGNORE INTO Research_project (project_id, pathogen_id, start_date, end_date, current_status)
VALUES
('proj_001', '101', '2023-01-01', '2023-12-31', 'ongoing'),
('proj_002', '102', '2022-05-15', '2023-05-14', 'completed'),
('proj_003', '103', '2023-03-01', NULL, 'ongoing'),
('proj_004', '104', '2021-07-20', '2022-07-19', 'completed'),
('proj_005', '105', '2023-06-01', NULL, 'ongoing'),
('proj_006', '101', '2022-01-01', '2022-12-31', 'completed'),
('proj_007', '102', '2023-02-01', NULL, 'ongoing');
"""

cursor.execute(populate_research_project_table_sql)

db.commit()

create_government_response_table_sql = """
CREATE TABLE IF NOT EXISTS Government_response (
    response_id VARCHAR(255) PRIMARY KEY,
    country_id INT NOT NULL,
    date_implemented DATE NOT NULL,
    response_type ENUM('Quarantine', 'TravelBan', 'SocialDistancing', 'VaccinationProgram', 'HumanitarianProgrammes') NOT NULL,
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
)
"""

cursor.execute(create_government_response_table_sql)

populate_government_response_table_sql = """
INSERT IGNORE INTO Government_response (response_id, country_id, date_implemented, response_type)
VALUES
('resp_001', '201', '2023-01-15', 'Quarantine'),
('resp_002', '202', '2023-02-01', 'Travel Ban'),
('resp_003', '203', '2023-03-10', 'Social Distancing'),
('resp_004', '203', '2023-04-05', 'Vaccination Program'),
('resp_005', '205', '2023-05-20', 'Humanitarian Programmes');
"""

cursor.execute(populate_government_response_table_sql)

db.commit()

create_vaccine_table_sql = """
CREATE TABLE IF NOT EXISTS Vaccine (
    vaccine_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    date_discovered DATE NOT NULL,
    effectiveness INT NOT NULL CHECK (effectiveness BETWEEN 0 AND 100),
    number_of_administrations INT NOT NULL,
    number_of_doses INT NOT NULL,
    side_effects ENUM('None', 'Mild', 'Severe') NOT NULL,
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id)
)
"""

cursor.execute(create_vaccine_table_sql)

populate_vaccine_table_sql = """
INSERT IGNORE INTO Vaccine (vaccine_id, name, project_id, date_discovered, effectiveness, number_of_administrations, number_of_doses, side_effects)
VALUES
('vac_001', 'Vaccine A', 'proj_001', '2023-02-01', 90, 1000000, 2, 'Mild'),
('vac_002', 'Vaccine B', 'proj_002', '2023-03-15', 85, 500000, 1, 'None'),
('vac_003', 'Vaccine C', 'proj_003', '2023-04-10', 95, 750000, 2, 'Severe'),
('vac_004', 'Vaccine D', 'proj_004', '2023-05-20', 80, 300000, 1, 'Mild'),
('vac_005', 'Vaccine E', 'proj_005', '2023-06-25', 70, 200000, 2, 'None');
"""

cursor.execute(populate_vaccine_table_sql)

db.commit()

create_global_vaccine_distribution_table_sql = """
CREATE TABLE IF NOT EXISTS Global_vaccine_distribution (
    vaccine_id VARCHAR(255),
    response_id VARCHAR(255),
    exporter_id INT,
    importer_id INT,
    doses_distributed INT NOT NULL,
    coverage_percentage DECIMAL(5,2) NOT NULL CHECK (coverage_percentage BETWEEN 0 AND 100),
    PRIMARY KEY (vaccine_id, response_id, exporter_id, importer_id),
    FOREIGN KEY (vaccine_id) REFERENCES Vaccine(vaccine_id),
    FOREIGN KEY (response_id) REFERENCES Government_response(response_id),
    FOREIGN KEY (exporter_id) REFERENCES Country(country_id),
    FOREIGN KEY (importer_id) REFERENCES Country(country_id)
)
"""

cursor.execute(create_global_vaccine_distribution_table_sql)

populate_global_vaccine_distribution_table_sql = """
INSERT IGNORE INTO Global_vaccine_distribution (vaccine_id, response_id, exporter_id, importer_id, doses_distributed, coverage_percentage)
VALUES
('vac_001', 'resp_001', 201, 202, 500000, 75.00),
('vac_002', 'resp_002', 202, 203, 300000, 60.00),
('vac_003', 'resp_003', 203, 204, 450000, 80.00),
('vac_004', 'resp_004', 204, 205, 200000, 50.00),
('vac_005', 'resp_005', 205, 206, 350000, 70.00),
('vac_001', 'resp_003', 201, 207, 250000, 65.00);
"""

cursor.execute(populate_global_vaccine_distribution_table_sql)

db.commit()

create_vaccine_distribution_cost = """
CREATE TABLE IF NOT EXISTS Vaccine_distribution_cost (
    vaccine_id VARCHAR(255),
    exporter_id INT,
    distribution_cost_per_country INT NOT NULL,
    PRIMARY KEY (vaccine_id, exporter_id),
    FOREIGN KEY (vaccine_id) REFERENCES Vaccine(vaccine_id),
    FOREIGN KEY (exporter_id) REFERENCES Country(country_id)
)
"""

cursor.execute(create_vaccine_distribution_cost)

populate_vaccine_distribution_cost_sql = """
INSERT IGNORE INTO Vaccine_distribution_cost (vaccine_id, exporter_id, distribution_cost_per_country)
VALUES
('vac_001', 201, 10000),
('vac_002', 202, 15000),
('vac_003', 203, 12000),
('vac_004', 204, 18000),
('vac_005', 205, 20000);
"""

cursor.execute(populate_vaccine_distribution_cost_sql)

db.commit()

create_vaccine_development = """
CREATE TABLE IF NOT EXISTS Vaccine_development (
    vaccine_id VARCHAR(255),
    project_id VARCHAR(255),
    pathogen_id VARCHAR(255),
    PRIMARY KEY (vaccine_id, project_id, pathogen_id),
    FOREIGN KEY (vaccine_id) REFERENCES Vaccine(vaccine_id),
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_vaccine_development)

populate_vaccine_development_sql = """
INSERT IGNORE INTO Vaccine_development (vaccine_id, project_id, pathogen_id)
VALUES
('vac_001', 'proj_001', '101'),
('vac_002', 'proj_002', '102'),
('vac_003', 'proj_003', '103'),
('vac_004', 'proj_004', '104'),
('vac_005', 'proj_005', '105');
"""

cursor.execute(populate_vaccine_development_sql)

db.commit()

create_research_focus = """
CREATE TABLE IF NOT EXISTS Research_focus (
    lab_id VARCHAR(255),
    project_id VARCHAR(255),
    pathogen_id VARCHAR(255),
    PRIMARY KEY (lab_id, project_id, pathogen_id),
    FOREIGN KEY (lab_id) REFERENCES Research_lab(lab_id),
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_research_focus)

populate_research_focus_sql = """
INSERT IGNORE INTO Research_focus (lab_id, project_id, pathogen_id)
VALUES
('301', 'proj_001', '101'),
('302', 'proj_002', '102'),
('303', 'proj_003', '103'),
('304', 'proj_004', '104'),
('305', 'proj_005', '105'),
('306', 'proj_006', '101'),
('301', 'proj_007', '102'),
('302', 'proj_001', '101');
"""

cursor.execute(populate_research_focus_sql)

db.commit()

create_resistance_sql = """
CREATE TABLE IF NOT EXISTS Resistance (
    pathogen_id VARCHAR(255),
    medium varchar(255),
    resistance_level INT NOT NULL CHECK (resistance_level BETWEEN 0 AND 100),
    PRIMARY KEY (pathogen_id, medium),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_resistance_sql)

db.commit()

populate_resistance_sql = """
INSERT IGNORE INTO Resistance (pathogen_id, medium, resistance_level)
VALUES
('101', 'Air', 20),
('101', 'Water', 30),
('101', 'Blood', 40),
('101', 'Droplet', 50),
('101', 'Contact', 60),
('101', 'Sexual', 70),
('102', 'Air', 30),
('102', 'Water', 40),
('102', 'Blood', 50),
('102', 'Droplet', 60),
('102', 'Contact', 70),
('102', 'Sexual', 80),
('103', 'Air', 40),
('103', 'Water', 50),
('103', 'Blood', 60),
('103', 'Droplet', 70),
('103', 'Contact', 80),
('103', 'Sexual', 90),
('104', 'Air', 50),
('104', 'Water', 60),
('104', 'Blood', 70),
('104', 'Droplet', 80),
('104', 'Contact', 90),
('104', 'Sexual', 100),
('105', 'Air', 60),
('105', 'Water', 70),
('105', 'Blood', 80),
('105', 'Droplet', 90),
('105', 'Contact', 100),
('105', 'Sexual', 10);
"""

cursor.execute(populate_resistance_sql)

db.commit()

create_research_aim_sql = """
CREATE TABLE IF NOT EXISTS Research_aim (
    project_id VARCHAR(255) PRIMARY KEY,
    research_aim VARCHAR(255) NOT NULL,
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id)
)
"""

cursor.execute(create_research_aim_sql)

populate_research_aim_sql = """
INSERT IGNORE INTO Research_aim (project_id, research_aim)
VALUES
('proj_001', 'Developing a vaccine for Influenza A'),
('proj_002', 'Developing a vaccine for Mycobacterium tuberculosis'),
('proj_003', 'Developing a vaccine for Plasmodium falciparum'),
('proj_004', 'Developing a vaccine for Candida albicans'),
('proj_005', 'Developing a vaccine for Ebola virus'),
('proj_006', 'Developing a vaccine for Influenza A'),
('proj_007', 'Developing a vaccine for Mycobacterium tuberculosis');
"""

cursor.execute(populate_research_aim_sql)

db.commit()

create_milestones_sql = """
CREATE TABLE IF NOT EXISTS Milestones (
    project_id VARCHAR(255) PRIMARY KEY,
    milestone VARCHAR(255) NOT NULL,
    date_achieved DATE NOT NULL,
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id)
)
"""

cursor.execute(create_milestones_sql)

populate_milestones_sql = """
INSERT IGNORE INTO Milestones (project_id, milestone, date_achieved)
VALUES
('proj_001', 'Vaccine A discovered', '2023-02-01'),
('proj_002', 'Vaccine B discovered', '2023-03-15'),
('proj_003', 'Vaccine C discovered', '2023-04-10'),
('proj_004', 'Vaccine D discovered', '2023-05-20'),
('proj_005', 'Vaccine E discovered', '2023-06-25'),
('proj_006', 'Vaccine A discovered', '2023-02-01'),
('proj_007', 'Vaccine B discovered', '2023-03-15');
"""

cursor.execute(populate_milestones_sql)

db.commit()

create_country_response_to_pathogen_sql= """
CREATE TABLE IF NOT EXISTS Country_response_to_pathogen (
    country_id INT,
    project_id VARCHAR(255),
    pathogen_id VARCHAR(255),
    PRIMARY KEY (country_id, project_id, pathogen_id),
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_country_response_to_pathogen_sql)

populate_country_response_to_pathogen_sql = """
INSERT IGNORE INTO Country_response_to_pathogen (country_id, project_id, pathogen_id)
VALUES
(201, 'proj_001', '101'),
(202, 'proj_002', '102'),
(203, 'proj_003', '103'),
(204, 'proj_004', '104'),
(205, 'proj_005', '105'),
(206, 'proj_006', '101'),
(207, 'proj_007', '102');
"""

cursor.execute(populate_country_response_to_pathogen_sql)

db.commit()

create_project_under_lab_sql= """
CREATE TABLE IF NOT EXISTS Project_under_lab (
    lab_id VARCHAR(255),
    project_id VARCHAR(255),
    funding_allocated INT NOT NULL,
    PRIMARY KEY (lab_id, project_id),
    FOREIGN KEY (lab_id) REFERENCES Research_lab(lab_id),
    FOREIGN KEY (project_id) REFERENCES Research_project(project_id)
)
"""

cursor.execute(create_project_under_lab_sql)

populate_project_under_lab_sql = """
INSERT IGNORE INTO Project_under_lab (lab_id, project_id, funding_allocated)
VALUES
('301', 'proj_001', 100000),
('302', 'proj_002', 200000),
('303', 'proj_003', 150000),
('304', 'proj_004', 300000),
('305', 'proj_005', 250000),
('306', 'proj_006', 120000),
('301', 'proj_007', 150000);
"""

cursor.execute(populate_project_under_lab_sql)

create_infection_sql= """
CREATE TABLE IF NOT EXISTS Infection (
    pathogen_id VARCHAR(255),
    country_id INT,
    first_case_date DATE NOT NULL,
    total_infected INT NOT NULL,
    total_death INT NOT NULL,
    PRIMARY KEY (pathogen_id, country_id),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id),
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
)
"""

cursor.execute(create_infection_sql)

populate_infection_sql = """
INSERT IGNORE INTO Infection (pathogen_id, country_id, first_case_date, total_infected, total_death)
VALUES
('101', 201, '2023-01-01', 1000, 100),
('102', 202, '2022-05-15', 500, 50),
('103', 203, '2023-03-01', 800, 80),
('104', 204, '2021-07-20', 400, 40),
('105', 205, '2023-06-01', 300, 30),
('101', 206, '2022-01-01', 200, 20),
('102', 207, '2023-02-01', 600, 60);
"""

cursor.execute(populate_infection_sql)

db.commit()

create_mutation_sql = """
CREATE TABLE IF NOT EXISTS Mutation (
    mutation_id VARCHAR(255) PRIMARY KEY,
    parent_pathogen_id VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    FOREIGN KEY (parent_pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_mutation_sql)

def insert_pathogen(pathogen_id, scientific_name, type, lethality_rate, transmission_method, predecessor, incubation_period, mutation_probability):
    pathogen_sql = """
    INSERT IGNORE INTO Pathogen (id, scientific_name, type, lethality_rate, transmission_method, predecessor, incubation_period, mutation_probability)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(pathogen_sql, (pathogen_id, scientific_name, type, lethality_rate, transmission_method, predecessor, incubation_period, mutation_probability))

def insert_mutation(mutation_id, parent_pathogen_id, year, month, day):
    mutation_sql = """
    INSERT IGNORE INTO Mutation (mutation_id, parent_pathogen_id, year, month, day)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(mutation_sql, (mutation_id, parent_pathogen_id, year, month, day))

mutated_pathogens_data = [
    ("106", "Mutation A", "Virus", 0.25, "Airborne", None, 10, 0.05),
    ("107", "Mutation B", "Bacteria", 0.45, "Airborne", None, 20, 0.04),
    ("108", "Mutation C", "Protozoa", 0.15, "Bloodborne", None, 12, 0.10),
    ("109", "Mutation D", "Fungus", 0.08, "Contact", None, 7, 0.12),
    ("110", "Mutation E", "Virus", 45.00, "Contact", None, 21, 0.25),
]

for mutated_pathogen in mutated_pathogens_data:
    insert_pathogen(*mutated_pathogen)

mutations_data = [
    ("106/101", "101", 2023, 1, 1),
    ("107/102", "102", 2022, 5, 15),
    ("108/103", "103", 2023, 3, 1),
    ("109/104", "104", 2021, 7, 20),
    ("110/105", "105", 2023, 6, 1),
]

for mutation in mutations_data:
    insert_mutation(*mutation)


#0f0 add the new table 'Response_effect' and populate it    # done?

create_response_effect_sql = """
CREATE TABLE IF NOT EXISTS Response_effect (
    response_id VARCHAR(255) NOT NULL,
    pathogen_id VARCHAR(255) NOT NULL,
    response_severity ENUM('Low', 'Mid', 'High') NOT NULL,
    effectiveness_rate INT NOT NULL CHECK (effectiveness_rate BETWEEN 0 AND 100),
    PRIMARY KEY (response_id, pathogen_id),
    FOREIGN KEY (response_id) REFERENCES Government_response(response_id),
    FOREIGN KEY (pathogen_id) REFERENCES Pathogen(id)
)
"""

cursor.execute(create_response_effect_sql)

response_effect_data = [
    ('resp_001', '101', 'High', 85),
    ('resp_002', '102', 'Mid', 60),
    ('resp_003', '103', 'Low', 40),
    ('resp_004', '104', 'High', 90),
    ('resp_005', '105', 'Mid', 70)
]

def insert_response_effect(response_id, pathogen_id, response_severity, effectiveness_rate):
    pathogen_sql = """
    INSERT IGNORE INTO Response_effect (response_id, pathogen_id, response_severity, effectiveness_rate)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(pathogen_sql, (response_id, pathogen_id, response_severity, effectiveness_rate))

for response_eff in response_effect_data:
    insert_response_effect(*response_eff)

db.commit()

db.close()