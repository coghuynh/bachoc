import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Text, REAL, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./profile.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session = SessionLocal()


class Subject(Base):
    __tablename__ = "Subjects"
    subject_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    facts = relationship("Fact", back_populates="subject")

class Predicate(Base):
    __tablename__ = "Predicates"
    predicate_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    facts = relationship("Fact", back_populates="predicate")

class Fact(Base):
    __tablename__ = "Facts"
    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    
    subject_id = Column(Integer, ForeignKey("Subjects.subject_id"), nullable=False)
    predicate_id = Column(Integer, ForeignKey("Predicates.predicate_id"), nullable=False)
    object_value = Column(Text, nullable=False)
    

    page = Column(Integer)
    confidence = Column(REAL)
    source = Column(Text)
    

    subject = relationship("Subject", back_populates="facts")
    predicate = relationship("Predicate", back_populates="facts")

    def __repr__(self):

        return f"<Fact: {self.subject.name} - {self.predicate.name} - {self.object_value}>"

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Đã tạo bảng thành công!")

if __name__ == "__main__":
    create_tables()