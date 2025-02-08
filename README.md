# 🚀 Django Project News/Places with Celery & Docker

## 📌 Table of Contents
| Section | Description |
|---------|------------|
| [Project Description](#-project-description) | Overview of the project and its features |
| [Technologies Used](#️-technologies-used) | List of technologies utilized in the project |
| [Features](#-features) | Functionalities provided by the system |
| [Setup & Installation](#️-setup--installation) | Steps to set up and run the project |
| [Testing](#-testing) | Instructions for running tests and linting |
| [Project Structure](#-project-structure) | Folder structure explanation |
| [Usage Presentation](#-usage-presentation) | Presentation of Service Work and API usage |
| [Contacts](#-contacts) | Developer contact information |

---

## 🚀 Project Description
This project is a **Django-based web application** that includes:
- 📡 **Celery** for background task processing.
- 🗺 **PostgreSQL with PostGIS** for geospatial data.
- 🔥 **Redis** as a message broker for Celery.
- ✉ **SMTP4Dev** for local email testing.
- 🐳 **Docker Compose** for easy setup and deployment.
- 📊 **Flower** for monitoring Celery tasks.

---

## ⚙️ **Technologies Used**
- **Backend:** ![Python 3.13](https://img.shields.io/badge/Python-3.13-000000?style=for-the-badge&labelColor=fafbfc&logo=python&logoColor=306998&color=2b3137) ![Django REST Framework](https://img.shields.io/badge/Django-DRF-000000?style=for-the-badge&labelColor=fafbfc&logo=django&logoColor=306998&color=2b3137) ![Celery](https://img.shields.io/badge/Celery-2b3137?style=for-the-badge&logo=celery)
- **Database:** ![PostgreSQL|Postgis](https://img.shields.io/badge/Postgresql-Postgis-000000?style=for-the-badge&labelColor=fafbfc&logo=postgresql&logoColor=306998&color=2b3137)
- **Task Queue:** ![Redis](https://img.shields.io/badge/Redis-2b3137?style=for-the-badge&logo=redis)
- **Email Testing**: ![SMTP4Dev](https://img.shields.io/badge/SMTP4Dev-2b3137?style=for-the-badge&logo=gmail)
- **Monitoring**: ![Flower](https://img.shields.io/badge/Flower-2b3137?style=for-the-badge&logo=celery)
- **Testing & CI/CD:** ![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-fafbfc?style=for-the-badge&labelColor=fafbfc&logo=github-actions&logoColor=black&color=2b3137) ![Tox](https://img.shields.io/badge/Tox-2b3137?style=for-the-badge&logo=tox) ![Pytest](https://img.shields.io/badge/Pytest-2b3137?style=for-the-badge&logo=pytest) ![Ruff](https://img.shields.io/badge/Ruff-2b3137?style=for-the-badge&logo=ruff)
- **Deployment:** ![Docker & Docker Compose](https://img.shields.io/badge/Docker-Compose-fafbfc?style=for-the-badge&labelColor=fafbfc&logo=docker&locoColor=black&color=2b3137)

---

## 🎯 **Features**
### 📰 **News Management**
- ✅ **CRUD operations for news** with fields:
  - Title
  - Main image (auto-generates preview)
  - Rich-text content (via Summernote)
  - Publication date
  - Author
- ✅ **Admin panel with rich-text editor for news editing**
- ✅ **Automatic preview image generation (200px on the shortest side)**

### 📩 **Email Notifications for News**
- ✅ **Scheduled Celery task to send daily emails** about published news.
- ✅ **Configurable email settings via Django Constance**:
  - Recipient list
  - Email subject
  - Email body
  - Scheduled sending time

### 📍 **Places Management**
- ✅ **Import places from an XLSX file**, including:
  - Name
  - Geo-coordinates (PointField)
  - Rating (0 to 25)
- ✅ **Admin panel integration with a map widget for coordinate selection**

### 🌦 **Weather Summary Collection**
- ✅ **Scheduled Celery task to fetch weather data** for all places.
- ✅ **Configurable task frequency from the admin panel** (default: every hour).
- ✅ **Weather data provider: Open-Meteo API**
- ✅ **Stored weather data includes**:
  - Temperature (°C)
  - Humidity (%)
  - Atmospheric pressure (mmHg)
  - Wind direction
  - Wind speed (m/s)
- ✅ **Weather records are immutable once saved**
- ✅ **Admin panel filter for places and date selection**
- ✅ **Export weather data to XLSX format**

### 🛠 **Additional Features**
- ✅ **Dockerized setup for easy deployment**
- ✅ **Celery task monitoring with Flower**
- ✅ **Mail monitoring with SMTP4Dev** (only docker-compose run)
- ✅ **Testing with Pytest & Tox**

---

## 🛠️ Setup & Installation

Follow the steps below to set up and run the project locally.

### 1. Clone the Repository

Clone the repository to your local machine:
```bash
git clone https://github.com/arielen/test_CifraK.git
cd test_CifraK
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory by copying the example file:
```bash
cp .env.example .env
```
Then, update the `.env` file according to your configuration.

### 3. Running the Project

You can run the project using one of the following methods:

### A. Using Docker-Compose

If you have Docker installed, use Docker Compose to build and run all services (Django, Celery, Redis, PostgreSQL, and SMTP4Dev). All migrations will be executed automatically:
```bash
docker-compose up -d --build
```

### B. Running Locally without Docker

1. **Running the Django Application**

   Create a virtual environment, install dependencies, perform migrations, create a superuser, and run the development server:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   python backend/manage.py makemigrations
   python backend/manage.py migrate
   python backend/manage.py createsuperuser
   python backend/manage.py runserver
   ```

2. **Running Celery Worker & Beat**

   Navigate to the `backend` directory and start Celery with the worker and Beat:
   ```bash
   cd backend
   celery -A config worker -B -l info
   ```

3. **(Optional) Running Celery Flower**

   To monitor Celery tasks, you can use Flower. Run the following command:
   ```bash
   celery -A config flower --port=5555
   ```
   Flower will be available at [http://localhost:5555](http://localhost:5555).

## 4. Admin Interface and API Documentation

- **Admin Interface:** [http://localhost:8000/admin](http://localhost:8000/admin)
- **API Schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
- **Swagger UI:** [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **Redoc:** [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)

---

## ✅ **Testing**
To run tests with `tox`:
```sh
tox  # run all tests, coverage and lint
```
or 
```sh
tox -e coverage  # run target only coverage
tox -e lint  # run target only lint with ruff
```
Test coverage must be at least 95%. If the code is not 95% covered, the overall coverage will drop.

---

## 📂 **Project Structure**
```
📂 backend
├── 📂 config                  # Django settings & Celery config
├── 📂 news                    # News app (models, views, tasks)
├── 📂 places                  # Places app (geospatial data, weather tasks)
├── 📂 templates               # Custom admin templates
├── 📜 manage.py               # Django entry point
├── 📜 requirements.txt        # Dependencies
├── 📜 Dockerfile              # Dockerfile for Django
├── 📜 __main__.py             # Main script
├── 📜 create_admin.py         # Superuser creation script
├── 📂 tests                   # Test cases
📜 .env.example                # Example environment variables
📜 docker-compose.yml          # Docker Compose setup
📜 pyproject.toml              # Configuration for ruff & pytest
📜 tox.ini                     # Testing configuration
📜 README.md                   # Project documentation
```

---

## ✉ **Email & Celery Monitoring**
### 🔹 **Email Testing with SMTP4Dev**
The project uses `smtp4dev` for testing email functionality. Access the UI at:
[http://localhost:8025](http://localhost:8025)

### 🔹 **Monitor Celery Tasks with Flower**
Access Flower to monitor Celery tasks:
[http://localhost:5555](http://localhost:5555)

---

## 🎥 **Usage presentation**

---

## 📞 **Contacts**
💻 **Developer:** [arielen](https://github.com/arielen)  
📧 **Email:** pavlov_zv@mail.ru  
📧 **TG:** [1 0](https://t.me/touch_con)  
