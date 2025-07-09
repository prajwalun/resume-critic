"""Utility functions for parsing resume files."""
import logging
import re
import pdfplumber
from typing import Optional, List, Dict, Tuple, Any

def extract_resume_text(file_content: bytes, filename: str) -> str:
    """Extract text from a resume file."""
    try:
        # Log the input
        logging.info(f"Extracting text from file: {filename} ({len(file_content)} bytes)")
        
        # Check if it's a PDF file
        is_pdf = filename.lower().endswith('.pdf')
        
        if is_pdf:
            # Use pdfplumber for PDF files
            import io
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                text = '\n'.join(text_parts)
                logging.info(f"Extracted text from PDF: {len(text)} characters")
        else:
            # Try different encodings for text files
            encodings = ['utf-8', 'latin1', 'cp1252', 'ascii']
            text = None
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    logging.info(f"Successfully decoded using {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try utf-8 with error handling
            if text is None:
                text = file_content.decode('utf-8', errors='replace')
                logging.warning("Using fallback UTF-8 decoding with error handling")
        
        # Clean up the text
        text = clean_resume_text(text)
        
        # Log the output
        logging.info(f"Extracted {len(text)} characters of text")
        return text
        
    except Exception as e:
        error_msg = f"Could not extract text from file: {str(e)}"
        logging.error(error_msg)
        raise ValueError(error_msg)

def clean_resume_text(text: Optional[str]) -> str:
    """Clean and normalize resume text."""
    if not text:
        return ""
        
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    
    # Remove null bytes and replacement characters
    text = text.replace('\x00', '')
    text = text.replace('\ufffd', ' ')
    
    # Remove BOM markers
    text = text.lstrip('\ufeff')
    
    # Normalize whitespace but preserve line breaks
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Clean each line individually
        cleaned_line = re.sub(r'\s+', ' ', line.strip())
        cleaned_lines.append(cleaned_line)
    
    # Join lines back together
    text = '\n'.join(cleaned_lines)
    
    # Remove excessive empty lines (more than 2 consecutive)
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()

def split_resume_sections(text: str) -> List[Dict[str, str]]:
    """Split resume text into structured sections using improved header detection."""
    # Enhanced section headers with more variations
    section_patterns = {
        'contact_info': [
            r"contact\s+info(?:rmation)?",
            r"personal\s+info(?:rmation)?",
            r"contact\s+details"
        ],
        'summary': [
            r"(?:professional\s+)?summary",
            r"(?:career\s+)?profile",
            r"(?:professional\s+)?objective",
            r"about\s+me",
            r"overview"
        ],
        'experience': [
            r"(?:work\s+|professional\s+)?experience",
            r"employment\s+history",
            r"career\s+history",
            r"professional\s+background",
            r"work\s+history"
        ],
        'education': [
            r"education(?:al\s+background)?",
            r"academic\s+background",
            r"qualifications",
            r"degrees?",
            r"academic\s+credentials"
        ],
        'skills': [
            r"(?:technical\s+)?skills",
            r"core\s+competencies", 
            r"competencies",
            r"expertise",
            r"technical\s+expertise",
            r"areas\s+of\s+expertise",
            r"programming\s+languages?",
            r"technologies",
            r"tools?\s+(?:and\s+)?technologies"
        ],
        'projects': [
            r"projects?",
            r"personal\s+projects?",
            r"key\s+projects?",
            r"project\s+experience",
            r"portfolio",
            r"notable\s+projects?",
            r"academic\s+projects?"
        ],
        'certifications': [
            r"certifications?",
            r"licenses?",
            r"professional\s+certifications?",
            r"credentials"
        ],
        'achievements': [
            r"achievements?",
            r"accomplishments?",
            r"awards?",
            r"honors?",
            r"recognition"
        ],
        'publications': [
            r"publications?",
            r"research",
            r"papers?",
            r"articles?"
        ],
        'volunteer': [
            r"volunteer(?:ing)?",
            r"community\s+service",
            r"volunteer\s+experience",
            r"civic\s+involvement"
        ],
        'languages': [
            r"languages?",
            r"language\s+skills"
        ],
        'interests': [
            r"interests?",
            r"hobbies",
            r"personal\s+interests?"
        ],
        'references': [
            r"references?",
            r"referees?"
        ]
    }
    
    # Try to extract contact information from the beginning
    contact_info = _extract_contact_info(text)
    
    # Find all section headers and their positions
    sections = []
    section_matches = []
    
    for section_type, patterns in section_patterns.items():
        for pattern in patterns:
            # Look for section headers (case insensitive, allowing for formatting)
            regex = re.compile(rf"^[\s\-=]*{pattern}[\s\-=:]*$", re.MULTILINE | re.IGNORECASE)
            matches = list(regex.finditer(text))
            
            for match in matches:
                section_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': section_type,
                    'header': match.group(0).strip(),
                    'match': match
                })
    
    # Sort matches by position in text
    section_matches.sort(key=lambda x: x['start'])
    
    # If we found contact info, add it as the first section
    if contact_info:
        sections.append({
            "id": "contact_info",
            "type": "contact_info",
            "content": contact_info
        })
    
    # Extract content between section headers
    for i, section_match in enumerate(section_matches):
        start = section_match['end']
        end = section_matches[i+1]['start'] if i+1 < len(section_matches) else len(text)
        
        content = text[start:end].strip()
        
        # Clean up content (remove excessive whitespace and formatting)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        if content:
            sections.append({
                "id": section_match['type'],
                "type": section_match['type'],
                "content": content
            })
    
    # If no sections found OR missing critical sections, try intelligent splitting
    if not sections or not _has_critical_sections(sections):
        logging.info("No sections found or missing critical sections, using intelligent content analysis")
        sections = _intelligent_section_extraction(text, contact_info)
    
    # Ensure we have at least Skills and Projects sections with some content
    sections = _ensure_critical_sections(sections, text)
    
    # Remove duplicates and empty sections
    unique_sections = []
    seen_types = set()
    
    for section in sections:
        if section['type'] not in seen_types and section['content'].strip():
            unique_sections.append(section)
            seen_types.add(section['type'])
    
    return unique_sections if unique_sections else [{"id": "full", "type": "content", "content": text.strip()}]

