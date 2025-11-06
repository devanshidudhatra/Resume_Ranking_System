from pymongo import MongoClient
from dotenv import load_dotenv
import os
import csv
import os
import datetime

load_dotenv()

MONGO_URI = "mongodb+srv://heetdobariya07:uDR0Eeztg9NllZUy@cluster.yn4nj.mongodb.net/resume_analyzer?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.get_database()

job_collection = db.job_descriptions
resume_collection = db.resumes
scores_collection = db.relevancy_scores

import csv
import os

def load_job_descriptions_csv(filename):
    """Load job descriptions from a CSV file into a dictionary."""
    job_descriptions = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row['job_id']
                job_descriptions[job_id] = {
                    'job_id': job_id,
                    'job_title': row['job_title'],
                    'job_description': row['job_description'],
                    'required_skills': [skill.strip() for skill in row['required_skills'].split(',')],
                    'required_education': [edu.strip() for edu in row['required_education'].split(',')],
                    'required_experience': [exp.strip() for exp in row['required_experience'].split(',')]
                }
    return job_descriptions

def save_job_description_csv(filename, job_data):
    """Save a new job description to the CSV file."""
    file_exists = os.path.exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['job_id', 'job_title', 'job_description', 'required_skills', 'required_education', 'required_experience']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'job_id': job_data['job_id'],
            'job_title': job_data['job_title'],
            'job_description': job_data['job_description'],
            'required_skills': ','.join(job_data['required_skills']),
            'required_education': ','.join(job_data['required_education']),
            'required_experience': ','.join(job_data['required_experience'])
        })

def save_job_description_mongodb(job_data):
    """Save job description to MongoDB"""
    job_collection.update_one(
        {'job_id': job_data['job_id']},
        {'$set': job_data},
        upsert=True
    )

def load_job_descriptions_mongodb():
    """Load job descriptions from MongoDB"""
    return {job['job_id']: job for job in job_collection.find()}

def save_relevancy_score_csv(filename, resume_id, job_id, relevancy_score, interpret_relevancy_score, extracted_data, missing_data):
    """Save the relevancy score along with extracted and missing data to the CSV file."""
    file_exists = os.path.exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'resume_id', 'job_id', 'relevancy_score', 'interpret_relevancy_score',
            'extracted_skills', 'extracted_education', 'extracted_experience',
            'missing_skills', 'missing_education', 'missing_experience'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'resume_id': resume_id,
            'job_id': job_id,
            'relevancy_score': relevancy_score,
            'interpret_relevancy_score': interpret_relevancy_score,
            'extracted_skills': ','.join(extracted_data.get('skills', [])),
            'extracted_education': ','.join(extracted_data.get('education', [])),
            'extracted_experience': ','.join(extracted_data.get('experience', [])),
            'missing_skills': ','.join(missing_data.get('skills', [])),
            'missing_education': ','.join(missing_data.get('education', [])),
            'missing_experience': ','.join(missing_data.get('experience', []))
        })

def save_relevancy_score_mongodb(resume_id, job_id, relevancy_score, interpret_score, extracted_data, missing_data):
    """Save relevancy score to MongoDB"""
    score_data = {
        'resume_id': resume_id,
        'job_id': job_id,
        'relevancy_score': relevancy_score,
        'interpret_relevancy_score': interpret_score,
        'extracted_data': extracted_data,
        'missing_data': missing_data,
        'timestamp': datetime.datetime.utcnow()
    }
    scores_collection.insert_one(score_data)

def load_relevancy_scores_csv(filename):
    """Load relevancy scores from a CSV file."""
    relevancy_scores = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                resume_id = row['resume_id']
                relevancy_scores[resume_id] = {
                    'job_id': row['job_id'],
                    'relevancy_score': float(row['relevancy_score']),
                    'interpret_relevancy_score': row.get('interpret_relevancy_score', ''),
                    'extracted_data': {
                        'skills': [s.strip() for s in row.get('extracted_skills', '').split(',') if s],
                        'education': [e.strip() for e in row.get('extracted_education', '').split(',') if e],
                        'experience': [e.strip() for e in row.get('extracted_experience', '').split(',') if e]
                    },
                    'missing_skills': [s.strip() for s in row.get('missing_skills', '').split(',') if s],
                    'missing_education': [e.strip() for e in row.get('missing_education', '').split(',') if e],
                    'missing_experience': [e.strip() for e in row.get('missing_experience', '').split(',') if e]
                }
    return relevancy_scores

def load_relevancy_scores_mongodb(job_id=None):
    """Load relevancy scores from MongoDB"""
    query = {'job_id': job_id} if job_id else {}
    return list(scores_collection.find(query))
