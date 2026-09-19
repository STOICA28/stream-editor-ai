
from sqlalchemy import create_engine
from stream_editor.api.models.project import Base
engine = create_engine("sqlite:///test.db")
Base.metadata.create_all(engine)

