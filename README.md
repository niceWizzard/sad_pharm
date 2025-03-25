# SAD Pharmacy Inventory System

This is a System Analysis Design (SAD) project

## Setup / Installation
1. Make sure to have nodejs (v22.14.x) & python (13.3.x) installed
2. Clone the repo
3. Go to the root of the project
4. (Optional, recommended) Create a virtual environment alongside repo 
    i. `python -m venv venv`
    ii. `venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. `py manage.py migrate` - migrates the local database to models
7. (Optional) `py manage.py test ` - run the tests written
8. `py manage.py runserver` - runs the server in localhost.


## Features
1. Users - contains everything about users such as models, login/signup pages
2. Inventory - contains everything that will be stored in the system: items, stocks, etc.