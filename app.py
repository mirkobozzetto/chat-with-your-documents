# app.py
from dotenv import load_dotenv
load_dotenv()

from src.ui.controllers.app_controller import AppController


def main():
    app_controller = AppController()
    app_controller.run_application()


if __name__ == "__main__":
    main()
