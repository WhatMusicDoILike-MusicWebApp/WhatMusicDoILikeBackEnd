from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'test_user'
app.config['MYSQL_PASSWORD'] = 'test_password'
app.config['MYSQL_DB'] = 'backend'

mysql = MySQL(app)


# Using MySQLdb for INSERT
@app.route('/users', methods=['POST'])
def new_user():
    data = request.get_json()  # Get JSON payload from request

    userId = data.get('userId')
    name = data.get('name')
    email = data.get('email')

    if not userId or not name or not email:
        return jsonify({"error": "Missing required fields"}), 400
    
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    insert_query = "INSERT INTO users (userId, name, email, createdAt) VALUES (%s, %s, %s, %s)"
    
    try:
        cur = mysql.connection.cursor()
        cur.execute(insert_query, (userId, name, email, created_at))
        mysql.connection.commit()  # Commit transaction
        cur.close()
        return jsonify({"message": "User created successfully!", "userId": userId}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
