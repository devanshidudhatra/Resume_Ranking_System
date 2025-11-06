import re
import html
from pdfminer.high_level import extract_text as pdf_extract_text
from bs4 import BeautifulSoup
import docx
import spacy
from spacy.matcher import DependencyMatcher
from spacy.matcher import PhraseMatcher


# Load the large spaCy model
nlp = spacy.load("en_core_web_lg")

# Constants for skills, education, and non-skill words
SKILLS_LIST = [
    # Programming Languages
    'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin',
    'Go', 'Rust', 'TypeScript', 'R', 'MATLAB', 'Scala', 'Perl', 'Shell', 'SQL',
    # Data Science & ML
    'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'NLP',
    'Data Analysis', 'Data Science', 'Data Visualization', 'Statistics', 'Big Data',
    'Data Mining', 'Neural Networks', 'AI', 'Artificial Intelligence', 
    'Predictive Modeling', 'Regression', 'Classification', 'Clustering',
    # Frameworks & Libraries
    'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy', 'SciPy',
    'Matplotlib', 'Seaborn', 'React', 'Angular', 'Vue.js', 'Flask', 'Django',
    'Spring', 'Express.js', 'Node.js', 'Bootstrap', 'jQuery',
    # Cloud & DevOps
    'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
    'Git', 'GitHub', 'GitLab', 'Terraform', 'Ansible', 'DevOps',
    # Databases
    'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQL Server', 'SQLite', 'NoSQL',
    'Redis', 'Elasticsearch', 'Firebase',
    # Soft Skills
    'Communication', 'Leadership', 'Project Management', 'Problem Solving',
    'Teamwork', 'Critical Thinking', 'Time Management', 'Creativity',
    # Other Technical Skills
    'Web Development', 'Mobile Development', 'UI/UX', 'Cybersecurity',
    'Blockchain', 'IoT', 'Agile', 'Scrum', 'RESTful API', 'GraphQL'
]

NON_SKILLS = [
    'and', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'a', 'an', 'with', 'by',
    'resume', 'curriculum', 'vitae', 'cv', 'contact', 'email', 'phone', 'address',
    'page', 'section', 'references', 'available', 'request', 'date', 'name',
    'summary', 'profile', 'objective', 'qualifications', 'interests', 'hobbies',
    'details', 'about', 'me', 'my', 'see', 'also', 'using', 'used', 'use', 
    'including', 'includes', 'included', 'please', 'thank', 'you', 'regards',
    'developed', 'created', 'managed', 'led', 'built', 'designed', 'implemented',
    'studied', 'learned', 'taught', 'responsible', 'www', 'http', 'https', 'com',
    'org', 'net', 'edu', 'year', 'month', 'day', 'week', 'quarter', 'semester'
]

DEGREE_TYPES = [
    'Bachelor', 'BSc', 'B.Sc.', 'BS', 'B.S.', 'BA', 'B.A.', 'B.E.', 'BBA', 'B.B.A.',
    'Master', 'MSc', 'M.Sc.', 'MS', 'M.S.', 'MA', 'M.A.', 'MBA', 'M.B.A.', 'M.E.', 'MEng',
    'Ph.D.', 'PhD', 'Doctorate', 'Doctoral', 'Postdoctoral', 'Postdoc',
    'Associate', 'A.A.', 'A.S.', 'A.A.S.',
    'Certificate', 'Certification', 'Diploma',
    'Bachelor of Science', 'Bachelor of Arts', 'Bachelor of Engineering', 'Bachelor of Business Administration',
    'Master of Science', 'Master of Arts', 'Master of Engineering', 'Master of Business Administration',
    'Doctor of Philosophy'
]

FIELDS_OF_STUDY = [
    'Computer Science', 'Information Technology', 'IT', 'Engineering', 'Business', 
    'Economics', 'Mathematics', 'Statistics', 'Physics', 'Chemistry', 'Biology',
    'Psychology', 'Sociology', 'Marketing', 'Finance', 'Accounting', 'Management',
    'Liberal Arts', 'Education', 'History', 'English', 'Communication', 'Media',
    'Journalism', 'Political Science', 'International Relations', 'Law',
    'Medicine', 'Nursing', 'Pharmacy', 'Health Sciences', 'Public Health',
    'Architecture', 'Design', 'Fine Arts', 'Performing Arts', 'Music',
    'Agriculture', 'Environmental Science', 'Sustainability', 'Philosophy',
    'Religious Studies', 'Linguistics', 'Languages', 'Anthropology',
    'Criminal Justice', 'Social Work', 'Human Resources', 'HR',
    'Electrical Engineering', 'Mechanical Engineering', 'Civil Engineering',
    'Chemical Engineering', 'Software Engineering', 'Data Science'
]

# Helper functions
def extract_text_from_pdf(file_path):
    """Extract plain text from PDF"""
    return pdf_extract_text(file_path)

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def extract_text(file_path):
    """Extract text based on file type"""
    file_extension = file_path.rsplit('.', 1)[1].lower()
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    return ""

