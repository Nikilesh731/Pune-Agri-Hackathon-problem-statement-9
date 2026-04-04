# Shared Module

## Purpose
Common types, constants, and utilities shared across frontend, backend, and AI services.

## Structure
```
shared/
├── types/              # TypeScript type definitions
│   ├── common.ts      # Core business entity types
│   ├── ai.ts          # AI service integration types
│   └── index.ts       # Type exports
├── constants/          # Application constants
│   ├── common.ts      # General constants
│   ├── index.ts       # Constant exports
│   └── api.ts         # API-related constants
├── utils/              # Shared utility functions
│   ├── validation.ts  # Validation utilities
│   ├── formatting.ts  # Data formatting utilities
│   └── index.ts       # Utility exports
└── schemas/            # Data schemas
    ├── api.ts         # API request/response schemas
    └── database.ts    # Database schemas
```

## Type Definitions

### Core Types (`types/common.ts`)
- **User**: User entity with roles and permissions
- **Application**: Application entity with status and priority
- **Grievance**: Grievance entity with categories and severity
- **Farmer**: Farmer entity with land holdings and bank details
- **Verification**: Verification task entity with results
- **Notification**: Notification entity with types and priorities

### AI Service Types (`types/ai.ts`)
- **OCR**: Text extraction from images
- **Classification**: Text categorization
- **Scoring**: Application priority scoring
- **Fraud Detection**: Fraud pattern detection
- **Summarization**: Text summarization

## Constants

### API Endpoints (`constants/index.ts`)
- Backend API endpoints
- AI service endpoints
- Authentication endpoints
- Resource endpoints

### Status Colors (`constants/index.ts`)
- UI color mappings for different statuses
- Priority level colors
- Severity level colors

### Application Configuration (`constants/index.ts`)
- Pagination settings
- File upload limits
- Session timeouts
- Rate limiting

### Validation Rules (`constants/index.ts`)
- Input validation patterns
- Length constraints
- Format requirements

## Usage

### Frontend (React/TypeScript)
```typescript
import { User, ApplicationStatus } from '../../../shared/types/common'
import { STATUS_COLORS, API_ENDPOINTS } from '../../../shared/constants'

// Use shared types in components
const UserProfile: React.FC<{ user: User }> = ({ user }) => {
  return (
    <div style={{ color: STATUS_COLORS.APPLICATION_STATUS[user.status] }}>
      {user.name}
    </div>
  )
}
```

### Backend (Node.js/TypeScript)
```typescript
import { Application, ApplicationStatus } from '../../../shared/types/common'
import { ERROR_CODES, VALIDATION_RULES } from '../../../shared/constants'

// Use shared types in services
class ApplicationService {
  async createApplication(data: Partial<Application>): Promise<Application> {
    // Validate using shared rules
    if (!VALIDATION_RULES.APPLICATION.TITLE_MIN_LENGTH) {
      throw new Error(ERROR_CODES.VALIDATION.INVALID_LENGTH)
    }
    // Implementation
  }
}
```

### AI Services (Python/FastAPI)
```python
from typing import Dict, Any
from pydantic import BaseModel

# Use shared type definitions as reference
# (Python equivalent of TypeScript types)
class OCRRequest(BaseModel):
    image_data: str  # Base64 encoded
    language: str = "eng"
    preprocess: bool = True

class OCRResponse(BaseModel):
    success: bool
    extracted_text: str
    confidence: float
    language_detected: Optional[str]
    processing_time_ms: int
    request_id: str
```

## Benefits

1. **Type Safety**: Consistent types across all services
2. **Reduced Duplication**: Single source of truth for common definitions
3. **Easier Maintenance**: Changes in one place reflect everywhere
4. **Better Collaboration**: Shared understanding of data structures
5. **API Consistency**: Standardized request/response formats

## Development Guidelines

1. **Keep it Generic**: Avoid service-specific logic in shared types
2. **Version Compatibility**: Consider backward compatibility when updating
3. **Documentation**: Provide clear descriptions for complex types
4. **Validation**: Include validation rules where applicable
5. **Examples**: Add usage examples in comments

## Updates

When updating shared types or constants:
1. Update all affected services
2. Run tests to ensure compatibility
3. Update documentation
4. Communicate changes to team members
5. Consider versioning for breaking changes
