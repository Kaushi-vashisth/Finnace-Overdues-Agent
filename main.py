from database.schema import initialize_database
from observability.tracing import configure_tracing
from scheduler.retry_scheduler import start_scheduler
from ui.app import run_ui

def main():
    initialize_database()
    configure_tracing()
    start_scheduler()
    run_ui()

if __name__ == "__main__":
    main()