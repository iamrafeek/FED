from flask import Flask, request, render_template,  jsonify
from sklearn.neighbors import KNeighborsClassifier
from datetime import datetime
import numpy as np
import sqlite3
import random
import shutil
import joblib
import cv2
import os
import re



# Ensure necessary directories exist
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')

# Load the face detector
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

app = Flask(__name__)
nimgs = 100  # Target number of images to capture
is_running = True


# Identify face using ML model
def identify_face(facearray):
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)


def extract_faces(img):
    """Extract the face from an image."""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = face_detector.detectMultiScale(gray, 1.2, 5, minSize=(20, 20))
        return face_points
    except Exception as e:
        print(f"Error in extract_faces: {e}")
        return []
    

def faces_cleaning(folder_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    images_with_faces = []
    images_without_faces = []

    # First, categorize images into those with and without faces
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(folder_path, filename)
            img = cv2.imread(img_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                if len(faces) > 0:
                    images_with_faces.append(filename)
                else:
                    images_without_faces.append(filename)

    # Ensure there is at least one face image to use for replacement
    if not images_with_faces:
        print("No face images found for replacement.")
        return

    # Replace each no-face image with a random face image
    for no_face_image in images_without_faces:
        source_image = random.choice(images_with_faces)  # Select a random face image
        source_path = os.path.join(folder_path, source_image)
        target_path = os.path.join(folder_path, no_face_image)

        # Delete the no-face image
        os.remove(target_path)

        # Copy the selected face image to the deleted image's name
        shutil.copy(source_path, target_path)
        print(f"Replaced {no_face_image} with a copy of {source_image}")


    
# A function which trains the model on all the faces available in faces folder
def train_model():
    faces = []
    labels = []
    userlist = os.listdir('static/faces')
    for user in userlist:
        for imgname in os.listdir(f'static/faces/{user}'):
            img = cv2.imread(f'static/faces/{user}/{imgname}')
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'static/face_recognition_model.pkl')




# Function to initialize the database and create a table if not exists
def init_db():
    with sqlite3.connect('attendance.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS detected_users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, user_number TEXT, name TEXT, detected_date TEXT, detected_time TEXT)''')
        conn.commit()

# Function to insert detected user information into the database
def insert_user(user_number, name, detected_date, detected_time):
    with sqlite3.connect('attendance.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO detected_users (user_number, name, detected_date, detected_time)
                          VALUES (?, ?, ?, ?)''', (user_number, name, detected_date, detected_time))
        conn.commit()
###############################################################################

@app.route('/')
def home():
    """Home Page."""
    return render_template('home.html')

@app.route('/test1')
def test():
    """Home Page."""
    return render_template('home.html')

# Our main Face Recognition functionality. 
# This function will run when we click on Take Attendance Button.
@app.route('/start', methods=['GET'])
def start():
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', mess='There is no trained model in the static folder. Please add a new face to continue.')

    init_db()  # Initialize the database and table
    cap = cv2.VideoCapture(0)
    ret = True

    while is_running:
        ret, frame = cap.read()
        if len(extract_faces(frame)) > 0:
            for face_rect in extract_faces(frame):
                (x, y, w, h) = face_rect
                cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
                cv2.rectangle(frame, (x, y), (x+w, y-40), (86, 32, 251), -1)
                face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
                identified_person = identify_face(face.reshape(1, -1))[0]
                parts = identified_person.split("_")  # Split the string by '_'
                Name = parts[0]  # The first part before '_'
                usernum = parts[1] 
                # Insert detected user information into the database
                current_date = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%H:%M:%S')
                insert_user(usernum, Name, current_date, current_time)

                cv2.putText(frame, f'{identified_person}', (x+5, y-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow('Attendance', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return render_template('home.html')



def get_next_user_id():
    """Get the next available user ID by finding the highest current user ID and adding one."""
    user_ids = []
    base_path = 'static/faces'
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    for directory in os.listdir(base_path):
        # Assuming directory names are in 'username_userid' format
        match = re.search(r'_([0-9]+)$', directory)
        if match:
            user_ids.append(int(match.group(1)))
    next_user_id = max(user_ids) + 1 if user_ids else 1  # Start from 1 if no users exist
    return next_user_id

@app.route('/add', methods=['POST'])
def add():
    """Add a new user and capture face images."""
    newusername = request.form['newusername']
    # Automatically assign a new user ID
    newuserid = get_next_user_id()
    userimagefolder = f'static/faces/{newusername}_{newuserid}'
    if not os.path.isdir(userimagefolder):
        os.makedirs(userimagefolder)
    
    i, j = 0, 0; 
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 20), 2)
            cv2.putText(frame, f'Images Captured: {i}/{nimgs}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 20), 2, cv2.LINE_AA)
            if j % 5 == 0 and i < nimgs:
                name = f'{newusername}_{i}.jpg'
                cv2.imwrite(os.path.join(userimagefolder, name), frame[y:y+h, x:x+w])
                i += 1
            j += 1
        if i >= nimgs:
            break
        cv2.imshow('Adding new User', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print('Cleaning Images')
    folder_path = 'static/faces'

    # List all entries in the folder
    entries = os.listdir(folder_path)

    # Iterate through each entry, update `f` if it's a directory
    for entry in entries:
        full_path = os.path.join(folder_path, entry)
        faces_cleaning(full_path)
    print('Training Model')
    train_model()
    # Flash a message to be displayed in the template
    return render_template('home.html')



DATABASE = 'attendance.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return conn

def get_latest_data():
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM detected_users;')
    data = cursor.fetchall()
    # Convert the list of rows into a list of dicts
    data_list = [dict(row) for row in data]
    conn.close()
    return data_list

@app.route('/index')
def index():
    return render_template('live.html')

@app.route('/get-data')
def get_data():
    data = get_latest_data()  # Fetch all data from the database
    return jsonify(data)


def query_db():
    conn = sqlite3.connect('attendance.db')
    cur = conn.cursor()
    query = """
    SELECT user_number, name, detected_date, MIN(detected_time), MAX(detected_time),
    (JULIANDAY(MAX(detected_time)) - JULIANDAY(MIN(detected_time))) * 24 * 60 AS spent_minutes
    FROM detected_users
    GROUP BY user_number, detected_date
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        user_number, name, detected_date, entry_time, exit_time, spent_minutes = row
        # Check if spent_minutes is less than 1, adjust exit_time and spent_minutes accordingly
        if spent_minutes < 1:
            exit_time = "0"
            spent_time = "0"
        else:
            spent_time = f"{spent_minutes:.2f} minutes"

        result.append({
            'user_number': user_number,
            'name': name,
            'detected_date': detected_date,
            'time_entry': entry_time,
            'time_exit': exit_time,
            'spent_time': spent_time
        })
    return result

@app.route('/user_details')
def attendence():
    return render_template('attendance.html')

@app.route('/get-data-atd')
def get_data_atd():
    data = query_db()
    return jsonify(data)

@app.route('/stop', methods=['GET'])
def stop():
    global is_running
    is_running = False
    return render_template('attendance.html')

if __name__ == '__main__':
    app.run(debug=True)
