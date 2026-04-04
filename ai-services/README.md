# AI Services Module

## Purpose
FastAPI microservice for AI-powered agriculture administration features.

## Technology Stack
- **Python** - Programming language
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **PyTorch** - Machine learning framework
- **Scikit-learn** - ML library
- **OpenCV** - Computer vision
- **Tesseract** - OCR engine
- **NLTK** - Natural language processing
- **Transformers** - Hugging Face models

## AI Services

### 1. OCR (Optical Character Recognition)
- **Purpose**: Extract text from scanned documents and images
- **Features**: Multi-language support, batch processing, image preprocessing
- **Router**: `/api/ocr/`

### 2. Grievance Classification
- **Purpose**: Automatically categorize farmer grievances
- **Features**: Multi-class classification, confidence scoring, batch processing
- **Router**: `/api/classification/`

### 3. Application Priority Scoring
- **Purpose**: Score and prioritize applications based on multiple criteria
- **Features**: Multi-factor scoring, risk assessment, batch processing
- **Router**: `/api/scoring/`

### 4. Fraud Detection
- **Purpose**: Detect potential fraud in applications and documents
- **Features**: Pattern detection, risk indicators, explanation generation
- **Router**: `/api/fraud-detection/`

### 5. Text Summarization
- **Purpose**: Generate concise summaries of long documents
- **Features**: Extractive/abstractive summarization, configurable length
- **Router**: `/api/summarization/`

## Project Structure
```
ai-services/
├── app/                    # FastAPI application
│   ├── api/               # API route definitions
│   ├── core/              # Core configuration
│   ├── models/            # ML model definitions
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   └── main.py           # Application entry point
├── ocr/                   # OCR service
│   ├── router.py         # FastAPI router
│   ├── service.py        # Business logic
│   └── models.py         # ML models
├── grievance_classification/  # Classification service
│   ├── router.py         # FastAPI router
│   ├── service.py        # Business logic
│   └── models.py         # ML models
├── application_priority_scoring/  # Scoring service
│   ├── router.py         # FastAPI router
│   ├── service.py        # Business logic
│   └── models.py         # ML models
├── fraud_detection/      # Fraud detection service
│   ├── router.py         # FastAPI router
│   ├── service.py        # Business logic
│   └── models.py         # ML models
└── summarization/        # Summarization service
    ├── router.py         # FastAPI router
    ├── service.py        # Business logic
    └── models.py         # ML models
```

## Development Setup
1. Create virtual environment: `python -m venv venv`
2. Activate environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Start development server: `uvicorn app.main:app --reload`

## API Design
- RESTful endpoints
- Consistent response schemas
- Comprehensive error handling
- Request validation
- Async processing support

## Model Management
- Model loading and caching
- Version management
- Performance monitoring
- Batch processing support

## Development Guidelines
- Use async/await for I/O operations
- Implement proper error handling
- Add comprehensive logging
- Maintain type hints
- Write unit tests for services
- Document API endpoints

## Performance Considerations
- Model caching strategies
- Batch processing optimization
- Memory management
- Request queuing for heavy operations
- Monitoring and metrics
