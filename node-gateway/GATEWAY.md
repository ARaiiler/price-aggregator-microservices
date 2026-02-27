# 🚀 GATEWAY — Node.js Express Service

Service backend Node.js (Express) qui agit comme **API Gateway** central du projet.  
Il gère l'authentification JWT, la watchlist utilisateur, et fait le proxy vers le service Python Collector.

---

## 📌 Responsabilités

- **Authentification** : Register / Login avec JWT
- **Watchlist** : CRUD des produits favoris (MongoDB)
- **Search Gateway** : Reçoit les requêtes du frontend et les redirige vers le Python Collector
- **SearchHistory** : Sauvegarde l'historique des recherches en MongoDB

---

## 🏗️ Architecture

```
Frontend (React :3000)
        │
        │  HTTP + JWT Bearer Token
        ▼
Node Gateway (:5000)   ◄── CE SERVICE
        │
        │  HTTP + X-Internal-Api-Key
        ▼
Python Collector (:8000)
        │
        ▼
      Redis
```

---

## ⚙️ Variables d'environnement

Copie `.env.example` en `.env` et remplis les valeurs :

```env
PORT=5000
NODE_ENV=development

MONGO_URI=mongodb://localhost:27017/priceaggregator

JWT_SECRET=change_this_to_a_strong_secret

PYTHON_SERVICE_URL=http://python-collector:8000
INTERNAL_API_KEY=changeme-internal-key
```

> ⚠️ Ne jamais committer le fichier `.env` sur GitHub.

---

## 🔌 Endpoints API

### Auth — public (pas de token requis)

| Méthode | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register` | Créer un compte |
| POST | `/auth/login` | Se connecter, reçoit JWT |

**Register — Body :**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Login — Body :**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Login — Réponse :**
```json
{
  "message": "Login successful",
  "token": "eyJhbGci...",
  "expiresIn": "24h",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "role": "USER"
  }
}
```

---

### Search — 🔐 JWT requis

| Méthode | Route | Description |
|--------|-------|-------------|
| GET | `/search?query=laptop` | Rechercher des produits via Python Collector |

**Réponse :**
```json
{
  "success": true,
  "query": "laptop",
  "results": [...],
  "sources": ["Amazon", "Jumia", "eBay"],
  "total_results": 3,
  "timestamp": "2026-02-27T..."
}
```

---

### Watchlist — 🔐 JWT requis

| Méthode | Route | Description |
|--------|-------|-------------|
| GET | `/watchlist` | Voir tous ses favoris |
| POST | `/watchlist` | Ajouter un produit aux favoris |
| DELETE | `/watchlist/:id` | Supprimer un favori |

**POST — Body :**
```json
{
  "productId": "abc123456789",
  "productName": "Laptop Pro 15\"",
  "lastPrice": 8049.90,
  "source": "Amazon",
  "currency": "MAD",
  "productUrl": "https://amazon.com/...",
  "imageUrl": "https://..."
}
```

---

### Health — public

| Méthode | Route | Description |
|--------|-------|-------------|
| GET | `/health` | Vérifier que le service tourne |

**Réponse :**
```json
{
  "status": "healthy",
  "service": "node-gateway",
  "timestamp": "2026-02-27T...",
  "uptime": 42.5,
  "environment": "production"
}
```

---

## 🔐 Authentification

Toutes les routes protégées nécessitent le header :

```
Authorization: Bearer <token>
```

Le token est obtenu via `POST /auth/login` et expire après **24h**.

---

## 🔗 Communication avec Python Collector

Le service Node Gateway appelle le Python Collector via HTTP avec une clé partagée :

```
Header: X-Internal-Api-Key: <INTERNAL_API_KEY>
```

Les endpoints appelés sur le Python Collector :

| Route Python | Appelée depuis Node |
|---|---|
| `GET /api/search?q=...` | `GET /search?query=...` |
| `GET /api/product/:name/history` | usage interne |

---

## 🗄️ Base de données (MongoDB)

### Collections

**Users**
```json
{
  "email": "user@example.com",
  "password": "<hashed>",
  "role": "USER",
  "createdAt": "...",
  "updatedAt": "..."
}
```

**Watchlist**
```json
{
  "user": "<userId>",
  "productId": "abc123",
  "productName": "Laptop Pro 15\"",
  "lastPrice": 8049.90,
  "source": "Amazon",
  "currency": "MAD",
  "addedAt": "..."
}
```

**SearchHistory**
```json
{
  "userId": "<userId>",
  "query": "laptop",
  "providers": ["Amazon", "Jumia", "eBay"],
  "resultCount": 3,
  "createdAt": "..."
}
```

---

## 🐳 Docker

Le service est conteneurisé. Le Dockerfile expose le port **5000**.

Pour lancer uniquement ce service en local avec Docker Compose :

```bash
docker-compose up node-gateway mongodb
```

Pour lancer tout le projet :

```bash
docker-compose up --build
```

---

## 💻 Lancer en local (sans Docker)

```bash
# Installer les dépendances
npm install

# Copier et configurer les variables d'environnement
cp .env.example .env

# Lancer en mode développement
npm run dev

# Lancer en production
npm start
```

---

## 📦 Dépendances principales

| Package | Rôle |
|---------|------|
| `express` | Framework HTTP |
| `mongoose` | ODM MongoDB |
| `jsonwebtoken` | Génération/vérification JWT |
| `bcryptjs` | Hachage des mots de passe |
| `axios` | Appels HTTP vers Python Collector |
| `helmet` | Sécurité HTTP headers |
| `cors` | Cross-Origin Resource Sharing |
| `morgan` | Logging des requêtes |
| `express-validator` | Validation des inputs |
| `dotenv` | Gestion des variables d'environnement |

