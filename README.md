# Charge Beacon

![Group 8](https://github.com/charge-beacon/charge-beacon/assets/101497/e4e8683f-6318-4a36-94b9-7e0cbc811a50)

[Charge Beacon](https://chargebeacon.app) is a tool that allows you to track and receive updates on EV charging station installations and
availability in specific regions, primarily in North America. It is a free tool that is open to the public. Hosting is provided courtesy of the project maintainers.

## Requirements

* Python 3.11 or later
* Docker for development and testing

## Getting Started

1. Clone the repo
    ```sh
    git clone https://github.com/charge-beacon/charge-beacon.git
   ```

2. Create a virtual environment
    ```sh
    python3 -m venv .venv
    ```

3. Activate the virtual environment. You will want to do this every time you begin development.
    ```sh
    source .venv/bin/activate
    ```

4. Install the required packages. This file changes frequently, so you may want to do this whenever pulling new changes.
    ```sh
    pip install -r requirements.txt
    ```

5. Start docker containers. These are required to run the app as well as run tests.
    ```sh
    docker-compose up -d
    ```

6. Create the database. This is required any time a database migration is added. Run it any time you pull changes.
   ```sh
   python manage.py migrate
   ```

7. Create a superuser. Only required once, or whenever you nuke the DB.
    ```sh
    python manage.py createsuperuser
   ```

8. Run the development server
    ```sh
    python manage.py runserver
   ```

9. Open your browser and navigate to `http://127.0.0.1:8000`

## Contributing

Please feel free to contribute bug fixes and new features. Pull requests are welcome. Please make sure to include tests!

Join in our [Discord](https://discord.gg/rSRtd67JPX) to discuss the project and get help.
