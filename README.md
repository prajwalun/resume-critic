# Resume Critic AI

An AI-powered resume analysis and improvement tool that provides personalized feedback and suggestions to help job seekers create more effective resumes.

## Features

- Resume analysis with detailed feedback
- Job description matching
- Section-by-section improvement suggestions
- Real-time tracing and evaluation using Judgment Labs
- Modern web interface with Next.js

## Project Structure

```
resume-critic-ai/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/           # API routes
│   │   ├── core/          # Core business logic
│   │   ├── models/        # Data models
│   │   └── services/      # Services layer
│   ├── tests/             # Test files
│   ├── requirements.txt   # Python dependencies
│   └── main.py           # Entry point
└── frontend/              # Next.js frontend
    ├── app/              # Pages and routes
    ├── components/       # React components
    ├── hooks/           # Custom hooks
    ├── lib/             # Utilities
    ├── public/          # Static assets
    └── styles/          # CSS styles
```

## Setup

### Backend

1. Create and activate virtual environment:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

3. Run the development server:
```bash
npm run dev
```

## API Documentation

The API documentation is available at `/docs` when the backend server is running.

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Tracing and Evaluation

This project uses Judgment Labs for tracing and evaluating AI interactions:

- Real-time tracing of all AI operations
- Multiple evaluation scorers for different aspects:
  - Answer relevancy
  - Faithfulness
  - Correctness
  - Tool order
- Async evaluation support
- Error tracking with examples

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 