def _has_critical_sections(sections: List[Dict[str, str]]) -> bool:
    """Check if we have the critical sections needed for analysis."""
    section_types = {section['type'] for section in sections}
    critical_sections = {'education', 'experience'}  # At minimum we need these
    return len(critical_sections.intersection(section_types)) >= 1

def _intelligent_section_extraction(text: str, contact_info: str) -> List[Dict[str, str]]:
    """Use content analysis to extract sections when headers aren't clear."""
    sections = []
    
    # Add contact info if available
    if contact_info:
        sections.append({
            "id": "contact_info",
            "type": "contact_info", 
            "content": contact_info
        })
    
    # Split by double line breaks first
    chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
    
    # Analyze each chunk for content type
    classified_chunks = []
    for chunk in chunks:
        if len(chunk) < 30:  # Skip very short chunks
            continue
        
        section_type = _classify_content_advanced(chunk)
        classified_chunks.append({
            'content': chunk,
            'type': section_type,
            'confidence': _get_classification_confidence(chunk, section_type)
        })
    
    # Group chunks by section type
    section_groups = {}
    for chunk in classified_chunks:
        section_type = chunk['type']
        if section_type not in section_groups:
            section_groups[section_type] = []
        section_groups[section_type].append(chunk['content'])
    
    # Create sections from groups
    for section_type, contents in section_groups.items():
        if section_type != 'unknown':
            combined_content = '\n\n'.join(contents)
            sections.append({
                "id": section_type,
                "type": section_type,
                "content": combined_content
            })
    
    return sections

