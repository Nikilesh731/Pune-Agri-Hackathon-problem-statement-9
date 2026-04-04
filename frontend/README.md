# Frontend Module

## Purpose
React-based frontend application for AI Smart Agriculture Administration platform.

## Technology Stack
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework

## Project Structure
```
src/
├── app/                 # App shell and main components
├── components/          # Reusable UI components
│   ├── common/         # Shared business components
│   └── ui/             # Pure UI components
├── features/           # Feature-based modules
│   ├── auth/           # Authentication
│   ├── dashboard/      # Main dashboard
│   ├── applications/    # Application management
│   ├── grievances/      # Grievance management
│   ├── verification/    # Verification workflow
│   ├── analytics/       # Analytics and reporting
│   ├── farmer-tracking/ # Farmer status tracking
│   ├── notifications/   # Notification system
│   └── settings/        # Settings and configuration
├── layouts/            # Page layout wrappers
├── pages/              # Route page components
├── services/           # API and external service integrations
├── hooks/              # Custom React hooks
├── store/              # State management
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
└── constants/          # Application constants
```

## Development Setup
1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Build for production: `npm run build`

## Feature Modules
Each feature module follows a consistent structure:
- `index.ts` - Module exports
- `components/` - Feature-specific components
- `services/` - Feature-specific API services
- `types/` - Feature-specific types
- `hooks/` - Feature-specific hooks

## Development Guidelines
- Use feature-first organization
- Keep components reusable and composable
- Maintain type safety throughout
- Follow consistent naming conventions
- Add proper documentation for complex logic
