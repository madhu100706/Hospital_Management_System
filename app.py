from flask import Flask , render_template, request,redirect , flash
from database import create_tables,get_db_connection

app = Flask(__name__)
app.secret_key = "hospital-management-secret-key"


create_tables()

@app.route("/")
def home():

    connection = get_db_connection()

    total_patients = connection.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    total_doctors = connection.execute(
        "SELECT COUNT(*) FROM doctors"
    ).fetchone()[0]

    total_appointments = connection.execute(
        "SELECT COUNT(*) FROM appointments"
    ).fetchone()[0]

    total_revenue = connection.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        WHERE payment_status = 'Paid'
        """
    ).fetchone()[0]


    recent_appointments = connection.execute(
    """
    SELECT
        patients.name AS patient_name,
        doctors.name AS doctor_name,
        appointments.appointment_date,
        appointments.appointment_time,
        appointments.status
    FROM appointments
    JOIN patients
        ON appointments.patient_id = patients.id
    JOIN doctors
        ON appointments.doctor_id = doctors.id
    ORDER BY appointments.id DESC
    LIMIT 5
    """
).fetchall()

    connection.close()

    return render_template(
        "index.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_revenue=total_revenue,
        recent_appointments=recent_appointments
    )


@app.route("/add-patient", methods=["GET", "POST"])
def add_patient():

    if request.method == "POST":

        name = request.form["name"].strip()
        age = request.form["age"].strip()
        gender = request.form["gender"]
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()

        # Validate patient name
        if not name:
            return render_template(
                "add_patient.html",
                error="Patient name cannot be empty."
            )

        # Validate age
        if not age.isdigit():
            return render_template(
                "add_patient.html",
                error="Age must contain numbers only."
            )

        age = int(age)

        if age < 0 or age > 120:
            return render_template(
                "add_patient.html",
                error="Age must be between 0 and 120."
            )

        # Validate gender
        if gender not in ["Male", "Female", "Other"]:
            return render_template(
                "add_patient.html",
                error="Please select a valid gender."
            )

        # Validate phone
        if not phone.isdigit() or len(phone) != 10:
            return render_template(
                "add_patient.html",
                error="Phone number must contain exactly 10 digits."
            )

        # If all validation passes, save to database
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO patients
            (name, age, gender, phone, address)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, age, gender, phone, address)
        )

        connection.commit()
        connection.close()

        flash("Patient registered successfully.")
        return redirect("/patients")

    return render_template("add_patient.html")

# seperate route to dispaly all patients

@app.route("/patients")
def patients():


    search = request.args.get("search", "")


    connection = get_db_connection()

    if search:
        patients_data = connection.execute(
            """
            SELECT *FROM patients
            WHERE name LIKE ? OR phone LIKE?
            """,
            (f"%{search}%" , f"%{search}%")
        ).fetchall()

    else:
        patients_data = connection.execute(
            "SELECT *FROM patients"
        ).fetchall()


    connection.close()

    return render_template(
        "patients.html",
        patients = patients_data,
        search = search
    )



@app.route("/add-doctor", methods=["GET", "POST"])
def add_doctor():

    if request.method == "POST":

        name = request.form["name"].strip()
        specialization = request.form["specialization"].strip()
        phone = request.form["phone"].strip()


        # Validate doctor name
        if not name:
            return render_template(
                "add_doctor.html",
                error="Doctor name cannot be empty."
            )

        # Validate specialization
        if not specialization:
            return render_template(
                "add_doctor.html",
                error="Specialization cannot be empty."
            )

        # Validate phone
        if not phone.isdigit() or len(phone) != 10:
            return render_template(
                "add_doctor.html",
                error="Phone number must contain exactly 10 digits."
            )

# save doctor data if validation passes
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO doctors
            (name, specialization, phone)
            VALUES (?, ?, ?)
            """,
            (name, specialization, phone)
        )

        connection.commit()
        connection.close()

        
        flash("Doctor added successfully.")
        return redirect("/doctors")

    return render_template("add_doctor.html")


@app.route("/doctors")
def doctors():

    connection = get_db_connection()

    doctors_data = connection.execute(
        "SELECT * FROM doctors"
    ).fetchall()

    connection.close()

    return render_template(
        "doctors.html",
        doctors=doctors_data
    )



