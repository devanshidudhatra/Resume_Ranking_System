import os
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb+srv://heetdobariya07:uDR0Eeztg9NllZUy@cluster.yn4nj.mongodb.net/resume_analyzer?retryWrites=true&w=majority"
client = MongoClient(app.config["MONGO_URI"])
db = client.get_database()

# Collections
job_collection = db.job_descriptions
resume_collection = db.resumes
scores_collection = db.relevancy_scores

from extractor import (
    extract_text,
    convert_to_html,
    extract_skills_from_html,
    extract_education_from_html,
    extract_experience_from_html,
    allowed_file
)
from utils import load_job_descriptions_csv, save_job_description_csv, save_job_description_mongodb, load_job_descriptions_mongodb, save_relevancy_score_csv, save_relevancy_score_mongodb, load_relevancy_scores_csv, load_relevancy_scores_mongodb
from models import calculate_relevancy, interpret_score  # Placeholder for now

app.config['UPLOAD_FOLDER'] = 'data/resumes'
app.config['JOB_DESCRIPTIONS_FILE'] = 'data/job_descriptions.csv'
app.config['RELEVANCY_SCORES_FILE'] = 'data/relevancy_scores.csv'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize job descriptions (load from CSV)
job_descriptions = load_job_descriptions_mongodb()

# --- Utility Functions ---
def get_missing_requirements(extracted_data, required_data):
    missing = {}
    for key in required_data:
        extracted_set = set(extracted_data.get(key, []))
        required_set = set(required_data[key])
        missing[key] = list(required_set - extracted_set)
    return missing

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recruiter')
def recruiter_dashboard():
    return render_template('recruiter/dashboard.html', job_descriptions=job_descriptions)

@app.route('/applicant')
def applicant_dashboard():
    return render_template('applicant/dashboard.html', job_descriptions=job_descriptions)

@app.route('/recruiter/add_job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        job_id = str(uuid.uuid4())
        job_title = request.form['job_title']
        job_description = request.form['job_description']
        required_skills = [skill.strip() for skill in request.form['required_skills'].split(',')]
        required_education = [edu.strip() for edu in request.form['required_education'].split(',')]
        required_experience = [exp.strip() for exp in request.form['required_experience'].split(',')]

        job_data = {
            'job_id': job_id,
            'job_title': job_title,
            'job_description': job_description,
            'required_skills': required_skills,
            'required_education': required_education,
            'required_experience': required_experience
        }
        save_job_description_csv(app.config['JOB_DESCRIPTIONS_FILE'], job_data)
        save_job_description_mongodb(job_data)
        job_descriptions[job_id] = job_data  # Update in-memory data

        return redirect(url_for('recruiter_dashboard'))
    return render_template('recruiter/add_job.html')

@app.route('/applicant/upload_resume/<job_id>', methods=['POST'])
def upload_resume(job_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            html_content = convert_to_html(filepath)

            extracted_data = {
                'skills': extract_skills_from_html(html_content),
                'education': extract_education_from_html(html_content),
                'experience': extract_experience_from_html(html_content)
            }

            # Load job description
            job_description = job_descriptions.get(job_id)
            if not job_description:
                return jsonify({'error': 'Job description not found'}), 404

            required_data = {
                'skills': job_description['required_skills'],
                'education': job_description['required_education'],
                'experience': job_description['required_experience']
            }

            # Calculate Relevancy Score
            relevancy_score = calculate_relevancy(extracted_data, job_description)     # Using Calculate Relevancy
            interpret_relevancy_score = interpret_score(relevancy_score)
            missing_requirements = get_missing_requirements(extracted_data, required_data)
            resume_id = str(uuid.uuid4())
            
            # Save to CSV
            save_relevancy_score_csv(
                app.config['RELEVANCY_SCORES_FILE'],
                resume_id,
                job_id,
                relevancy_score,
                interpret_relevancy_score,
                extracted_data,
                missing_requirements
            )

            # Save to MongoDB
            save_relevancy_score_mongodb(
                resume_id,
                job_id,
                relevancy_score,
                interpret_relevancy_score,
                extracted_data,
                missing_requirements
            )

            return jsonify({
                'resume_id': resume_id,
                'relevancy_score': relevancy_score,
                'interpret_relevancy_score': interpret_relevancy_score,
                'extracted': extracted_data,
                'missing': missing_requirements
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        # finally:
            # if os.path.exists(filepath):
            #     os.remove(filepath)

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/recruiter/view_resumes/<job_id>')
def view_resumes(job_id):
    # Load relevancy scores from CSV
    relevancy_scores = load_relevancy_scores_csv(app.config['RELEVANCY_SCORES_FILE'])

    # Load job descriptions
    job_descriptions = load_job_descriptions_mongodb()

    job_description = job_descriptions.get(job_id)

    if not job_description:
        return jsonify({'error': 'Job not found'}), 404
    
    job_name = job_description.get('job_title', 'Unnamed Position')

    required_data = {
        'skills': job_description['required_skills'],
        'education': job_description['required_education'],
        'experience': job_description['required_experience']
    }

    job_scores = {}

    for resume_id, score_data in relevancy_scores.items():
        if score_data['job_id'] != job_id:
            continue

        extracted_data = score_data.get('extracted_data', {
            'skills': [],
            'education': [],
            'experience': []
        })

        missing = get_missing_requirements(extracted_data, required_data)

        job_scores[resume_id] = {
            'relevancy_score': score_data.get('relevancy_score', 0),
            'interpret_relevancy_score': score_data.get('interpret_relevancy_score', ''),
            'missing_skills': missing.get('skills', []),
            'missing_education': missing.get('education', []),
            'missing_experience': missing.get('experience', [])
        }

    return render_template(
        'recruiter/view_resumes.html',
        job_id=job_id,
        job_name=job_name,
        relevancy_scores=job_scores
    )

# --- Main ---
if __name__ == '__main__':
    app.run(debug=True)
