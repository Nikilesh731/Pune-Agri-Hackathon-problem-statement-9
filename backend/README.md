# Backend Module

## Purpose
Node.js/Express backend API for AI Smart Agriculture Administration platform.

## Technology Stack
- **Node.js** - Runtime environment
- **Express** - Web framework
- **TypeScript** - Type safety
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing
- **Winston** - Logging
- **Joi** - Request validation

## Project Structure
```
src/
├── config/            # Configuration management
├── modules/           # Feature-based modules
│   ├── auth/          # Authentication & authorization
│   ├── applications/  # Application management
│   ├── grievances/    # Grievance management
│   ├── verification/  # Verification workflow
│   ├── analytics/     # Analytics & reporting
│   ├── farmer-tracking/ # Farmer status tracking
│   ├── notifications/ # Notification system
│   └── ai-orchestrator/ # AI service integration
├── middlewares/       # Express middleware
├── repositories/      # Data access layer
├── services/          # Business logic layer
├── controllers/       # HTTP request handlers
├── routes/           # API route definitions
├── utils/            # Utility functions
└── types/            # TypeScript type definitions
```

## Module Structure
Each feature module follows a consistent structure:
- `index.ts` - Module exports
- `*.routes.ts` - API endpoints
- `*.controller.ts` - Request handlers
- `*.service.ts` - Business logic
- `*.repository.ts` - Data access
- `*.types.ts` - Module-specific types

## Development Setup
1. Install dependencies: `npm install`
2. Set up environment variables (copy `.env.example` to `.env`)
3. Start development server: `npm run dev`
4. Build for production: `npm run build`

## API Design Principles
- RESTful API design
- Consistent response format
- Proper HTTP status codes
- Request validation
- Error handling
- Authentication & authorization

## Middleware Stack
- **Helmet** - Security headers
- **CORS** - Cross-origin requests
- **Morgan** - HTTP request logging
- **Body Parser** - JSON/URL-encoded parsing
- **Auth Middleware** - JWT verification
- **Request Validator** - Joi schema validation
- **Error Handler** - Centralized error handling

## Development Guidelines
- Use TypeScript for type safety
- Follow modular architecture
- Implement proper error handling
- Add comprehensive logging
- Maintain API consistency
- Write unit tests for services
