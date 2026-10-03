import os
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'db.sqlite3')
migrations_dir = os.path.join(base_dir, 'core', 'migrations')

try:
    if os.path.exists(db_path):
        os.remove(db_path)
        print("db.sqlite3 deleted.")
except PermissionError:
    print("WARNING: db.sqlite3 is locked by runserver. Please stop runserver and try again.")

if os.path.exists(migrations_dir):
    shutil.rmtree(migrations_dir)
    print("core/migrations deleted.")

os.makedirs(migrations_dir)
with open(os.path.join(migrations_dir, '__init__.py'), 'w') as f:
    pass
print("core/migrations created.")
