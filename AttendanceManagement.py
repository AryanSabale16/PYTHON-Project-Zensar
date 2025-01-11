import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import date, datetime
from decimal import Decimal
import mysql.connector

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",          
        port=3307,                  
        user="root",                
        password="Root",            
        database="avcoe"            
    )

# Custom JSON Encoder for handling special data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# HTTP request handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)  
            
            # Handle specific GET routes
            if self.path.startswith("/students/"):
                student_id = self.path.split("/")[-1]
                cursor.execute("SELECT * FROM Students WHERE StudentID = %s", (student_id,))
                result = cursor.fetchone()
            elif self.path.startswith("/students"):
                cursor.execute("SELECT * FROM Students")
                result = cursor.fetchall()
            elif self.path.startswith("/courses/"):
                course_id = self.path.split("/")[-1]
                cursor.execute("SELECT * FROM Courses WHERE CourseID = %s", (course_id,))
                result = cursor.fetchone()
            elif self.path.startswith("/courses"):
                cursor.execute("SELECT * FROM Courses")
                result = cursor.fetchall()
            elif self.path.startswith("/attendance/"):
                course_id = self.path.split("/")[-1]
                cursor.execute("SELECT * FROM Attendance WHERE CourseID = %s", (course_id,))
                result = cursor.fetchall()
            elif self.path.startswith("/attendance"):
                cursor.execute("SELECT * FROM Attendance")
                result = cursor.fetchall()
            else:
                # If no valid route is found, return a 404 error
                self.send_error(404, "Endpoint not found")
                return

            # If no results are found, return a 404 response
            if not result:
                response_body = json.dumps({"error": "Record not found"})
                self.send_response(404)  # Not Found
            else:
                response_body = json.dumps(result, cls=CustomJSONEncoder)
                self.send_response(200)  # OK
            
            # Send the response
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode())

        except mysql.connector.Error as db_error:
            self.send_error(500, f"Database error: {str(db_error)}")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length).decode())
            conn = get_db_connection()
            cursor = conn.cursor()

            if self.path == "/students":
                required_fields = ["FirstName", "LastName", "Email", "PhoneNumber"]
                missing_fields = [field for field in required_fields if field not in post_data]
                if missing_fields:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Missing fields: {', '.join(missing_fields)}"}).encode())
                    return

                cursor.execute(
                    "INSERT INTO Students (FirstName, LastName, Email, PhoneNumber) VALUES (%s, %s, %s, %s)",
                    (post_data['FirstName'], post_data['LastName'], post_data['Email'], post_data['PhoneNumber'])
                )
                message = "Student record added successfully."

            elif self.path == "/courses":
                required_fields = ["CourseName", "Instructor"]
                missing_fields = [field for field in required_fields if field not in post_data]
                if missing_fields:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Missing fields: {', '.join(missing_fields)}"}).encode())
                    return

                cursor.execute(
                    "INSERT INTO Courses (CourseName, Instructor) VALUES (%s, %s)",
                    (post_data['CourseName'], post_data['Instructor'])
                )
                message = "Course record added successfully."

            elif self.path == "/attendance":
                required_fields = ["StudentID", "CourseID", "AttendanceDate", "Status"]
                missing_fields = [field for field in required_fields if field not in post_data]
                if missing_fields:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Missing fields: {', '.join(missing_fields)}"}).encode())
                    return

                cursor.execute(
                    "INSERT INTO Attendance (StudentID, CourseID, AttendanceDate, Status) VALUES (%s, %s, %s, %s)",
                    (post_data['StudentID'], post_data['CourseID'], post_data['AttendanceDate'], post_data['Status'])
                )
                message = "Attendance record added successfully."

            conn.commit()
            response_body = json.dumps({"message": message})
            self.send_response(201)  # Created
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode())

        except mysql.connector.Error as db_error:
            self.send_error(500, f"Database error: {str(db_error)}")
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

# Function to start the HTTP server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
