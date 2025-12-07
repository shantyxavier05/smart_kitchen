# Smart Kitchen Application

A frontend application for managing kitchen inventory, meal planning, and shopping lists.

## Features

- User authentication (Login/Signup) - *Backend integration needed*
- Protected routes - only authenticated users can access pages
- Meal planning interface
- Inventory management
- Shopping list generation

## Setup Instructions

### Frontend Setup (React/Vite)

1. Install Node.js dependencies (if not already installed):
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000` (or the port specified in vite.config.js).

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── ProtectedRoute.jsx
│   │   ├── MealPlanner.jsx
│   │   ├── Inventory.jsx
│   │   ├── ShoppingList.jsx
│   │   └── Landing.jsx
│   ├── context/
│   │   └── AuthContext.jsx  # Authentication context (needs backend integration)
│   └── App.jsx              # Main app component
└── package.json            # Node.js dependencies
```

## Backend Integration

This application requires a backend for authentication and data persistence. The `AuthContext.jsx` file contains placeholder functions that need to be integrated with your backend API.

### Required Backend Endpoints

- `POST /api/signup` - Register a new user
- `POST /api/login` - Authenticate user and get JWT token
- `GET /api/verify` - Verify JWT token (protected)

### Integration Steps

1. Update `API_BASE_URL` in `src/context/AuthContext.jsx` with your backend URL
2. Implement the `login` and `signup` functions to call your backend API
3. Update the authentication verification logic as needed

## Notes

- Authentication is currently disabled until backend is integrated
- Protected routes will redirect to login page
- All data is currently stored in component state (not persisted)