def convert_to_html(file_path):
    """Convert document to HTML format using a simplified approach"""
    file_extension = file_path.rsplit('.', 1)[1].lower()
    text = extract_text(file_path)
    
    # Create simple HTML with paragraphs
    html_parts = ['<html><body>']
    for line in text.split('\n'):
        if line.strip():
            html_parts.append(f'<p>{html.escape(line)}</p>')
    html_parts.append('</body></html>')
    
    return ''.join(html_parts)

def is_valid_skill(skill):
    """Check if a given string is likely to be a valid skill"""
    # Strip leading/trailing whitespace and punctuation
    skill = skill.strip().strip('.,;:()[]{}')
    
    # If empty after stripping, not a valid skill
    if not skill:
        return False
    
    # Check length constraints (too short or too long probably isn't a skill)
    if len(skill) <= 1 or len(skill) > 30:
        return False
    
    # Check if it's in our non-skills list
    if skill.lower() in [ns.lower() for ns in NON_SKILLS]:
        return False
    
    # Check if it's just a number, date, or common formatting
    if re.match(r'^[\d\s\-\/\.]+$', skill):
        return False
    
    # Check if it's just punctuation or special characters
    if re.match(r'^[^\w\s]+$', skill):
        return False
    
    # Check for common non-skill patterns
    non_skill_patterns = [
        r'^[0-9]+(st|nd|rd|th)$',  # Ordinals like 1st, 2nd
        r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$',  # Month abbreviations
        r'^(www|http|https|ftp)',  # URLs
        r'^@',  # Social media handles
        r'^\d{1,2}/\d{1,2}/\d{2,4}$',  # Dates
        r'^\d{1,2}:\d{2}$',  # Times
        r'^\d+(h|hrs|hours|m|mins|minutes)$',  # Time durations
    ]
    
    for pattern in non_skill_patterns:
        if re.match(pattern, skill.lower()):
            return False
    
    return True

def clean_resume_text(text):
    """Cleans HTML, removes excessive whitespace, and aggressive filtering"""
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove extra newline characters and "[\u00a7]" artifacts
    text = re.sub(r'[\n\r\f]+', ' ', text)
    text = re.sub(r'\[\\u00a7\]', '', text)

    # Aggressively remove patterns with "cid:" and short lines
    text = re.sub(r'cid:\S+', '', text)
    text = '\n'.join(line for line in text.split('\n') if len(line.split()) > 3)
    return text


# Update extract_text functions to use clean_resume_text()

def extract_skills_from_html(html_content):
    """Skill extraction using SpaCy's PhraseMatcher"""
    doc = nlp(clean_resume_text(html_content))
    matcher = PhraseMatcher(nlp.vocab)
    
    # Create patterns from SKILLS_LIST
    patterns = [nlp(skill) for skill in SKILLS_LIST]
    matcher.add("SKILLS", patterns)
    
    # Extract matches
    skills = []
    for match_id, start, end in matcher(doc):
        span = doc[start:end]
        if span.text not in skills:
            skills.append(span.text)
    
    # Additional filtering
    return [skill for skill in skills if len(skill) > 2 and skill.lower() not in NON_SKILLS]

def extract_education_from_html(html_content):
    """Improved education extraction focusing on degree names rather than institutions using spaCy"""
    doc = nlp(html_content)
    education_info = []
    
    # Extract education entities using spaCy's named entity recognition
    for ent in doc.ents:
        if ent.label_ == "ORG" and any(degree.lower() in ent.text.lower() for degree in DEGREE_TYPES):
            education_info.append(ent.text.strip())
    
    # Extract education based on degree types
    for degree_type in DEGREE_TYPES:
        pattern = r'(?i)\b(' + re.escape(degree_type) + r'(?:\s+of\s+[A-Za-z]+)?(?:\s+in\s+[^,\.]*)?)'
        matches = re.findall(pattern, doc.text)
        for match in matches:
            if match and match not in education_info:
                education_info.append(match.strip())
    
    return education_info

def extract_experience_from_html(html_content):
    """Improved experience extraction from HTML content using spaCy"""
    doc = nlp(html_content)
    experience_info = []
    
    # Extract organizations as potential experience
    for ent in doc.ents:
        if ent.label_ == "ORG":
            experience_info.append(ent.text.strip())
    
    # Extract noun chunks that might represent job titles or roles
    for chunk in doc.noun_chunks:
        if len(chunk.text) > 10:
            experience_info.append(chunk.text.strip())
    
    # Filter out duplicates and irrelevant information
    final_experience = []
    seen = set()
    for exp in experience_info:
        exp_lower = exp.lower()
        if exp_lower not in seen and len(exp) > 5:
            seen.add(exp_lower)
            final_experience.append(exp)
    
    return final_experience

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}  # Define allowed extensions here
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
