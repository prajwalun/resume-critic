# 🚀 Resume Critic AI

**AI-powered resume analysis and improvement with human-in-the-loop review**

A comprehensive resume analysis system that provides intelligent suggestions, bullet-point evaluation, and interactive clarification processes to help you create the perfect resume for your dream job.

## ✨ Features

### 🎯 Core Analysis
- **Multi-format Support**: PDF, DOCX, DOC, TXT files
- **Section-based Analysis**: Contact, Summary, Experience, Education, Skills, Projects
- **Bullet-point Evaluation**: Clarity, Impact, and Relevance scoring (1-10)
- **Job-specific Optimization**: Tailored suggestions based on job descriptions

### 🤖 AI-Powered Improvements
- **GPT-4 Integration**: Advanced language model for intelligent suggestions
- **Conservative Approach**: Never fabricates achievements or metrics
- **Context-aware Prompts**: Considers job requirements and resume context
- **Deduplication**: Avoids repetition across bullets

### 👥 Human-in-the-Loop Review
- **Interactive Clarification**: Ask users for specific details when bullets are vague
- **Real Impact Integration**: User input directly improves suggestions
- **Traceability**: Track clarifications with bullet IDs
- **Improved Accuracy**: No hallucinated metrics or achievements

### 📊 Comprehensive Evaluation
- **Clarity Score**: How clear and specific is the bullet point?
- **Impact Score**: How impressive and measurable are the achievements?
- **Relevance Score**: How well does it align with job requirements?
- **Categorization**: Strong, Needs Improvement, Missing Metrics, Vague

### 🔍 Judgment Labs Integration
- **Automatic Tracing**: Track all LLM calls and function executions
- **Online Evaluations**: Real-time quality monitoring
- **Error Tracking**: Comprehensive debugging and monitoring
- **Performance Insights**: Latency and cost tracking

## 🏗️ Architecture

```
resume-critic-ai/
├── backend/                 # FastAPI backend server
│   ├── main.py             # API endpoints and server setup
│   ├── resume_agent.py     # Core ResumeAgent class
│   ├── pdf_parser.py       # Multi-format file parsing
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend application
│   ├── app/               # Next.js app directory
│   ├── components/        # Reusable UI components
│   ├── lib/              # Utilities and API client
│   └── package.json      # Node.js dependencies
└── start.sh              # Full-stack startup script
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd resume-critic-ai
```

### 2. Environment Configuration
Create `backend/.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
JUDGMENT_API_KEY=your_judgment_api_key_here  # Optional
JUDGMENT_ORG_ID=your_judgment_org_id_here    # Optional
```

### 3. Install Dependencies
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 4. Start the Application
```bash
# Start both backend and frontend
./start.sh
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Health Check**: http://localhost:8001/api/health

## 📡 API Endpoints

### Resume Analysis
```http
POST /api/analyze-resume
Content-Type: multipart/form-data

file: resume.pdf
job_description: "Software Engineer position..."
review_mode: true
```

### Human-in-the-Loop Clarification
```http
POST /api/process-clarification
Content-Type: application/json

{
  "analysis_id": "uuid",
  "section_id": "experience",
  "bullet_id": "bullet_1",
  "user_response": "Reduced API response time by 30%",
  "clarification_type": "missing_metrics",
  "original_text": "Improved backend performance",
  "question": "Can you provide measurable results?"
}
```

### Final Resume Generation
```http
POST /api/generate-final-resume
Content-Type: application/json

{
  "analysis_id": "uuid",
  "accepted_changes": {
    "bullet_1": "improved",
    "bullet_2": "original"
  }
}
```

## 🎨 Frontend Features

### Beautiful UI
- **Modern Design**: Clean, professional interface with dark/light mode
- **Responsive Layout**: Works perfectly on desktop and mobile
- **Real-time Feedback**: Live updates and progress indicators
- **Interactive Elements**: Smooth animations and transitions

### User Experience
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Progress Tracking**: Real-time analysis progress
- **Error Handling**: Clear error messages and recovery options
- **Clarification Modal**: Intuitive interface for providing additional details

### Analysis Results
- **Visual Scoring**: Color-coded impact levels and categories
- **Before/After Comparison**: Side-by-side original vs. improved bullets
- **Explanation Cards**: Detailed reasoning for each suggestion
- **Action Buttons**: Apply, Edit, or Reject suggestions

## 🔧 Backend Features

### ResumeAgent Class
- **`extract_job_keywords()`**: Extract skills from job descriptions
- **`parse_resume_sections()`**: Structured resume parsing
- **`evaluate_bullet_point()`**: Comprehensive bullet evaluation
- **`improve_bullet_point()`**: AI-powered improvements
- **`process_clarification()`**: Human-in-the-loop processing
- **`generate_final_resume()`**: Final formatted output

### Judgment Labs Integration
- **Automatic Tracing**: All LLM calls and functions traced
- **Online Evaluations**: Real-time quality monitoring
- **Error Tracking**: Comprehensive debugging
- **Performance Insights**: Latency and cost tracking

## 📊 Analysis Output

```json
{
  "success": true,
  "analysis_id": "uuid",
  "sections": [
    {
      "id": "experience",
      "title": "Work Experience",
      "bullets": [
        {
          "id": "bullet_1",
          "original_text": "Improved backend performance",
          "evaluation": {
            "clarity_score": 3,
            "impact_score": 2,
            "relevance_score": 4,
            "overall_score": 3,
            "category": "missing_metrics",
            "explanation": "Lacks specific metrics",
            "needs_clarification": {
              "required": true,
              "question": "Can you provide measurable results?",
              "type": "missing_metrics"
            }
          },
          "improvement": {
            "improved_text": "Reduced API response time by 30%",
            "changes_made": ["Added specific metric"],
            "confidence": "high"
          }
        }
      ]
    }
  ],
  "summary": {
    "total_bullets": 15,
    "strong_bullets": 8,
    "needs_improvement": 5,
    "needs_clarification": 2,
    "overall_score": 7.2
  }
}
```

## 🛠️ Development

### Backend Development
```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Testing
```bash
# Test backend health
curl http://localhost:8001/api/health

# Test frontend
open http://localhost:3000
```

## 🔒 Security & Privacy

- **No Data Storage**: Analysis results are stored in memory only
- **Secure File Handling**: Temporary file processing with cleanup
- **API Key Protection**: Environment variable configuration
- **CORS Configuration**: Proper cross-origin resource sharing

## 🚀 Deployment

### Backend Deployment
```bash
# Production server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend Deployment
```bash
# Build for production
cd frontend
npm run build
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI**: For GPT-4 language model
- **Judgment Labs**: For tracing and evaluation infrastructure
- **Next.js**: For the frontend framework
- **FastAPI**: For the backend framework
- **Tailwind CSS**: For styling

---

**Built with ❤️ for better resumes and career success!** 