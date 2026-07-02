import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, JSON, text
from sqlalchemy.orm import declarative_base, Session

load_dotenv(override=False)

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

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ pgvector extension enabled")
    Base.metadata.create_all(engine)
    print("✅ Table created successfully")

def save_profile(summary: dict):
    with Session(engine) as session:
        existing = session.query(CandidateProfile)\
            .filter_by(username=summary["username"]).first()
        if existing:
            existing.name             = summary["name"]
            existing.public_repos     = summary["public_repos"]
            existing.followers        = summary["followers"]
            existing.languages        = summary["languages"]
            existing.total_stars      = summary["total_stars"]
            existing.has_readme_count = summary["has_readme_count"]
            existing.recent_commits   = summary["recent_commits"]
            existing.top_repo         = summary["top_repo"]
            existing.bio              = summary["bio"]
            session.commit()
            print(f"✅ Updated {summary['username']} in database")
        else:
            profile = CandidateProfile(
                username         = summary["username"],
                name             = summary["name"],
                public_repos     = summary["public_repos"],
                followers        = summary["followers"],
                languages        = summary["languages"],
                total_stars      = summary["total_stars"],
                has_readme_count = summary["has_readme_count"],
                recent_commits   = summary["recent_commits"],
                top_repo         = summary["top_repo"],
                bio              = summary["bio"],
            )
            session.add(profile)
            session.commit()
            print(f"✅ Saved {summary['username']} to database")

if __name__ == "__main__":
    from ingestion import build_profile_summary
    init_db()
    summary = build_profile_summary("Harikarthik7124")
    save_profile(summary)