import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import engine, CandidateProfile, init_db
from ingestion import build_profile_summary
from graph import build_graph, CandidateState

load_dotenv()

app = FastAPI(
    title="AutoEval API",
    description="Multi-agent developer assessment platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://autoeval.vercel.app",
        "https://*.onrender.com",
        "https://autoeval-frontend.onrender.com",
        "https://autoeval-api.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

init_db()

class EvaluateRequest(BaseModel):
    username: str

class EvaluateResponse(BaseModel):
    id          : str
    username    : str
    composite   : float
    final_scores: dict
    conflicts   : list
    status      : str
    cache_hit   : bool

results_store = {}

def profile_changed(existing: CandidateProfile, new_summary: dict) -> bool:
    repo_changed    = existing.public_repos != new_summary["public_repos"]
    commits_changed = abs(existing.recent_commits - new_summary["recent_commits"]) > 5
    lang_changed    = set(existing.languages or []) != set(new_summary["languages"])

    if repo_changed:
        print(f"🔄 Repo count changed: {existing.public_repos} → {new_summary['public_repos']}")
    if commits_changed:
        print(f"🔄 Commits changed: {existing.recent_commits} → {new_summary['recent_commits']}")
    if lang_changed:
        print(f"🔄 Languages changed: {existing.languages} → {new_summary['languages']}")

    return repo_changed or commits_changed or lang_changed

def get_cached_result(username: str) -> dict | None:
    for r in results_store.values():
        if r["username"] == username:
            return r
    return None

@app.get("/")
def health_check():
    return {
        "status" : "running",
        "app"    : "AutoEval API",
        "version": "1.0.0"
    }

@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate_candidate(request: EvaluateRequest):
    username = request.username.strip()
    print(f"\n📥 Received evaluation request for: {username}")

    try:
        summary = build_profile_summary(username)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not fetch GitHub profile for '{username}': {str(e)}"
        )

    with Session(engine) as session:
        existing = session.query(CandidateProfile)\
            .filter_by(username=username).first()

        if existing:
            changed = profile_changed(existing, summary)
            if not changed:
                cached = get_cached_result(username)
                if cached:
                    print(f"✅ Cache hit — returning stored score: {cached['composite']}/100")
                    cached["cache_hit"] = True
                    return cached
                else:
                    print(f"⚠️  Profile unchanged but no cache — re-evaluating")
            else:
                print(f"🔄 Profile changed — running fresh evaluation")
        else:
            print(f"🆕 New candidate — running first evaluation")

    try:
        pipeline = build_graph()
        initial_state = CandidateState(
            username       = summary["username"],
            summary        = summary,
            llama70_scores = {},
            llama8_scores  = {},
            final_scores   = {},
            conflicts      = [],
            composite      = 0.0
        )
        result = pipeline.invoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring pipeline failed: {str(e)}"
        )

    try:
        with Session(engine) as session:
            existing = session.query(CandidateProfile)\
                .filter_by(username=username).first()

            if existing:
                existing.public_repos     = summary["public_repos"]
                existing.followers        = summary["followers"]
                existing.languages        = summary["languages"]
                existing.total_stars      = summary["total_stars"]
                existing.has_readme_count = summary["has_readme_count"]
                existing.recent_commits   = summary["recent_commits"]
                existing.top_repo         = summary["top_repo"]
                existing.bio              = summary["bio"]
                session.commit()
                print(f"✅ Updated existing profile for {username}")
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
                print(f"✅ Saved new profile for {username}")
    except Exception as e:
        print(f"⚠️ DB save warning: {e}")

    for result_id, r in list(results_store.items()):
        if r["username"] == username:
            del results_store[result_id]
            break

    result_id = str(uuid.uuid4())
    results_store[result_id] = {
        "id"          : result_id,
        "username"    : username,
        "composite"   : result["composite"],
        "final_scores": result["final_scores"],
        "conflicts"   : result["conflicts"],
        "status"      : "complete",
        "cache_hit"   : False
    }

    print(f"✅ Evaluation complete — composite: {result['composite']}/100")
    return results_store[result_id]

@app.get("/results/{result_id}")
def get_results(result_id: str):
    if result_id not in results_store:
        raise HTTPException(
            status_code=404,
            detail=f"Result '{result_id}' not found"
        )
    return results_store[result_id]

@app.get("/leaderboard")
def get_leaderboard():
    with Session(engine) as session:
        candidates = session.query(CandidateProfile).all()
    leaderboard = []
    for candidate in candidates:
        score = None
        for r in results_store.values():
            if r["username"] == candidate.username:
                score = r["composite"]
                break
        leaderboard.append({
            "username"  : candidate.username,
            "name"      : candidate.name,
            "languages" : candidate.languages,
            "top_repo"  : candidate.top_repo,
            "composite" : score if score else 0.0,
        })
    leaderboard.sort(key=lambda x: x["composite"], reverse=True)
    return leaderboard

@app.get("/cache/status")
def cache_status():
    return {
        "cached_results": len(results_store),
        "usernames": [r["username"] for r in results_store.values()]
    }