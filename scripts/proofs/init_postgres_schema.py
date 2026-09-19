from stream_editor.api.models.project import Base
from sqlalchemy import create_engine

pg_url = 'postgresql://streameditor:streameditor@127.0.0.1:5432/streameditor'
engine = create_engine(pg_url)
Base.metadata.create_all(engine)
print('PostgreSQL tables successfully created!')
