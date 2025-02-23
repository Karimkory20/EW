from flask import Flask, jsonify, request, render_template, send_from_directory
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure necessary folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data(filepath):
    try:
        if filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        elif filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            return None, "Invalid file type."
        return df, None
    except FileNotFoundError:
        return None, "File not found."
    except Exception as e:
        return None, f"Error reading file: {e}"

data_df = None  # Initialize data_df

def refresh_data():
    global data_df
    try:
        data_df, error = load_data(os.path.join(app.config['UPLOAD_FOLDER'], 'data.xlsx'))  # or data.csv
        if error:
            print(error)
    except FileNotFoundError:
        print("No data file found.")

refresh_data()  # Load initial data.

@app.route('/')
def index():
    return render_template('index.html')  # ✅ This will now correctly load your UI

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        refresh_data()  # Reload data
        return 'File uploaded successfully!'
    else:
        return "Invalid file type. Please use .xlsx or .csv."

@app.route('/performance/<member_id>', methods=['GET'])
def get_performance(member_id):
    global data_df
    if data_df is None:
        return jsonify({'error': 'No data uploaded yet.'}), 400

    try:
        member_id = int(member_id)  # Ensure member_id is an integer.
        member_data = data_df[data_df['id'] == member_id]
        if not member_data.empty:
            performance = member_data.to_dict(orient='records')[0]  # Get first row as a dictionary.
            return jsonify(performance)
        else:
            return jsonify({'error': 'Member not found'}), 404
    except ValueError:
        return jsonify({'error': 'Invalid member ID'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)

