import alembic.config
import os
import sys
sys.path.insert(0, os.path.abspath("apps/api/src"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///stream_editor.db"
alembicArgs = ["-c", "apps/api/alembic.ini"] + sys.argv[1:]
with open("apps/api/alembic.ini", "r") as f:
    text = f.read()
with open("apps/api/alembic.ini", "w") as f:
    f.write(text.replace("script_location = alembic", "script_location = apps/api/alembic"))
try:
    alembic.config.main(argv=alembicArgs)
finally:
    with open("apps/api/alembic.ini", "w") as f:
        f.write(text)
