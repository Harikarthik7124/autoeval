import os
import time
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from schemas import RubricScore

load_dotenv()

# Scorer 1 — Llama3.3 70B via Groq
scorer1 = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Scorer 2 — Llama3.1 8B via Groq
scorer2 = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

scorer1_llm = scorer1.with_structured_output(RubricScore)
scorer2_llm = scorer2.with_structured_output(RubricScore)

SYSTEM_PROMPT = """You are a senior AI/ML engineer evaluating developer candidates.
You will be given a GitHub profile summary.
Score the candidate across all 8 rubrics from 0.0 to 10.0.

Rules:
- Be critical. Reserve 8-10 for genuinely exceptional candidates.
- Base scores ONLY on evidence provided. Never assume.

You MUST return exactly these 10 fields:

NUMBER fields (float 0.0 to 10.0):
- code_quality
- commit_hygiene
- documentation
- stack_breadth
- project_complexity
- recency
- oss_contributions
- ai_ml_presence

TEXT fields (must be a sentence, NEVER a number):
- reasoning: a short sentence explaining your scoring, e.g. "Strong Python projects with clear documentation"
- confidence: must be exactly one of these three words: "high", "medium", or "low"

Do NOT put numbers in reasoning or confidence fields.
Do NOT use any other field names.
"""

class CandidateState(TypedDict):
    username       : str
    summary        : dict
    llama70_scores : dict
    llama8_scores  : dict
    final_scores   : dict
    conflicts      : list
    composite      : float

def build_context(summary: dict) -> str:
    return f"""
CANDIDATE: {summary['username']}
Name: {summary['name']}
Public repos: {summary['public_repos']}
Followers: {summary['followers']}
Languages: {', '.join(summary['languages'])}
Total stars: {summary['total_stars']}
README count: {summary['has_readme_count']} out of {summary['public_repos']} repos
Recent commits: {summary['recent_commits']}
Top repo: {summary['top_repo']}
Bio: {summary['bio']}
"""

def safe_invoke(llm, messages, retries=3):
    for attempt in range(retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"⚠️  Rate limit hit — retrying in {wait}s... (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
            else:
                print(f"❌ All {retries} attempts failed")
                raise e

def scorer1_node(state: CandidateState) -> CandidateState:
    print("🦙 Llama3.3-70B scoring...")
    context = build_context(state["summary"])
    result  = safe_invoke(scorer1_llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context)
    ])
    state["llama70_scores"] = result.model_dump()
    print(f"✅ Llama3.3-70B done — code_quality: {result.code_quality}")
    return state

def scorer2_node(state: CandidateState) -> CandidateState:
    print("⚡ Llama3.1-8B scoring...")
    time.sleep(3)   # ← prevent rate limit between the two scorers
    context = build_context(state["summary"])
    result  = safe_invoke(scorer2_llm, [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context)
    ])
    state["llama8_scores"] = result.model_dump()
    print(f"✅ Llama3.1-8B done — code_quality: {result.code_quality}")
    return state

def consensus_node(state: CandidateState) -> CandidateState:
    print("⚖️  Consensus calculating...")
    g = state["llama70_scores"]
    r = state["llama8_scores"]
    rubrics = [
        "code_quality", "commit_hygiene",
        "documentation", "stack_breadth",
        "project_complexity", "recency",
        "oss_contributions", "ai_ml_presence"
    ]
    final     = {}
    conflicts = []
    for rubric in rubrics:
        avg   = round((g[rubric] + r[rubric]) / 2, 2)
        delta = round(abs(g[rubric] - r[rubric]), 2)
        final[rubric] = avg
        if delta > 1.5:
            conflicts.append({
                "rubric" : rubric,
                "llama70": g[rubric],
                "llama8" : r[rubric],
                "delta"  : delta
            })
    composite = round(sum(final.values()) / len(final) * 10, 2)
    state["final_scores"] = final
    state["conflicts"]    = conflicts
    state["composite"]    = composite
    print(f"✅ Consensus done — composite score: {composite}/100")
    return state

def build_graph():
    graph = StateGraph(CandidateState)
    graph.add_node("scorer1",   scorer1_node)
    graph.add_node("scorer2",   scorer2_node)
    graph.add_node("consensus", consensus_node)
    graph.set_entry_point("scorer1")
    graph.add_edge("scorer1",   "scorer2")
    graph.add_edge("scorer2",   "consensus")
    graph.add_edge("consensus", END)
    return graph.compile()

if __name__ == "__main__":
    from ingestion import build_profile_summary

    summary = build_profile_summary("Harikarthik7124")
    initial_state = CandidateState(
        username       = summary["username"],
        summary        = summary,
        llama70_scores = {},
        llama8_scores  = {},
        final_scores   = {},
        conflicts      = [],
        composite      = 0.0
    )
    pipeline = build_graph()
    result   = pipeline.invoke(initial_state)

    print("\n" + "="*50)
    print(f"CANDIDATE : {result['username']}")
    print(f"COMPOSITE : {result['composite']}/100")
    print("\nFINAL SCORES:")
    for rubric, score in result["final_scores"].items():
        print(f"  {rubric:25} {score}/10")
    print(f"\nCONFLICTS DETECTED: {len(result['conflicts'])}")
    for c in result["conflicts"]:
        print(f"  {c['rubric']}: Llama70B={c['llama70']} Llama8B={c['llama8']} delta={c['delta']}")