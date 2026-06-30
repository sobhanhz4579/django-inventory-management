import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BACKUP_DIR = BASE_DIR / "backups"

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def create_backup():
    """Create PostgreSQL database backup."""

    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    existing = list(BACKUP_DIR.glob(f"backup_{timestamp}_*.sql"))

    counter = 1

    if existing:
        numbers = []

        for file in existing:
            try:
                numbers.append(int(file.stem.split("_")[-1]))
            except ValueError:
                pass

        if numbers:
            counter = max(numbers) + 1

    backup_file = BACKUP_DIR / f"backup_{timestamp}_{counter:03d}.sql"

    cmd = [
        "pg_dump",
        "-h",
        DB_HOST,
        "-p",
        DB_PORT,
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-f",
        str(backup_file),
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    try:
        subprocess.run(cmd, env=env, check=True)

        print("Backup created successfully")
        print(f"{backup_file}")

    except subprocess.CalledProcessError as e:
        print("Error while creating backup")
        print(e)

    except FileNotFoundError:
        print("pg_dump not found.")
        print("Install PostgreSQL client:")
        print("sudo apt install postgresql-client")


if __name__ == "__main__":
    create_backup()
