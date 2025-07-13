# Ordering System Microservices

A Dockerized Python microservices app for browsing items, adding to cart, and placing orders. Built with FastAPI, MongoDB, PostgreSQL, gRPC, and RabbitMQ, with Google OAuth2 auth and separate admin and user interfaces.

## 🛒 Features

- User interface for browsing and filtering items
- Add items to a shopping cart and place orders
- Admin panel to manage items and orders
- Google OAuth2 login for secure access
- Asynchronous order handling via RabbitMQ and gRPC
- Templated UI using Jinja2

## 🧰 Tech Stack

- **Backend**: Python, FastAPI, Starlette
- **Auth**: Google OAuth2
- **Databases**: MongoDB (items, cart), PostgreSQL (orders)
- **Communication**: RabbitMQ, gRPC
- **Frontend**: Jinja2 templates
- **Containerization**: Docker, Docker Compose

## 🚀 Running the Project

1. Clone the repository:
   ```bash
   git clone https://github.com/david-dostal/ordering-system-microservices.git
   cd ordering-system-microservices
   ```

2. Start services with Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Access:
   - User UI: [http://localhost:8000](http://localhost:8000)
   - Admin UI: [http://localhost:8005](http://localhost:8005)
   - RabbitMQ Dashboard: [http://localhost:15672](http://localhost:15672)
   - Mongo Express: [http://localhost:27001](http://localhost:27001)
   - Adminer (PostgreSQL): [http://localhost:8081](http://localhost:8081)
