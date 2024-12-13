from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file,flash,abort
from flask_mysqldb import MySQL
from datetime import datetime, date, timedelta
import csv
import bcrypt
import MySQLdb.cursors
import math
from os import getenv
import os
import hashlib
import uuid
import pytz

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.permanent_session_lifetime = timedelta(minutes=10)  # Auto logout after 10 minutes

# MySQL Configuration

app.config["MYSQL_HOST"] = getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = getenv("MYSQL_DB")
mysql = MySQL(app)

'''


app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "attendance_system"
mysql = MySQL(app)
'''


# College coordinates
COLLEGE_LAT = 23.1821179
COLLEGE_LON = 77.3018561   

MAX_DISTANCE_METERS = 150  # Radius of geofence in meters

def is_within_boundary(user_lat, user_lon):
    print(f"{user_lat} ,{user_lon}")
    """
    Check if a user's location is within the geofence radius of 150 meters.
    :param user_lat: Latitude of the user's location.
    :param user_lon: Longitude of the user's location.
    :return: True if within geofence, False otherwise.
    """
    R = 6371000  # Earth's radius in meters

    # Calculate differences in coordinates
    d_lat = math.radians(user_lat - COLLEGE_LAT)
    d_lon = math.radians(user_lon - COLLEGE_LON)
    lat1 = math.radians(COLLEGE_LAT)
    lat2 = math.radians(user_lat)

    # Haversine formula
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c  # Distance in meters

    # Check if distance is within the maximum allowed distance
    return distance <= MAX_DISTANCE_METERS



def generate_device_token():
    # Generating a device token using a unique device identifier (can be based on user agent, IP, etc.)
    device_id = str(uuid.uuid4())  # Unique device identifier (can be customized based on the device info)
    return hashlib.sha256(device_id.encode()).hexdigest()

def get_current_time():
    # Ensure the current time is naive (no timezone)
    return datetime.now()

@app.route("/")
def index():
    current_time = datetime.now().strftime("%H:%M")  # Format time as HH:MM
    return render_template("index.html")



@app.route('/location', methods=['POST'])
def location():
    # Simulate location error or success
    location_access = True  # Change to False to simulate denial

    if location_access:
        flash("Location fetched successfully!", "success")
    else:
        flash("Location access denied. Please enable it in browser settings.", "danger")

    return redirect(url_for('dashboard'))


@app.route('/view_attendance_page')
def view_attendance_page():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect if not logged in
    return render_template('view_attendance.html')

@app.route("/view_users")
def view_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY enrollment_no")  # Sorting by enrollment number
    users = cur.fetchall()
    cur.close()
    return render_template("view_users.html", users=users)

@app.route("/edit_user/<int:id>", methods=["GET", "POST"])
def edit_user(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (id,))
    user = cur.fetchone()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        branch = request.form["branch"]
        college_name = request.form["college_name"]

        cur.execute("""
            UPDATE users 
            SET name = %s, email = %s, mobile = %s, branch = %s, college_name = %s 
            WHERE id = %s
        """, (name, email, mobile, branch, college_name, id))
        mysql.connection.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("view_users"))
    
    cur.close()
    return render_template("edit_user.html", user=user)

@app.route("/delete_user/<int:id>", methods=["GET"])
def delete_user(id):
    try:
        cur = mysql.connection.cursor()

        # First, delete attendance records associated with the user
        cur.execute("DELETE FROM attendance WHERE user_id = %s", (id,))
        
        # Then, delete the user from the users table
        cur.execute("DELETE FROM users WHERE id = %s", (id,))
        
        # Commit the changes to the database
        mysql.connection.commit()

        flash("User deleted successfully!", "danger")
    except Exception as e:
        # If there is any error, roll back the transaction
        mysql.connection.rollback()
        flash(f"Error occurred: {e}", "danger")

    return redirect(url_for("view_users"))