@app.route("/add-appointment", methods=["GET", "POST"])
def add_appointment():

    connection = get_db_connection()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]

        # Check whether patient exists
        patient = connection.execute(
            "SELECT id FROM patients WHERE id = ?",
            (patient_id,)
        ).fetchone()

        if patient is None:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            doctors_data = connection.execute(
                "SELECT * FROM doctors"
            ).fetchall()

            connection.close()

            return render_template(
                "add_appointment.html",
                patients=patients_data,
                doctors=doctors_data,
                error="Selected patient does not exist."
            )

        # Check whether doctor exists
        doctor = connection.execute(
            "SELECT id FROM doctors WHERE id = ?",
            (doctor_id,)
        ).fetchone()

        if doctor is None:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            doctors_data = connection.execute(
                "SELECT * FROM doctors"
            ).fetchall()

            connection.close()

            return render_template(
                "add_appointment.html",
                patients=patients_data,
                doctors=doctors_data,
                error="Selected doctor does not exist."
            )

        # Save appointment
        connection.execute(
            """
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                doctor_id,
                appointment_date,
                appointment_time,
                "Scheduled"
            )
        )

        connection.commit()
        connection.close()

        flash("Appointment booked successfully.")
        return redirect("/appointments")

    patients_data = connection.execute(
        "SELECT * FROM patients"
    ).fetchall()

    doctors_data = connection.execute(
        "SELECT * FROM doctors"
    ).fetchall()

    connection.close()

    return render_template(
        "add_appointment.html",
        patients=patients_data,
        doctors=doctors_data
    )


@app.route("/appointments")
def appointments():

    connection = get_db_connection()

    appointments_data = connection.execute(
        """
        SELECT
            appointments.id,
            patients.name AS patient_name,
            doctors.name AS doctor_name,
            doctors.specialization,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.status

        FROM appointments

        JOIN patients
            ON appointments.patient_id = patients.id

        JOIN doctors
            ON appointments.doctor_id = doctors.id

        ORDER BY appointments.appointment_date,
                appointments.appointment_time
        """
    ).fetchall()

    connection.close()

    return render_template(
        "appointments.html",
        appointments=appointments_data
    )


@app.route("/add-bill", methods=["GET", "POST"])
def add_bill():

    connection = get_db_connection()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        amount = request.form["amount"].strip()
        payment_status = request.form["payment_status"]

        # Check whether patient exists
        patient = connection.execute(
            "SELECT id FROM patients WHERE id = ?",
            (patient_id,)
        ).fetchone()

        if patient is None:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            connection.close()

            return render_template(
                "add_bill.html",
                patients=patients_data,
                error="Selected patient does not exist."
            )

        # Validate amount
        try:
            amount = float(amount)
        except ValueError:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            connection.close()

            return render_template(
                "add_bill.html",
                patients=patients_data,
                error="Bill amount must be a valid number."
            )

        if amount <= 0:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            connection.close()

            return render_template(
                "add_bill.html",
                patients=patients_data,
                error="Bill amount must be greater than 0."
            )

        # Validate payment status
        if payment_status not in ["Paid", "Pending"]:
            patients_data = connection.execute(
                "SELECT * FROM patients"
            ).fetchall()

            connection.close()

            return render_template(
                "add_bill.html",
                patients=patients_data,
                error="Please select a valid payment status."
            )

        # Save bill
        connection.execute(
            """
            INSERT INTO bills
            (patient_id, amount, payment_status)
            VALUES (?, ?, ?)
            """,
            (patient_id, amount, payment_status)
        )

        connection.commit()
        connection.close()

        flash("Bill created successfully.")
        return redirect("/billing")

    patients_data = connection.execute(
        "SELECT * FROM patients"
    ).fetchall()

    connection.close()

    return render_template(
        "add_bill.html",
        patients=patients_data
    )

@app.route("/billing")
def billing():

    connection = get_db_connection()

    bills_data = connection.execute(
        """
        SELECT
            bills.id,
            patients.name AS patient_name,
            bills.amount,
            bills.payment_status

        FROM bills

        JOIN patients
            ON bills.patient_id = patients.id

        ORDER BY bills.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "billing.html",
        bills=bills_data
    )


if __name__ == "__main__":
    app.run(debug = True)