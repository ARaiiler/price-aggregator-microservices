# PriceCompare Frontend

Complete React 18 frontend for the price comparison aggregator. Runs on **port 3000** and connects to the existing backend API on **port 5000**.

**Frontend only** — do not create or modify backend files. The backend is already running separately.

## Backend API (do not touch)

- `POST http://localhost:5000/auth/register` — Body: `{ email, password }`
- `POST http://localhost:5000/auth/login` — Body: `{ email, password }` → Returns `{ token }`
- `GET http://localhost:5000/search?query=` — Requires `Authorization: Bearer <token>`

## Features

- **Auth**: Register, login, logout. JWT stored in `localStorage` under key `token`.
- **Protected routes**: Dashboard and Favorites redirect to `/login` if not authenticated.
- **Search**: Prominent search bar on Dashboard; calls `/search?query=` with JWT; loading skeleton and error handling.
- **Favorites**: Heart icon (♡/♥) on each product card; favorites stored in `localStorage` under key `favorites`. No backend calls for favorites.
- **Favorites page**: Route `/favorites`; grid of favorited products; empty state message; hearts filled and clickable to remove.
- **Navbar**: Logo, Dashboard, Favorites, Logout when logged in; Log in / Get started when not.
- **Design**: Tailwind CSS, light gray background (#F9FAFB), white cards, indigo primary, responsive grid (3/2/1 columns).

## Tech stack

- React 18, functional components, hooks
- React Router v6
- Axios (baseURL + token interceptor; 401 logs out and redirects to login)
- Context API: `AuthContext` (login, logout, register), `FavoritesContext` (favorites, add, remove, toggle)
- Tailwind CSS
- React Icons (FiHeart outline, FaHeart filled)

## Getting started

1. Ensure the backend is running on `http://localhost:5000`.
2. From the project root:

   ```bash
   cd frontend
   npm install
   npm start
   ```

3. Open `http://localhost:3000`.

## Environment

Create or edit `.env` in `frontend/`:

```
REACT_APP_API_URL=http://localhost:5000
```

## Project structure

```
frontend/
├── public/index.html
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── auth/
│   │   │   ├── LoginForm.jsx
│   │   │   └── RegisterForm.jsx
│   │   ├── search/
│   │   │   ├── SearchBar.jsx
│   │   │   ├── ProductCard.jsx   (heart icon + View Deal)
│   │   │   ├── ProductGrid.jsx
│   │   │   └── LoadingSkeleton.jsx
│   │   ├── favorites/
│   │   │   └── FavoritesGrid.jsx
│   │   └── ui/
│   │       ├── Button.jsx
│   │       ├── Input.jsx
│   │       ├── Spinner.jsx
│   │       └── Alert.jsx
│   ├── pages/
│   │   ├── LandingPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── DashboardPage.jsx
│   │   └── FavoritesPage.jsx
│   ├── context/
│   │   ├── AuthContext.jsx
│   │   └── FavoritesContext.jsx
│   ├── services/api.js    (registerUser, loginUser, searchProducts)
│   ├── utils/formatters.js
│   ├── App.jsx
│   └── index.js
├── .env
├── .gitignore
├── package.json
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

## Verification checklist

- [x] User can register with email/password
- [x] User can login and token is stored (`localStorage` key `token`)
- [x] Protected routes redirect to login when not authenticated
- [x] Navbar shows Dashboard, Favorites, Logout when logged in
- [x] Logout removes token and redirects to landing
- [x] Search bar calls API with token and displays results
- [x] Each product card has a heart icon (FiHeart / FaHeart)
- [x] Clicking heart adds/removes product in favorites (localStorage `favorites`)
- [x] Favorites page shows favorited products; empty state message
- [x] Favorites persist after page refresh
- [x] Heart state matches localStorage (filled if favorited)
- [x] Responsive layout (Tailwind grid)
