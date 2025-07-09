# ResumeWise - Project Structure

```
resume-critic-ai/
├── 📄 README.md                     # Comprehensive project documentation
├── 📄 LICENSE                       # MIT License
├── 📄 .gitignore                    # Git ignore patterns
├── 🚀 start.sh                      # One-click startup script
├── 📄 PROJECT_STRUCTURE.md          # This file
│
├── 🐍 backend/                      # Python FastAPI Backend
│   ├── 📦 app/                      # Main application package
│   │   ├── 📄 __init__.py          
│   │   ├── 📄 main.py               # FastAPI application entry point
│   │   ├── 🔧 api/                  # API routes and endpoints
│   │   │   └── 📄 __init__.py
│   │   ├── 🧠 core/                 # Core business logic
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 🤖 resume_agent.py   # Main agentic resume analyzer
│   │   │   └── 📊 judgment_config.py # Judgment framework integration
│   │   ├── 📋 models/               # Data models and schemas
│   │   │   └── 📄 __init__.py
│   │   ├── ⚙️ services/             # Business services layer
│   │   │   └── 📄 __init__.py
│   │   └── 🛠️ utils/                # Utilities and helpers
│   │       ├── 📄 __init__.py
│   │       └── 📄 pdf_parser.py     # PDF processing utilities
│   ├── 🧪 tests/                    # Test suite
│   │   ├── 📄 __init__.py
│   │   └── 📄 test_resume_agent.py  # Agent testing
│   ├── 📄 requirements.txt          # Python dependencies
│   ├── 📄 pytest.ini               # Test configuration
│   └── 📊 OPTIMIZED_JUDGMENT_INTEGRATION.md # Integration docs
│
└── ⚛️ frontend/                     # Next.js React Frontend
    ├── 📁 app/                      # Next.js 14 app directory
    │   ├── 📄 layout.tsx            # Root layout component
    │   ├── 📄 page.tsx              # Home page
    │   ├── 📄 globals.css           # Global styles
    │   └── 📋 resume-preview/       # Resume preview page
    │       └── 📄 page.tsx
    ├── 🧩 components/               # React components
    │   ├── 📄 theme-provider.tsx    # Theme management
    │   └── 🎨 ui/                   # UI component library (shadcn/ui)
    │       ├── 📄 button.tsx
    │       ├── 📄 card.tsx
    │       ├── 📄 input.tsx
    │       └── ... (30+ UI components)
    ├── 🪝 hooks/                    # Custom React hooks
    │   ├── 📄 use-mobile.tsx
    │   └── 📄 use-toast.ts
    ├── 📚 lib/                      # Utilities and configurations
    ├── 🖼️ public/                   # Static assets
    │   ├── 📷 placeholder-logo.png
    │   ├── 📷 placeholder-user.jpg
    │   └── 📷 placeholder.svg
    ├── 🎨 styles/                   # Styling files
    │   └── 📄 globals.css
    ├── 📄 package.json              # Node.js dependencies
    ├── 📄 package-lock.json         # Dependency lock file
    ├── 📄 pnpm-lock.yaml           # PNPM lock file
    ├── 📄 next.config.mjs          # Next.js configuration
    ├── 📄 tailwind.config.ts       # Tailwind CSS config
    ├── 📄 tsconfig.json            # TypeScript configuration
    ├── 📄 postcss.config.mjs       # PostCSS configuration
    └── 📄 components.json           # shadcn/ui configuration
```

## 🏗️ Architecture Overview

### **Backend (Python/FastAPI)**
- **Dual-System Architecture**: Fast primary scoring + comprehensive Judgment evaluation
- **Agentic Framework**: Iterative improvement with multi-perspective analysis  
- **Observability**: Complete tracing, evaluation, and monitoring via Judgment Labs
- **API-First**: RESTful API with automatic OpenAPI documentation

### **Frontend (Next.js/React)**
- **Modern Stack**: Next.js 14 with App Router, React 18, TypeScript
- **UI Library**: shadcn/ui components with Tailwind CSS
- **Responsive**: Mobile-first design with modern UX patterns
- **Performance**: Optimized builds with Next.js optimizations

### **Key Features**
- 🤖 **Agentic AI**: Autonomous iterative improvement with decision-making
- ⚡ **Dual-System**: Fast decisions + comprehensive insights
- 📊 **Full Observability**: Traces, evaluations, and monitoring
- 🚨 **Pattern Detection**: Automated quality and error pattern recognition
- 🔒 **Privacy**: No data storage, in-memory processing only
- 📈 **Scalable**: Modular architecture ready for production

## 🚀 Quick Start

1. **Clone & Navigate**:
   ```bash
   git clone <repo-url>
   cd resume-critic-ai
   ```

2. **One-Click Start**:
   ```bash
   ./start.sh
   ```

3. **Access Applications**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Judgment Dashboard: https://platform.judgment.ai

## 📊 Monitoring

Monitor your agentic system at [platform.judgment.ai](https://platform.judgment.ai):
- **Traces**: Complete agent execution flows
- **Evaluations**: Quality metrics and pass/fail rates  
- **Monitoring**: Agent actions, errors, and patterns
- **Analytics**: Performance trends and cost analysis 