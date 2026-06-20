import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, JSON, text
from sqlalchemy.orm import declarative_base, Session
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

Base = declarative_base()

class CandidateProfile(Base):
    __tablename__ = "candidates"

    id               = Column(Integer, primary_key=True)
    username         = Column(String,  nullable=False)
    name             = Column(String)
    public_repos     = Column(Integer)
    followers        = Column(Integer)
    languages        = Column(JSON)
    total_stars      = Column(Integer)
    has_readme_count = Column(Integer)
    recent_commits   = Column(Integer)
    top_repo         = Column(String)
    bio              = Column(String)
    embedding        = Column(Vector(384))

model = SentenceTransformer("all-MiniLM-L6-v2")

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ pgvector extension enabled")
    Base.metadata.create_all(engine)   # ← removed drop_all
    print("✅ Table created successfully")

def generate_embedding(summary: dict):
    text_input = f"""
    Developer: {summary['name']}
    Languages: {', '.join(summary['languages'])}
    Top project: {summary['top_repo']}
    Bio: {summary['bio']}
    Public repos: {summary['public_repos']}
    Recent commits: {summary['recent_commits']}
    READMEs: {summary['has_readme_count']}
    """
    embedding = model.encode(text_input)
    return embedding

def save_profile(summary: dict):
    embedding = generate_embedding(summary)

    with Session(engine) as session:
        # check if candidate already exists
        existing = session.query(CandidateProfile)\
            .filter_by(username=summary["username"]).first()
        if existing:
            # update existing row
            existing.name             = summary["name"]
            existing.public_repos     = summary["public_repos"]
            existing.followers        = summary["followers"]
            existing.languages        = summary["languages"]
            existing.total_stars      = summary["total_stars"]
            existing.has_readme_count = summary["has_readme_count"]
            existing.recent_commits   = summary["recent_commits"]
            existing.top_repo         = summary["top_repo"]   # ← correct field
            existing.bio              = summary["bio"]
            existing.embedding        = embedding
            session.commit()
            print(f"✅ Updated {summary['username']} in database")
        else:
            # insert new row
            profile = CandidateProfile(
                username         = summary["username"],
                name             = summary["name"],
                public_repos     = summary["public_repos"],
                followers        = summary["followers"],
                languages        = summary["languages"],
                total_stars      = summary["total_stars"],
                has_readme_count = summary["has_readme_count"],
                recent_commits   = summary["recent_commits"],
                top_repo         = summary["top_repo"],       # ← correct field
                bio              = summary["bio"],
                embedding        = embedding,
            )
            session.add(profile)
            session.commit()
            print(f"✅ Saved {summary['username']} with embedding to database")

if __name__ == "__main__":
    from ingestion import build_profile_summary

    init_db()
    summary = build_profile_summary("Harikarthik7124")
    save_profile(summary)