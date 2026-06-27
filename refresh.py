import os
import time
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db import engine, CandidateProfile, init_db
from ingestion import build_profile_summary
from graph import build_graph, CandidateState

load_dotenv()

def profile_changed(existing: CandidateProfile, new_summary: dict) -> bool:
    repo_changed    = existing.public_repos != new_summary["public_repos"]
    commits_changed = abs(existing.recent_commits - new_summary["recent_commits"]) > 5
    lang_changed    = set(existing.languages or []) != set(new_summary["languages"])

    if repo_changed:
        print(f"   📁 Repo count changed: {existing.public_repos} → {new_summary['public_repos']}")
    if commits_changed:
        print(f"   💾 Commits changed: {existing.recent_commits} → {new_summary['recent_commits']}")
    if lang_changed:
        print(f"   🔤 Languages changed: {existing.languages} → {new_summary['languages']}")

    return repo_changed or commits_changed or lang_changed

def refresh_all_candidates():
    print("=" * 50)
    print("🔄 AutoEval — Nightly Refresh Started")
    print("=" * 50)

    with Session(engine) as session:
        candidates = session.query(CandidateProfile).all()
        usernames  = [c.username for c in candidates]

    total     = len(usernames)
    refreshed = 0
    skipped   = 0
    failed    = 0

    print(f"📋 Found {total} candidates to check\n")

    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{total}] 👤 Checking {username}...")

        try:
            # Step 1 — fetch fresh GitHub data
            new_summary = build_profile_summary(username)

            # Step 2 — compare with stored data
            with Session(engine) as session:
                existing = session.query(CandidateProfile)\
                    .filter_by(username=username).first()

                if not existing:
                    print(f"   ⚠️  Not found in DB — skipping")
                    skipped += 1
                    continue

                changed = profile_changed(existing, new_summary)

            # Step 3 — skip if no meaningful change
            if not changed:
                print(f"   ✅ No changes detected — skipping re-score")
                skipped += 1
                continue

            # Step 4 — re-run LLM scoring pipeline
            print(f"   🤖 Profile changed — running fresh evaluation...")

            pipeline = build_graph()
            initial_state = CandidateState(
                username       = username,
                summary        = new_summary,
                llama70_scores = {},
                llama8_scores  = {},
                final_scores   = {},
                conflicts      = [],
                composite      = 0.0
            )
            result = pipeline.invoke(initial_state)

            # Step 5 — update database with fresh data + new score
            with Session(engine) as session:
                existing = session.query(CandidateProfile)\
                    .filter_by(username=username).first()

                if existing:
                    existing.public_repos     = new_summary["public_repos"]
                    existing.followers        = new_summary["followers"]
                    existing.languages        = new_summary["languages"]
                    existing.total_stars      = new_summary["total_stars"]
                    existing.has_readme_count = new_summary["has_readme_count"]
                    existing.recent_commits   = new_summary["recent_commits"]
                    existing.top_repo         = new_summary["top_repo"]
                    existing.bio              = new_summary["bio"]
                    session.commit()

            print(f"   ✅ Re-scored → {result['composite']}/100")
            refreshed += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1

        finally:
            # always wait 10s between candidates
            # prevents GitHub API + Groq rate limits
            if i < total:
                print(f"   ⏳ Waiting 10s before next candidate...")
                time.sleep(10)

    print("\n" + "=" * 50)
    print("📊 Nightly Refresh Complete")
    print("=" * 50)
    print(f"   ✅ Re-scored  : {refreshed}")
    print(f"   ⏭️  Skipped    : {skipped}")
    print(f"   ❌ Failed     : {failed}")
    print(f"   📋 Total      : {total}")
    print("=" * 50)

if __name__ == "__main__":
    init_db()
    refresh_all_candidates()