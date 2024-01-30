from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import time


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None
current_caregiver = None

def is_strong_pass(password):
    print("pass is", password)
    if len(password) < 8:  # length >= 8
        return False
    if not (password.lower().islower() and any(c.isnumeric() for c in password)):  # contains letters and numbers
        return False
    if password.islower() or password.isupper():  # contains upper and lowercase
        return False
    if not any(c in password for c in '!@#?'):  # contains special
        return False
    return True

def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens needs to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if username already taken
    if username_exists_patient(username):
        print("Username taken, try again!")
        return
    if not is_strong_pass(password):
        print("Password too weak! Please make sure you meet the following criteria:\n-At least 8 characters.\n-A mix "
              "of letters and numbers.\n-A mix of both upper and lowercase.\n-At least one of the following special "
              "characters: !@#?")
        return
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)
    # save patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user", username)
    display_commands()


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return
    if not is_strong_pass(password):
        print("Password too weak! Please make sure you meet the following criteria:\n-At least 8 characters.\n-A mix "
              "of letters and numbers.\n-A mix of both upper and lowercase.\n-At least one of the following special "
              "characters: !@#?")
        return
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user", username)
    display_commands()


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
        return
    else:
        print("Logged in as: " + username)
        current_patient = patient
    display_commands()

def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
        return
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver
    display_commands()


def search_caregiver_schedule(tokens):
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    # Make sure it's the right token length
    if len(tokens) != 2:
        print("Please try again!")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()

    find_caregivers = "SELECT * FROM Availabilities, Vaccines WHERE Availabilities.Time = %s ORDER BY Availabilities.Username"

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        cursor = conn.cursor()
        d = datetime.datetime(year, month, day)
        cursor.execute(find_caregivers, d)
        print('[Availabilities on ' + date + ']')
        for row in cursor:
            print(row[1], row[2], row[3])
    except:
        print("Please try again!")
        return
    finally:
        cm.close_connection()
    display_commands()


def reserve(tokens):
    if len(tokens) != 3:
        print("Please try again!")
        return
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if current_patient is None:
        print("Please login as a patient!")
        return
    # Seeing if there are caregivers
    cm = ConnectionManager()
    conn = cm.create_connection()
    availability_info = "SELECT * FROM Availabilities, Vaccines WHERE Availabilities.Time = %s"

    date = tokens[1]
    vaccine_name = tokens[2]

    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        cursor = conn.cursor()
        d = datetime.datetime(year, month, day)
        cursor.execute(availability_info, d)
        returned_info = cursor.fetchall()
        available_caregivers = sorted({a[1] for a in returned_info})
        if len(available_caregivers) == 0:
            print("No Caregiver is available!")
            return
        enough_doses = False
        for row in returned_info:
            if row[2] == vaccine_name and row[3] > 0:
                enough_doses = True
        if not enough_doses:
            print("Not enough available doses!")
            return
        # Reservation is good to go
        reserved_caregiver = available_caregivers[0]
        appointment_id = int(time.time())
        print(f"Appointment ID: {appointment_id}, Caregiver username: {reserved_caregiver}")
        # app_id, date, vacc_name, care_user, patient_user
        reservation_info = (appointment_id, d, vaccine_name, reserved_caregiver, current_patient.get_username())
        add_app = "INSERT INTO Appointments VALUES (%s, %s, %s, %s, %s)"
        now_unavailable = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
        cursor = conn.cursor()
        cursor.execute(add_app, reservation_info)
        cursor.execute(now_unavailable, (d, reserved_caregiver))

        # must decrease doses
        vaccine = None
        try:
            vaccine = Vaccine(vaccine_name, 1).get()
        except pymssql.Error as e:
            print("Error occurred when decreasing doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when decreasing doses")
            print("Error:", e)
            return

        try:
            vaccine.decrease_available_doses(1)
        except pymssql.Error as e:
            print("Error occurred when decreasing doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when decreasing doses")
            print("Error:", e)
            return
        conn.commit()

    except:
        print("Please try again!")
        return
    finally:
        cm.close_connection()
    display_commands()

def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")
    display_commands()


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")
    display_commands()


def show_appointments(tokens):
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    if len(tokens) != 1:
        print("Please try again!")
        return
    cm = ConnectionManager()
    conn = cm.create_connection()

    if current_caregiver is not None:  # user is a caregiver
        show_apps = "SELECT * FROM Appointments WHERE Care_user = %s ORDER BY App_id"
        try:
            cursor = conn.cursor()
            cursor.execute(show_apps, current_caregiver.get_username())
            print('[Current appointments]')
            for row in cursor:
                print(row[0], row[2], row[1], row[4])
        except:
            print("Please try again! (caregiver error)")
            return
        finally:
            cm.close_connection()
    else:  # user is a patient
        show_apps = "SELECT * FROM Appointments WHERE Patient_user = %s ORDER BY App_id"
        try:
            cursor = conn.cursor()
            cursor.execute(show_apps, current_patient.get_username())
            print('[Current appointments]')
            for row in cursor:
                print(row[0], row[2], row[1], row[3])
        except:
            print("Please try again! (patient error)")
            return
        finally:
            cm.close_connection()
    display_commands()


def logout(tokens):
    if len(tokens) != 1:
        print("Please try again!")
        return
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    current_caregiver = None
    current_patient = None

    print("Successfully logged out!")
    display_commands()


def display_commands():
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")
    print("> reserve <date> <vaccine>")
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")
    print("> logout")
    print("> Quit")

def start():
    stop = False
    display_commands()
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break
        tokens = response.split(" ")

        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0].lower()
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(list(map(str.lower, tokens)))
        elif operation == "reserve":
            reserve(list(map(str.lower, tokens)))
        elif operation == "upload_availability":
            upload_availability(list(map(str.lower, tokens)))
        elif operation == cancel:
            cancel(list(map(str.lower, tokens)))
        elif operation == "add_doses":
            add_doses(list(map(str.lower, tokens)))
        elif operation == "show_appointments":
            show_appointments(list(map(str.lower, tokens)))
        elif operation == "logout":
            logout(list(map(str.lower, tokens)))
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()