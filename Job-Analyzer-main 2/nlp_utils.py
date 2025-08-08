import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def preprocess_text(text):
    """Clean and preprocess text for analysis"""
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(filtered_tokens)

def extract_skills(text, skill_keywords):
    """Extract skills from text based on a predefined list of skill keywords"""
    preprocessed_text = preprocess_text(text)
    found_skills = []
    
    for skill in skill_keywords:
        # Look for whole word matches
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, preprocessed_text):
            found_skills.append(skill)
            
    return found_skills

def calculate_similarity(text1, text2):
    """Calculate cosine similarity between two texts"""
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(similarity * 100, 2)  # Return as percentage
    except:
        return 0

def get_missing_skills(job_skills, resume_skills):
    """Identify skills in the job description that are missing from the resume"""
    return list(set(job_skills) - set(resume_skills))

# Common technical and soft skills for reference
TECHNICAL_SKILLS = [
    'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue', 
    'node', 'express', 'django', 'flask', 'sql', 'nosql', 'mongodb', 'mysql',
    'postgresql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'ci/cd',
    'machine learning', 'data science', 'ai', 'nlp', 'computer vision', 'tensorflow',
    'pytorch', 'pandas', 'numpy', 'scikit-learn', 'tableau', 'power bi'
]

SOFT_SKILLS = [
    'communication', 'teamwork', 'problem solving', 'critical thinking', 'leadership',
    'time management', 'adaptability', 'creativity', 'work ethic', 'interpersonal',
    'collaboration', 'flexibility', 'organization', 'self-motivation', 'conflict resolution',
    'decision making', 'stress management', 'attention to detail', 'customer service',
    'presentation skills', 'negotiation', 'mentoring', 'project management'
]
