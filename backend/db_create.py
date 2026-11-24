from config import engine
from models import Base

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

create_tables()

