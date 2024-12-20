# Spy-Cat-Agency

## This task involves building a CRUD application.

The goal is to create a system that showcases your understanding in building RESTful APIs, 
interacting with SQL-like databases, and integrating third-party services.

## Clone the Repository

git clone https://github.com/VlaBeh/Spy-Cat-Agency cd agency

### Virtual Environment Setup

Windows: python -m venv venv venv\Scripts\Activate

Unix systems: python3 -m venv venv source venv/bin/activate

### Environment Configuration

Create an .env file in the root of the project directory using the provided create_env.sh script. This script generates the .env file with the necessary fields.

## Local Installation

Install the required dependencies:
pip install -r requirements.txt

Apply the database migrations:
python.manage.py makemigrations
python manage.py migrate

Start the development server:
python manage.py runserver

## Postman Documentation:

https://www.postman.com/vlabeh/sca/overview

**Backend Requirements:**

- **Spy Cats**
    - Ability to create a spy cat in the system
        - A cat is described as Name, Years of Experience, Breed, and Salary.
        - Breed must be validated, see General
    - Ability to remove spy cats from the system
    - Ability to update spy cats’ information (Salary)
    - Ability to list spy cats
    - Ability to get a single spy cat
- **Missions / Targets**
    - Ability to create a mission in the system along with targets in one single request
        - A mission contains information about Cat, Targets and Complete state
        - Each target is unique to a mission, so the endpoint should accept an object describing targets
        - A target is described as Name, Country, Notes and Complete state
    - Ability to delete a mission
        - A mission cannot be deleted if it is already assigned to a cat
    - Ability to update mission targets
        - Ability to mark it as completed
        - Ability to update Notes
            - Notes cannot be updated if either the target or the mission is completed
    - Ability to assign a cat to a mission
    - Ability to list missions
    - Ability to get a single mission
- **General**
    - Framework
        - Use any of: Django
    - Database
        - db.sqlite3
    - Validations
        - Validate cat’s breed with [TheCatAPI](https://api.thecatapi.com/v1/breeds)# Django_back_coo