def _classify_content_advanced(content: str) -> str:
    """Advanced content classification based on multiple signals."""
    content_lower = content.lower()
    
    # Strong indicators for each section type
    strong_indicators = {
        'skills': [
            ['python', 'javascript', 'java', 'c++', 'react', 'node'],
            ['programming', 'languages', 'technologies', 'frameworks'],
            ['aws', 'azure', 'docker', 'kubernetes', 'git'],
            ['sql', 'mongodb', 'postgresql', 'database'],
            ['machine learning', 'ai', 'data science', 'analytics']
        ],
        'experience': [
            ['worked', 'developed', 'managed', 'led', 'implemented'],
            ['company', 'position', 'role', 'responsibilities'],
            ['achieved', 'improved', 'increased', 'reduced'],
            ['team', 'project', 'client', 'customers']
        ],
        'education': [
            ['university', 'college', 'school', 'institute'],
            ['degree', 'bachelor', 'master', 'phd', 'diploma'],
            ['gpa', 'graduated', 'coursework', 'major'],
            ['studied', 'concentration', 'thesis']
        ],
        'projects': [
            ['project', 'built', 'created', 'developed'],
            ['github', 'repository', 'demo', 'live', 'deployed'],
            ['application', 'website', 'app', 'system', 'platform'],
            ['features', 'implemented', 'technologies', 'stack']
        ]
    }
    
    # Calculate scores for each section type
    scores = {}
    for section_type, indicator_groups in strong_indicators.items():
        score = 0
        for group in indicator_groups:
            group_score = sum(1 for word in group if word in content_lower)
            if group_score > 0:
                score += group_score * 2  # Bonus for having indicators from multiple groups
        scores[section_type] = score
    
    # Return the highest scoring section type, or 'unknown' if no clear match
    if scores:
        max_score = max(scores.values())
        if max_score >= 2:  # Minimum threshold
            return max(scores.keys(), key=lambda k: scores[k])
    
    return 'unknown'

def _get_classification_confidence(content: str, section_type: str) -> float:
    """Get confidence score for content classification."""
    # This is a simplified confidence calculation
    # In practice, you'd want more sophisticated scoring
    content_lower = content.lower()
    
    type_keywords = {
        'skills': ['python', 'javascript', 'programming', 'technologies'],
        'experience': ['worked', 'developed', 'company', 'role'],
        'education': ['university', 'degree', 'graduated', 'studied'],
        'projects': ['project', 'built', 'github', 'application']
    }
    
    if section_type in type_keywords:
        keyword_count = sum(1 for word in type_keywords[section_type] if word in content_lower)
        return min(keyword_count / len(type_keywords[section_type]), 1.0)
    
    return 0.0

def _ensure_critical_sections(sections: List[Dict[str, str]], full_text: str) -> List[Dict[str, str]]:
    """Ensure we have Skills and Projects sections even if not explicitly found."""
    existing_types = {section['type'] for section in sections}
    
    # If Skills section is missing, try to extract it
    if 'skills' not in existing_types:
        skills_content = _extract_skills_from_text(full_text)
        if skills_content:
            sections.append({
                "id": "skills",
                "type": "skills",
                "content": skills_content
            })
    
    # If Projects section is missing, try to extract it
    if 'projects' not in existing_types:
        projects_content = _extract_projects_from_text(full_text)
        if projects_content:
            sections.append({
                "id": "projects", 
                "type": "projects",
                "content": projects_content
            })
    
    return sections

def _extract_skills_from_text(text: str) -> str:
    """Extract skills-related content from full text."""
    lines = text.split('\n')
    skills_lines = []
    
    # Look for lines that contain technical terms
    tech_patterns = [
        r'python|javascript|java|c\+\+|react|node|angular|vue',
        r'aws|azure|docker|kubernetes|git|github',
        r'sql|mongodb|postgresql|database|mysql',
        r'machine learning|ai|data science|analytics|tensorflow|pytorch',
        r'html|css|bootstrap|tailwind|sass|scss',
        r'api|rest|graphql|microservices|flask|django|express'
    ]
    
    for line in lines:
        line_lower = line.lower()
        for pattern in tech_patterns:
            if re.search(pattern, line_lower):
                skills_lines.append(line.strip())
                break
    
    # Also look for bullet-pointed lists that might contain skills
    bullet_pattern = r'^[\s]*[•·▪▫◦‣⁃\*\-]\s*(.+)$'
    for line in lines:
        if re.match(bullet_pattern, line):
            line_content = re.sub(bullet_pattern, r'\1', line).strip()
            if any(re.search(pattern, line_content.lower()) for pattern in tech_patterns):
                skills_lines.append(line.strip())
    
    return '\n'.join(skills_lines) if skills_lines else ""