@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/view_attendance', methods=['POST'])
def view_attendance():
    
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect to admin login if not logged in
    attendance_date = request.form.get('attendance_date')
    if not attendance_date:
        return jsonify({"error": "Please select a date"}), 400

    # Validate the selected date
    try:
        attendance_date_obj = datetime.strptime(attendance_date, "%Y-%m-%d").date()
        if attendance_date_obj > datetime.now().date():
            return jsonify({"error": "Wait for the next date"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    try:
        cur = mysql.connection.cursor()

        # Get all users sorted by enrollment_no
        cur.execute("SELECT id, name, enrollment_no FROM users")
        all_users = sorted(cur.fetchall(), key=lambda user: user[2])

        # Fetch attendance data for the selected date
        cur.execute("SELECT user_id, status FROM attendance WHERE date = %s", [attendance_date])
        attendance_records = cur.fetchall()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cur.close()

    # Create a dictionary of attendance statuses
    attendance_dict = {record[0]: record[1] for record in attendance_records}

    # Prepare response data
    attendance_display = [
        {
            "name": user[1],
            "enrollment_no": user[2],
            "status": attendance_dict.get(user[0], f"Absent")  #{attendance_date}
        }
        for user in all_users
    ]

    return jsonify(attendance_display)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Replace with your MySQL query to validate admin
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        admin = cur.fetchone()
        cur.close()

        if admin:
            session['admin_logged_in'] = True
            return redirect('/admin_dashboard')
        else:
            flash("Invalid Credentials", "danger")

    return render_template('admin_login.html')

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect if not logged in
    
    # Fetch the logged-in admin's username using the session
    admin_id = session.get("admin_logged_in")  # Assuming the admin's ID is stored in session
    cur = mysql.connection.cursor()
    cur.execute("SELECT username FROM admin WHERE id = %s", (admin_id,))
    admin_username = cur.fetchone()  # Fetch the username of the logged-in admin
    cur.close()

    # If admin username is found, pass it to the template
    if admin_username:
        username = admin_username[0]
    else:
        username = "Unknown"  # Fallback if no username is found
    
    # Fetch the total number of reports
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM reports")  # Count the total number of reports
    total_reports = cur.fetchone()[0]  # Get the count value
    cur.close()

    # Fetch the count of solved reports
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'solved'")
    solved_count = cur.fetchone()[0]
    cur.close()
      # Fetch total number of students from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM users")  # Query to get the total number of students
    total_students = cur.fetchone()[0]  # Fetch the count value
    cur.close()

    # Fetch the count of unsolved reports
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM reports WHERE status = 'unsolved'")
    unsolved_count = cur.fetchone()[0]
    cur.close()

    # Pass data to the template
    return render_template("admin_dashboard.html", 
                           username=username, 
                           total_reports=total_reports,
                           solved_count=solved_count,
                           unsolved_count=unsolved_count,total_students=total_students,current_date=date.today())

    

@app.route("/view_reports", methods=['GET', 'POST'])
def view_reports():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect if not logged in

    # Handle report status updates and deletions
    if request.method == 'POST':
        try:
            if 'status' in request.form:  # Handling status updates
                report_id = request.form.get('report_id')
                status = request.form.get('status')
                cur = mysql.connection.cursor()
                cur.execute("UPDATE reports SET status = %s WHERE id = %s", (status, report_id))
                mysql.connection.commit()
                cur.close()

            if 'delete' in request.form:  # Handling report deletion
                report_id = request.form.get('report_id')
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM reports WHERE id = %s", [report_id])
                mysql.connection.commit()
                cur.close()

        except Exception as e:
            print(f"Error updating or deleting report: {e}")

    # Fetch reports from the 'reports' table
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
        cur.execute("SELECT * FROM reports")
        reports = cur.fetchall()  # Fetch data as a list of dictionaries
        cur.close()

        # Debugging: Print the data in the terminal
        print("Fetched reports:", reports)
    except Exception as e:
        print("Error fetching reports:", e)
        reports = []

    return render_template("view_reports.html", reports=reports)



@app.route("/edit_student/<string:enrollment_no>", methods=["GET", "POST"])
def edit_student(enrollment_no):
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect if not logged in

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE enrollment_no = %s", (enrollment_no,))
    student = cur.fetchone()

    if request.method == "POST":
        # Get the updated data from the form
        name = request.form["name"]
        email = request.form["email"]
        mobile_number = request.form["mobile_number"]
        branch = request.form["branch"]
        college_name = request.form["college_name"]

        # Update the student data in the database
        cur.execute("""
            UPDATE users SET name = %s, email = %s, mobile = %s, branch = %s, college_name = %s 
            WHERE enrollment_no = %s
        """, (name, email, mobile_number, branch, college_name, enrollment_no))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for("admin_dashboard"))  # Redirect back to the dashboard

    cur.close()
    return render_template("edit_student.html", student=student)



@app.route('/admin_stats')
def admin_stats():
    
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect to admin login if not logged in
    # Fetch quick stats from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance")
    total_attendance = cur.fetchone()[0]

    cur.close()
    return jsonify({
        "total_users": total_users,
        "total_attendance": total_attendance
    })
    



@app.route('/admin_logout', methods=['GET'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin_login')


@app.before_request
def auto_mark_absent():
    current_time = datetime.now().strftime("%H:%M:%S")
    cutoff_time = "11:00:00"
    if current_time > cutoff_time:
        today_date = date.today()
        cur = mysql.connection.cursor()

        # Fetch all user IDs who haven't marked attendance today
        cur.execute("""
            SELECT id FROM users WHERE id NOT IN (
                SELECT user_id FROM attendance WHERE date = %s
            )
        """, [today_date])
        absent_users = cur.fetchall()

        # Mark them as "Absent" in attendance
        for user_id in absent_users:
            cur.execute("""
                INSERT INTO attendance (user_id, date, time, status)
                VALUES (%s, %s, %s, %s)
            """, (user_id[0], today_date, current_time, "Absent"))

        mysql.connection.commit()
        cur.close()

@app.route('/generate_report', methods=['POST'])
def generate_report():
    duration = request.form.get('report_duration')  # daily, monthly, or custom
    start_date = request.form.get('start_date')    # For custom reports
    end_date = request.form.get('end_date')

    cur = mysql.connection.cursor()

    # Query based on the selected duration
    if duration == 'daily':
        today_date = date.today()
        cur.execute(""" 
            SELECT u.name, u.enrollment_no, a.status, a.date 
            FROM attendance a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.date = %s
        """, [today_date])

    elif duration == 'monthly':
        month = request.form.get('month')  # Expected in 'YYYY-MM' format
        if not month:
            abort(400, description="Month parameter is required for monthly reports.")
        cur.execute("""
            SELECT u.name, u.enrollment_no, 
                   SUM(a.status = 'Present') AS days_present,
                   COUNT(a.id) AS total_classes
            FROM attendance a 
            JOIN users u ON a.user_id = u.id 
            WHERE DATE_FORMAT(a.date, '%%Y-%%m') = %s
            GROUP BY u.id
        """, [month])

    elif duration == 'custom' and start_date and end_date:
        cur.execute("""
            SELECT u.name, u.enrollment_no, a.status, a.date 
            FROM attendance a 
            JOIN users u ON a.user_id = u.id 
            WHERE a.date BETWEEN %s AND %s
        """, (start_date, end_date))

    else:
        abort(400, description="Invalid duration or missing required parameters.")

    records = cur.fetchall()
    cur.close()

    # Prepare filename with dynamic month name (if applicable)
    if duration == 'monthly':
        month_name = datetime.strptime(month, '%Y-%m').strftime('%B_%Y')  # e.g., "December_2024"
        csv_filename = f"attendance_report_{month_name}.csv"
    else:
        csv_filename = "attendance_report.csv"

    # Save the CSV file to a specific path (ensuring correct permissions)
    file_path = os.path.join(os.getcwd(), csv_filename)  # Save to current directory

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        if duration == 'daily':
            # Write headers and data for daily reports
            writer.writerow(['Name', 'Enrollment Number', 'Status', 'Date'])
            present_count = 0
            total_students = len(records)

            for record in records:
                writer.writerow(record)
                if record[2].lower() == 'present':  # Assuming status is 'Present' or 'Absent'
                    present_count += 1

            absent_count = total_students - present_count
            writer.writerow([])  # Blank row
            writer.writerow(['Summary'])
            writer.writerow(['Total Students', total_students])
            writer.writerow(['Present', present_count])
            writer.writerow(['Absent', absent_count])

        elif duration == 'monthly':
            # Write headers and data for monthly reports
            writer.writerow(['Name', 'Enrollment Number', 'Days Present', 'Total Classes'])
            for record in records:
                writer.writerow(record)

        elif duration == 'custom':
            # Write headers and data for custom date range reports
            writer.writerow(['Name', 'Enrollment Number', 'Status', 'Date'])
            for record in records:
                writer.writerow(record)

    # Ensure the file exists before attempting to send it
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found. Please try again.", 404

@app.route('/generate_report_page', methods=['GET'])
def generate_report_page():
    # Render a separate template for the report generation page
    return render_template('generate_report.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if "admin_logged_in" not in session:
        return redirect(url_for("admin_login"))  # Redirect to admin login if not logged in

    if request.method == "POST":
        # Get data from the form
        name = request.form["name"]
        enrollment_no = request.form["enrollment_no"]
        email = request.form["email"]
        mobile_number = request.form["mobile_number"]
        branch = request.form["branch"]
        college_name = request.form["college_name"]
        password = bcrypt.hashpw(request.form["password"].encode("utf-8"), bcrypt.gensalt())

        # Insert the user data into the database
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO users (name, enrollment_no, email, mobile, branch, college_name, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, enrollment_no, email, mobile_number, branch, college_name, password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for("admin_dashboard"))  # Redirect to admin dashboard after successful registration
    
    return render_template("register.html")  # Render the registration form if it's a GET request

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        enrollment_no = request.form["enrollment_no"]
        password = request.form["password"].encode("utf-8")

        # Generate a more unique device token using IP and User-Agent
        device_info = f"{request.remote_addr}_{request.headers.get('User-Agent')}"
        device_token = hashlib.sha256(device_info.encode("utf-8")).hexdigest()

        # Check device cooldown
        cur = mysql.connection.cursor()
        cur.execute("SELECT last_logout_time FROM device_activity WHERE device_token = %s", [device_token])
        device_activity = cur.fetchone()
        cur.close()

        if device_activity:
            last_logout_time = device_activity[0]
            current_time = get_current_time()

            # Check if cooldown period has passed
            if last_logout_time:
                cooldown_end = last_logout_time + timedelta(minutes=15)
                if current_time < cooldown_end:
                    remaining_time = (cooldown_end - current_time).seconds // 60
                    flash(f"Login restricted. Try again in {remaining_time} minutes.", "danger")
                    print(f"Device {device_token} login restricted for {remaining_time} minutes.")
                    return redirect(url_for("user_login"))

        # Fetching user from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE enrollment_no = %s", [enrollment_no])
        user = cur.fetchone()
        cur.close()

        if user:
            db_password = user[7].encode("utf-8")  # Password in database

            # Check password validity
            if bcrypt.checkpw(password, db_password):
                # Successful login
                session["user_id"] = user[0]
                session["username"] = user[1]
                session["device_token"] = device_token  # Save device token to session

                flash("Login successful!", "success")
                return redirect(url_for("user_dashboard"))
            else:
                flash("Invalid credentials. Please try again.", "danger")
        else:
            flash("User not found!", "danger")

    return render_template("user_login.html")


# Logout route
@app.route("/logout")
def logout():
    if "user_id" in session:
        user_id = session["user_id"]
        device_token = session.get("device_token")  # Get device token from session

        # Debugging logs for logout
        print(f"Logging out user {user_id} from device {device_token}")

        # Update last_logout_time for the device in device_activity table
        cur = mysql.connection.cursor()
        current_time = get_current_time()
        cur.execute("""
            INSERT INTO device_activity (device_token, last_logout_time)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE last_logout_time = %s
        """, (device_token, current_time, current_time))
        mysql.connection.commit()
        cur.close()

        # Clear session data
        session.clear()
        flash("You have been logged out successfully.", "success")
        print(f"User {user_id} logged out successfully on device {device_token}.")
    else:
        flash("You are not logged in.", "danger")

    return redirect(url_for("user_login"))


@app.route("/user_view_attendance", methods=["POST"])
def user_view_attendance():
    if "user_id" in session:
        attendance_records = []  # List to store attendance records
        total_attendance = 0  # To store total attendance count
        total_present = 0  # To store total present count
        selected_date = date.today()  # Default to today
        start_date = None
        end_date = None

        action = request.form.get("action", "").strip()
        selected_date_str = request.form.get("attendance_date", "").strip()
        start_date_str = request.form.get("start_date", "").strip()
        end_date_str = request.form.get("end_date", "").strip()

        # Handle specific date selection
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()  # Convert string to date
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
                return redirect(url_for("user_view_attendance"))

        # Handle custom date range selection
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
                return redirect(url_for("user_view_attendance"))

        # Connect to the database
        try:
            cur = mysql.connection.cursor()

            if start_date and end_date:
                # Fetch attendance for the custom date range
                cur.execute("""
                    SELECT a.id, a.date, a.time, a.status, a.latitude, a.longitude, u.name, u.enrollment_no
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.user_id = %s AND a.date BETWEEN %s AND %s
                    ORDER BY a.date DESC
                """, (session["user_id"], start_date, end_date))
            else:
                # Query to fetch attendance for a user on a specific date
                cur.execute("""
                    SELECT a.id, a.date, a.time, a.status, a.latitude, a.longitude, u.name, u.enrollment_no
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.user_id = %s AND a.date = %s
                """, (session["user_id"], selected_date))

            attendance_records = cur.fetchall()

            # Manually convert rows to dictionaries for easier access (column names mapped to keys)
            column_names = [col[0] for col in cur.description]  # Get column names
            attendance_records = [{column: value for column, value in zip(column_names, row)} for row in attendance_records]

            # Calculate total attendance and present count
            total_attendance = len(attendance_records)
            total_present = sum(1 for record in attendance_records if record['status'] == 'Present')

            cur.close()
        except Exception as e:
            flash(f"Error fetching attendance data: {str(e)}", "danger")
            return redirect(url_for("user_dashboard"))

        return render_template(
            "user_dashboard.html", 
            username=session["username"], 
            current_date=date.today(), 
            selected_date=selected_date, 
            start_date=start_date,
            end_date=end_date,
            attendance_records=attendance_records,
            total_attendance=total_attendance, 
            total_present=total_present
        )

    return redirect(url_for("index"))


@app.route("/user_dashboard", methods=["GET", "POST"])
def user_dashboard():
    if "user_id" in session:  # Ensure user is logged in
        if request.method == "POST":
            user_lat = request.form.get("latitude", "").strip()
            user_long = request.form.get("longitude", "").strip()
            action = request.form.get("action", "").strip()  # "mark" or "unmark"

            # Validate latitude and longitude
            if not user_lat or not user_long or not user_lat.replace(".", "").isdigit() or not user_long.replace(".", "").isdigit():
                flash("Invalid latitude or longitude.", "danger")
                return redirect(url_for("user_dashboard"))

            user_lat = float(user_lat)
            user_long = float(user_long)

            # Check location boundary
            if not is_within_boundary(user_lat, user_long):
                flash("You are outside the allowed area for attendance.", "danger")
                return redirect(url_for("user_dashboard"))

            # Validate time (12 AM - 11:59 PM)
            current_hour = datetime.now().hour
            if current_hour < 0 or current_hour >= 24:
                flash("Attendance can only be marked between 12 AM and 11:59 PM.", "danger")
                return redirect(url_for("user_dashboard"))

            # Database operations
            try:
                cur = mysql.connection.cursor()

                if action == "mark":
                    # Check if attendance already exists for today
                    cur.execute("SELECT * FROM attendance WHERE user_id = %s AND date = %s",
                                (session["user_id"], date.today()))
                    attendance = cur.fetchone()

                    if attendance:
                        if attendance[4] == "Absent":  # Update status if marked absent
                            cur.execute("""UPDATE attendance SET status = 'Present' WHERE user_id = %s AND date = %s""",
                                        (session["user_id"], date.today()))
                            mysql.connection.commit()
                            flash("Attendance updated to Present.", "success")
                        else:
                            flash("Attendance already marked as Present.", "info")
                    else:
                        # Insert new attendance record
                        cur.execute("""INSERT INTO attendance (user_id, date, time, status, latitude, longitude)
                                       VALUES (%s, %s, %s, %s, %s, %s)""",
                                    (session["user_id"], date.today(), datetime.now().strftime("%H:%M:%S"),
                                     "Present", user_lat, user_long))
                        mysql.connection.commit()
                        flash("Attendance marked successfully as Present.", "success")

                elif action == "unmark":
                    # Unmark attendance (set status to 'Absent')
                    cur.execute("SELECT * FROM attendance WHERE user_id = %s AND date = %s",
                                (session["user_id"], date.today()))
                    attendance = cur.fetchone()

                    if attendance:
                        cur.execute("""UPDATE attendance SET status = 'Absent' WHERE user_id = %s AND date = %s""",
                                    (session["user_id"], date.today()))
                        mysql.connection.commit()
                        flash("Attendance marked as Absent.", "danger")
                    else:
                        flash("No attendance to unmark for today.", "info")

            except Exception as e:
                flash(f"Error processing attendance: {str(e)}", "danger")
            finally:
                cur.close()

        return render_template("user_dashboard.html", username=session["username"], current_date=date.today())

    return redirect(url_for("user_login"))


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("index"))  # Redirect to login if user is not logged in

    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validate input
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New password and confirm password do not match.", "danger")
            return redirect(url_for("change_password"))

        try:
            cur = mysql.connection.cursor()

            # Verify current password
            cur.execute("SELECT password FROM users WHERE id = %s", (session["user_id"],))
            user = cur.fetchone()
            if not user or not bcrypt.checkpw(current_password.encode("utf-8"), user[0].encode("utf-8")):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("change_password"))

            # Update with the new password
            hashed_new_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new_password, session["user_id"]))
            mysql.connection.commit()
            cur.close()

            flash("Password changed successfully.", "success")
            return redirect(url_for("user_dashboard"))

        except Exception as e:
            flash(f"Error while changing password: {str(e)}", "danger")
            return redirect(url_for("change_password"))

    return render_template("change_password.html")


