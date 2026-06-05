import os
import re
import spacy
import PyPDF2
from docx import Document

# Load spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    try:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"Spacy download failed: {e}")
        nlp = None
except Exception:
    nlp = None

class ResumeParser:
    @staticmethod
    def extract_text(file_path):
        """Extract text from PDF or DOCX file."""
        text = ""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
            elif ext == '.docx':
                doc = Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            return text.strip()
        except Exception as e:
            print(f"Extraction error: {e}")
            return ""

    @staticmethod
    def parse_skills(text):
        """Extract skills from text using a mixture of Spacy and keywords."""
        # Common tech skills dictionary for basic matching
        skill_db = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'go',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'laravel',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
            'html', 'css', 'sass', 'tailwind', 'bootstrap',
            'data science', 'machine learning', 'deep learning', 'nlp', 'pandas', 'numpy',
            'project management', 'agile', 'scrum', 'ui/ux', 'figma', 'canva'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        # Keyword matching
        for skill in skill_db:
            # Use word boundaries to avoid partial matches (e.g., 'go' in 'google')
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill.title())
        
        # Spacy entity extraction for potentially unknown skills (proper nouns)
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT'] and ent.text.title() not in found_skills:
                    if len(ent.text) > 2 and len(ent.text) < 20:
                        found_skills.append(ent.text.title())
        
        return list(set(found_skills))

    @staticmethod
    def calculate_match_score(user_skills, job_text):
        """Calculate a percentage score of how well user skills match job description."""
        if not user_skills or not job_text:
            return 0
            
        job_text_lower = job_text.lower()
        user_skills_list = [s.strip().lower() for s in user_skills.split(',') if s.strip()]
        
        if not user_skills_list:
            return 0
            
        matched = 0
        for skill in user_skills_list:
            if skill in job_text_lower:
                matched += 1
                
        score = int((matched / len(user_skills_list)) * 100)
        # Cap at 100
        return min(score, 100)

    @staticmethod
    def auto_extract_profile(file_path):
        """Complete workflow to get profile data from resume."""
        text = ResumeParser.extract_text(file_path)
        if not text:
            return None
            
        skills = ResumeParser.parse_skills(text)
        
        # Basic regex for email and phone
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
        phone_match = re.search(r'(\d{3,4}[\s-]?\d{3,4}[\s-]?\d{4})', text)
        
        return {
            'skills': ", ".join(skills),
            'email': email_match.group(0) if email_match else "",
            'phone': phone_match.group(0) if phone_match else "",
            'full_text': text[:1000] # Snippet
        }
