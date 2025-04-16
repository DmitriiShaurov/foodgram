# Foodgram - Recipe Sharing Platform

https://showroute-foodgram.duckdns.org/

## Overview

Foodgram is a recipe sharing platform where users can publish their own recipes, save others' recipes to favorites, and
subscribe to their favorite authors. The platform also includes a "Shopping List" feature that allows registered users
to create a list of ingredients needed for selected dishes.

## Technology Stack

- Backend: Python/Django
- Frontend: React
- Database: PostgreSQL
- Server: Nginx
- Containerization: Docker

## Features

- User Authentication: Register, login, and manage your profile
- Recipe Management: Create, view, edit, and delete recipes
- Recipe Details. Each recipe includes:
    - Name
    - Image
    - Ingredients
    - Cooking time
    - Tags
- Social Features:
    - Follow your favorite authors
    - Add recipes to favorites
- Shopping List:
    - Add ingredients from recipes to your shopping list
    - Generate a downloadable shopping list with consolidated ingredients

## Installation and Setup

### Prerequisites

- Docker
- Docker Compose

### Development Setup

1. Clone the repository

```shell
git clone git@github.com:DmitriiShaurov/foodgram.git
cd foodgram
```

2. Create .env file with variables. Use .env.example as reference.

3. Build and run with Docker Compose:

```shell
docker compose -f docker-compose.production.yml up -d
```

4. Apply migrations and collect static files:

```shell
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

5. Add ingredients

```shell
docker compose -f docker-compose.production.yml exec backend python manage.py importcsv
```

6. Make sure that API works

```shell
curl -X GET "https://YOUR_DOMAIN/api/ingredients/?name=мука" -H "Accept: application/json" | jq .

[
  {
    "id": 1081,
    "name": "мука",
    "measurement_unit": "г"
  },
  {
    "id": 1082,
    "name": "мука 1 сорт",
    "measurement_unit": "г"
  },
  {
    "id": 1083,
    "name": "мука 2 сорт",
    "measurement_unit": "г"
  },
...
]
```

### API Documentation

You can find the OpenAPI schema in `docs/openapi-schema.yml`. API documentation is available at `/api/docs/`

### Testing

The project includes a Postman collection for API testing located in
`postman_collection/foodgram.postman_collection.json`.