from common.db import engine
from common.models import Base

def main():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    main()