def _extract_projects_from_text(text: str) -> str:
    """Extract project-related content from full text."""
    lines = text.split('\n')
    project_lines = []
    
    # Look for lines that mention projects, building, or development
    project_patterns = [
        r'project|built|created|developed|designed',
        r'github|repository|demo|live|deployed',
        r'application|website|app|system|platform',
        r'features|implemented|technologies|stack'
    ]
    
    in_project_section = False
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Check if this line starts a project description
        if any(re.search(pattern, line_lower) for pattern in project_patterns):
            project_lines.append(line.strip())
            in_project_section = True
        elif in_project_section:
            # Continue collecting lines if they seem to be part of the project description
            if line.strip() and (len(line) < 100 or any(re.search(pattern, line_lower) for pattern in project_patterns)):
                project_lines.append(line.strip())
            elif not line.strip():
                in_project_section = False
    
    return '\n'.join(project_lines) if project_lines else ""

def _extract_contact_info(text: str) -> str:
    """Extract contact information from the beginning of the resume."""
    # Look for contact info patterns in the first 500 characters
    top_text = text[:500]
    
    contact_patterns = [
        r'[\w\.-]+@[\w\.-]+\.\w+',  # Email
        r'[\+]?[\d\s\-\(\)\.]{10,}',  # Phone
        r'linkedin\.com/in/[\w\-]+',  # LinkedIn
        r'github\.com/[\w\-]+',  # GitHub
        r'[\w\s]+,\s*[\w\s]+,\s*[\w\s]+',  # Address-like patterns
    ]
    
    contact_info = []
    
    for pattern in contact_patterns:
        matches = re.findall(pattern, top_text, re.IGNORECASE)
        contact_info.extend(matches)
    
    # Also look for name-like patterns at the beginning
    lines = text.split('\n')[:5]  # First 5 lines
    name_pattern = r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$'
    
    for line in lines:
        if re.match(name_pattern, line.strip()):
            contact_info.insert(0, line.strip())  # Name goes first
            break
    
    return '\n'.join(contact_info) if contact_info else ""

def extract_section_metadata(content: str) -> Dict[str, Any]:
    """Extract metadata from section content."""
    metadata = {
        'word_count': len(content.split()),
        'line_count': len(content.split('\n')),
        'has_bullets': bool(re.search(r'[•·▪▫◦‣⁃]|\*\s|\-\s|\d+\.\s', content)),
        'has_dates': bool(re.search(r'\b\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content)),
        'has_emails': bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', content)),
        'has_phone': bool(re.search(r'[\+]?[\d\s\-\(\)\.]{10,}', content)),
        'has_links': bool(re.search(r'https?://|www\.|\.com|\.org|\.net', content)),
        'has_metrics': bool(re.search(r'\d+%|\$\d+|\d+\+|\d+k|\d+m|\d+x', content, re.IGNORECASE)),
        'contains_keywords': _extract_keywords(content),
        'estimated_type': _classify_content_advanced(content)
    }
    
    return metadata

def _extract_keywords(content: str) -> List[str]:
    """Extract potential keywords from content."""
    # Common technical keywords
    tech_keywords = [
        'python', 'javascript', 'java', 'react', 'node', 'angular', 'vue',
        'aws', 'azure', 'docker', 'kubernetes', 'sql', 'mongodb', 'postgresql',
        'git', 'github', 'api', 'rest', 'graphql', 'microservices',
        'machine learning', 'ai', 'data science', 'analytics', 'tensorflow',
        'pytorch', 'pandas', 'numpy', 'flask', 'django', 'express'
    ]
    
    found_keywords = []
    content_lower = content.lower()
    
    for keyword in tech_keywords:
        if keyword in content_lower:
            found_keywords.append(keyword)
    
    return found_keywords 