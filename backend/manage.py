import os
import subprocess
import argparse
from sqlmodel import Session, create_engine, select

from src.db import engine
from src.models.master.apps import Apps

parser = argparse.ArgumentParser(description="Manage the application.")

ALEMBIC_CLIENT_INI = "alembic_client.ini"
ALEMBIC_MASTER_INI = "alembic_master.ini"


def get_available_clients() -> list[Apps]:
    with Session(engine) as session:
        return session.exec(select(Apps).order_by(Apps.name_client)).all()


def print_available_clients() -> list[Apps]:
    clients = get_available_clients()
    if not clients:
        print("No clients found in master DB.")
        return []

    print("Available clients:")
    for client in clients:
        print(f"- {client.name_client}")
    return clients


def select_client() -> Apps:
    clients = print_available_clients()
    if not clients:
        raise RuntimeError("No clients configured")

    clients_by_name = {client.name_client: client for client in clients}
    while True:
        client_name = input("Enter client name: ").strip()
        selected = clients_by_name.get(client_name)
        if selected is None:
            print("Invalid client name. Choose one from the available clients.")
            continue
        if not selected.db_client or selected.db_client == "default":
            print(f"Client '{client_name}' has no valid db_client configured.")
            continue
        return selected

def run_alembic_for_client(args: list[str], client_db_url: str) -> int:
    env = os.environ.copy()
    env["URL_DB"] = client_db_url
    result = subprocess.run(args, env=env)
    return result.returncode

def new_super_user():
    from src.models.clients import User

    selected_client = select_client()
    client_engine = create_engine(selected_client.db_client, future=True)

    while True:
        input_username = input("Enter superuser username: ")
        input_email = input("Enter superuser email: ")
        input_password = input("Enter superuser password: ")
        
        hashed_password = User.hash_password(input_password)
        user = User(username=input_username, hashed_password=hashed_password, email=input_email, admin=True)
        if User.validate_password(input_password):
            print(User.validate_password(input_password))
            continue
        if user.validate():
            print(user.validate())
            continue
        break

    with Session(client_engine) as session:
        session.add(user)
        session.commit()
        print(f"Superuser {input_username} created successfully in client '{selected_client.name_client}'.")


def new_super_user_master():
    from src.models.master.users import UserMasterApp

    while True:
        input_username = input("Enter master superuser username: ")
        input_email = input("Enter master superuser email: ")
        input_password = input("Enter master superuser password: ")

        hashed_password = UserMasterApp.hash_password(input_password)
        user = UserMasterApp(username=input_username, hashed_password=hashed_password, email=input_email, admin=True)
        if UserMasterApp.validate_password(input_password):
            print(UserMasterApp.validate_password(input_password))
            continue
        if user.validate():
            print(user.validate())
            continue
        break

    with Session(engine) as session:
        session.add(user)
        session.commit()
        print(f"Master superuser {input_username} created successfully.")
    
def makemigrations():
    selected_client = select_client()
    name_change = input("Enter a name for the migration (e.g., 'add_users_table'): ")
    command = [
        "alembic",
        "-c",
        ALEMBIC_CLIENT_INI,
        "-x",
        "metadata=client",
        "revision",
        "--autogenerate",
        "-m",
        name_change,
    ]

    return_code = run_alembic_for_client(
        command,
        selected_client.db_client,
    )
    if return_code != 0:
        print(f"Migration generation failed for client '{selected_client.name_client}'.")


def makemigrations_master():
    name_change = input("Enter a name for the master migration (e.g., 'add_users_table'): ")
    command = [
        "alembic",
        "-c",
        ALEMBIC_MASTER_INI,
        "-x",
        "metadata=master",
        "revision",
        "--autogenerate",
        "-m",
        name_change,
    ]

    subprocess.run(command)

def migrate():
    selected_client = select_client()
    return_code = run_alembic_for_client(
        ["alembic", "-c", ALEMBIC_CLIENT_INI, "-x", "metadata=client", "upgrade", "head"],
        selected_client.db_client,
    )
    if return_code != 0:
        print(f"Migration failed for client '{selected_client.name_client}'.")


def migrate_master():
    command = ["alembic", "-c", ALEMBIC_MASTER_INI, "-x", "metadata=master", "upgrade", "head"]
    subprocess.run(command)

def delete_user():
    from src.models.master.users import UserMasterApp

    selected_client = select_client()
    client_engine = create_engine(selected_client.db_client, future=True)

    username = input("Enter the username of the user to delete: ")
    with Session(client_engine) as session:
        statement = select(UserMasterApp).where(UserMasterApp.username == username)
        user = session.exec(statement).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"User {username} deleted successfully in client '{selected_client.name_client}'.")
        else:
            print(f"User {username} not found in client '{selected_client.name_client}'.")


def delete_user_master():
    from src.models.master.users import UserMasterApp

    username = input("Enter the username of the master user to delete: ")
    with Session(engine) as session:
        statement = select(UserMasterApp).where(UserMasterApp.username == username)
        user = session.exec(statement).first()
        if user:
            session.delete(user)
            session.commit()
            print(f"Master user {username} deleted successfully.")
        else:
            print(f"Master user {username} not found.")


def list_clients():
    print_available_clients()
    
if __name__ == "__main__":
    parser.add_argument(
        "command",
        choices=[
            "create_superuser",
            "create_superuser_master",
            "makemigrations",
            "makemigrations_master",
            "migrate",
            "migrate_master",
            "delete_user",
            "delete_user_master",
            "list_clients",
            ],
            help="Command to execute"
        )
    args = parser.parse_args()

    if args.command == "create_superuser":
        new_super_user()

    if args.command == "create_superuser_master":
        new_super_user_master()

    if args.command == "makemigrations":
        makemigrations()

    if args.command == "makemigrations_master":
        makemigrations_master()

    if args.command == "migrate":
        migrate()

    if args.command == "migrate_master":
        migrate_master()
    
    if args.command == "delete_user":
        delete_user()

    if args.command == "delete_user_master":
        delete_user_master()

    if args.command == "list_clients":
        list_clients()