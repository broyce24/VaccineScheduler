CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Appointments (
	App_id int,
	Time date,
	vacc_name varchar(255) NOT NULL REFERENCES Vaccines,
	Care_user varchar(255) NOT NULL REFERENCES Caregivers,
	Patient_user varchar(255) NOT NULL REFERENCES Patients
	PRIMARY KEY (App_id)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) NOT NULL REFERENCES Caregivers,
    PRIMARY KEY (Time, Username)
);