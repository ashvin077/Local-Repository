# app.py (Flask Server)

# import necessary modules
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import mysql.connector

# configuring SQL database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:yourSQLpassword@YourUserName/yourDatabaseName'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


# create a class to map a table in a relational database
# this should be same as the column names in your database table
class Users(db.Model):
    SN = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(50), nullable=False)
    Username = db.Column(db.String(30), unique=True, nullable=False)
    Email = db.Column(db.String(50), nullable=False)
    Password = db.Column(db.String(30), nullable=False)
    Mobile = db.Column(db.String(20), nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.String(10), nullable=False)
    Height = db.Column(db.Numeric(5, 2), nullable=False)
    Weight = db.Column(db.Numeric(5, 2), nullable=False)

    # Method to check password, weather it is correct or not
    def check_password(self, password):
        return bcrypt.check_password_hash(self.Password, password)


# another class for another table
class Caloriesrecord(db.Model):
    SN = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(20), nullable=False)
    LastWorkoutDuration = db.Column(db.Numeric(5, 2), nullable=False)
    CaloriesBurn = db.Column(db.Numeric(5, 2), nullable=False)
    Date = db.Column(db.Date, nullable=False)


# check for valid password and username of user, for login
@app.route('/api/login_data', methods=['POST'])
def login_data():
    data = request.json  # Get JSON data sent from app
    user_name = data['user_name']
    password = data['password']

    # Validate input
    if not user_name or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Find user in database
    user = Users.query.filter_by(Username=user_name).first()

    # Check if user exists and if password is correct
    if user and user.check_password(password):
        return jsonify({"success": True, 'message': 'Login successful'}), 200
    else:
        return jsonify({"success": False, 'error': 'Invalid username or password'}), 401


# post request to database for saving signUp data of user in database
@app.route('/api/signup_data', methods=['POST'])
def process_data():
    data = request.json  # Get JSON data sent from app

    new_password = data['new_password']

    # Creating new user with hashed password
    password_hash = bcrypt.generate_password_hash(data['confirm_password']).decode('utf-8')

    new_user = Users(
        Name=data['name'],
        Username=data['user_name'],
        Email=data['email'],
        Password=password_hash,
        Mobile=data['mobile_number'],
        DateOfBirth=data['date_of_birth'],
        Gender=data['gender'],
        Height=data['height'],
        Weight=data['weight']
    )
    db.session.add(new_user)
    db.session.commit()         # save all data to database

    return jsonify({
        'Name': new_user.Name,
        'Username': new_user.Username,
        'Email': new_user.Email,
        'New_password': new_password,
        'Password': new_user.Password,
        'Mobile': new_user.Mobile,
        'DateOfBirth': new_user.DateOfBirth,
        'Gender': new_user.Gender,
        'Height': new_user.Height,
        'Weight': new_user.Weight
    })


db_config = {
    'host': 'yourHost',
    'user': 'YourUserName',
    'password': 'YourPassword',
    'database': 'YourDatabaseName'
}


# accessing particular data from database
@app.route('/user_info/<username>', methods=['GET'])
def get_user_info(username):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT name, username, email, mobile, dateofbirth, gender, height, weight FROM users WHERE username = %s",
        (username,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404


# updating particular data in database from application
@app.route('/update', methods=['POST'])
def update_user():
    # Connect to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    data = request.json
    username = data.get('username')  # Username sent in the request
    height = data.get('height')
    weight = data.get('weight')

    # Validate inputs
    if not username or not height or not weight:
        return jsonify({"error": "Missing required data"}), 400

    try:
        # Update user data
        cursor.execute(
            "UPDATE users SET height = %s, weight = %s WHERE username = %s",
            (height, weight, username)
        )
        # Commit the changes
        connection.commit()
        # Check if any rows were updated
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "Height and weight updated successfully!"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        # Close the connection
        if connection.is_connected():
            cursor.close()
            connection.close()


# Update password or change password
@app.route('/updatePassword', methods=['POST'])
def update_password():
    # Connect to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    data = request.json
    username = data.get('username')
    password = data.get('password')
    new_password = data.get('confirm_password')

    # Find user in database
    user = Users.query.filter_by(Username=username).first()

    new_hash_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    # Check if user exists and if password is correct
    if user and user.check_password(password):
        try:
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s",
                (new_hash_password, username))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "User not found"}), 203

            return jsonify({"message": "Password Updated Successfully"}), 201

        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 204

        finally:
            # Close the connection
            if connection.is_connected():
                cursor.close()
                connection.close()

    else:
        return jsonify({"success": False, 'error': 'Old password did not matched'}), 202


# updating Calories data in database table
@app.route('/api/insertCaloriesData', methods=['POST'])
def insert_calories_data():
    data = request.json

    calories_data = Caloriesrecord(
        Username=data['username'],
        LastWorkoutDuration=data['total_exercise_time'],
        CaloriesBurn=data['calories_burn'],
        Date=data['date']
    )
    db.session.add(calories_data)
    db.session.commit()

    return jsonify({
        'Username': calories_data.Username,
        'LastWorkoutDuration': calories_data.LastWorkoutDuration,
        'CaloriesBurn': calories_data.CaloriesBurn,
        'Date': calories_data.Date
    })


# fetching calories data from database
@app.route('/fetchCaloriesData/<username>', methods=['GET'])
def fetch_calories_data(username):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT Date, CaloriesBurn FROM caloriesrecord WHERE Username = %s ORDER BY Date",
            (username,))
        records = cursor.fetchall()  # Fetch all matching records

        if records:
            # Convert data into a client-friendly format
            data = {
                'date': [record['Date'].strftime('%m-%d') for record in records],
                'caloriesburn': [record['CaloriesBurn'] for record in records]
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Database query error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