@app.route("/report_issue", methods=["GET", "POST"])
def report_issue():
    if "user_id" not in session:
        return redirect(url_for("index"))  # Redirect to login if the user isn't authenticated
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        enrollment_number = request.form.get("enrollment_number", "").strip()
        problem_type = request.form.get("problem_type", "").strip()
        message = request.form.get("message", "").strip()

        # Validate input
        if not name or not enrollment_number or not problem_type or not message:
            flash("All fields are required.", "danger")
            return redirect(url_for("report_issue"))

        try:
            # Insert data into the reports table
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO reports (user_id, name, enrollment_number, date, problem_type, message) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session["user_id"], name, enrollment_number, date.today(), problem_type, message))
            mysql.connection.commit()
            cur.close()

            flash("Report submitted successfully.", "success")
            return redirect(url_for("user_dashboard"))
        except Exception as e:
            flash(f"Error submitting the report: {str(e)}", "danger")

    return render_template("report_issue.html")




@app.route('/attendance-data')
def attendance_data():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    # Query total classes and present classes
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_classes, 
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present_classes
        FROM attendance 
        WHERE user_id = %s
    """, (user_id,))
    result = cursor.fetchone()
    cursor.close()

    total_classes = result[0] or 0
    present_classes = result[1] or 0
    absent_classes = total_classes - present_classes

    return jsonify({
        'total_classes': total_classes,
        'present_classes': present_classes,
        'absent_classes': absent_classes
    })


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
