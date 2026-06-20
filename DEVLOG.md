## Day 1 — June 13, 2026

### What I built
- Created GitHub Classic PAT with public_repo + read:user scopes
- Built ingestion.py — fetches GitHub profile, repos, commits, README check
- Fixed indentation bug in for loop (mixed old + new code)
- Fixed language detection — Jupyter Notebook now maps to Python

### Output achieved
- languages: ['Python', 'HTML', 'CSS', 'Java', 'Jupyter Notebook']
- has_readme_count: 6/11 repos
- recent_commits: 33
- top_repo: cat-emotion-detection-system

### What I learned
- import, def, return, for loop, .get(), .append(), status_code
- Python indentation rule: 4 spaces per level
- GitHub API rate limit: 5000 requests/hour authenticated
- Bearer vs token header difference for PAT types

### Tomorrow
- Start Docker PostgreSQL container
- Write db.py — save profile summary to database
- Learn SQLAlchemy ORM basics


## Day 2 — June 14, 2026

### What I built
- Enabled pgvector extension inside PostgreSQL container
- Added Vector(384) column to candidates table
- Built generate_embedding() using sentence-transformers MiniLM model
- Fixed text variable name conflict with SQLAlchemy import
- Saved full profile + embedding to database
- Verified with SELECT query — row confirmed

### What I learned
- CREATE EXTENSION IF NOT EXISTS vector — enables pgvector in PostgreSQL
- SentenceTransformer.encode() converts text → 384 numbers (numpy array)
- text() in SQLAlchemy wraps raw SQL safely
- drop_all + create_all pattern to rebuild tables cleanly
- Variable name conflicts with imports cause silent bugs

### Tomorrow — Day 3
- Write schemas.py — Pydantic RubricScore model
- Start LangGraph graph.py — StateGraph with 4 nodes
- Call Claude API for first real LLM score


## Day 3 — June 15, 2026

### What I built
- schemas.py — Pydantic RubricScore model with Field validation
- graph.py — LangGraph StateGraph with 3 nodes
- Two Groq scorers: Llama3.3-70B + Llama3.1-8B
- Consensus node — averages scores, flags delta > 1.5

### Output achieved
- COMPOSITE: 47.5/100 for Harikarthik7124
- CONFLICTS: 3 detected (commit_hygiene, stack_breadth, oss_contributions)
- Pipeline: ingestion → scoring → consensus working end to end

### What I learned
- Pydantic Field(ge=0, le=10) — enforces score range
- TypedDict — shared state across LangGraph nodes
- with_structured_output() — forces LLM to return schema shape
- Conflict detection similar to backpropagation error signal
- Human-in-the-loop AI concept

### Tomorrow — Day 4
- Write main.py — FastAPI backend
- POST /evaluate endpoint
- GET /results endpoint
- GET /leaderboard endpoint
- Connect graph.py to API

## Day 4 — June 16, 2026

### What I built
- main.py — FastAPI with 4 endpoints
- POST /evaluate, GET /results/{id}, GET /leaderboard, GET /
- Fixed LLM hallucination with explicit field names in prompt
- Fixed top_repo bug — filtered profile README repo
- Fixed init_db — removed drop_all, added upsert pattern

### What I learned
- FastAPI decorators @app.post @app.get
- HTTPException 400/404/500 error codes
- CORSMiddleware — allows React frontend to call API
- uuid4() — unique result IDs
- Upsert pattern — update if exists, insert if not
- GitHub profile README repo has same name as username

### Output achieved
- API live at http://127.0.0.1:8000
- composite: 44.38/100 for Harikarthik7124
- top_repo: cat-emotion-detection-system ✅
- All 3 endpoints returning correct data

### Tomorrow — Day 5
- Build React frontend with Vite
- Input form → POST /evaluate
- RadarChart → rubric scores visualization
- Leaderboard table
- Conflict warning flags


## Day 5 — June 17, 2026

### What I built
- React frontend scaffolded with Vite
- App.jsx — search bar, RadarChart, score breakdown, conflicts accordion
- App.css — dark SaaS-style theme with proper contrast
- Unique color mapping per rubric (8 distinct colors)
- Custom Recharts tooltip with colored dots
- Responsive grid — single column on mobile, two columns on desktop

### What I learned
- useState — managing input, loading, result, error states
- axios.post() — calling FastAPI from React
- Recharts — RadarChart, custom dot rendering, custom tooltips
- CSS contrast — text-tertiary too dim, fixed with brighter scale
- Object.entries() + .map() — transforming dicts into chart data
- <details>/<summary> — native HTML accordion, no JS needed

### Output achieved
- Full working dashboard at localhost:5173
- End-to-end: type username → see scores → view conflicts
- Visually distinct rubric colors across chart, list, and conflicts

### Tomorrow — Day 6
- Write Dockerfile for backend
- Write docker-compose.yml (api + worker + redis + postgres)
- Test full stack locally with docker-compose up
- Then deploy: Railway (backend) + Vercel (frontend)