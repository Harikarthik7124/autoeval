from pydantic import BaseModel, Field
from typing import List

# ─────────────────────────────────────────
# Single rubric score returned by one LLM
# ─────────────────────────────────────────
class RubricScore(BaseModel):
    code_quality      : float = Field(ge=0.0, le=10.0)
    commit_hygiene    : float = Field(ge=0.0, le=10.0)
    documentation     : float = Field(ge=0.0, le=10.0)
    stack_breadth     : float = Field(ge=0.0, le=10.0)
    project_complexity: float = Field(ge=0.0, le=10.0)
    recency           : float = Field(ge=0.0, le=10.0)
    oss_contributions : float = Field(ge=0.0, le=10.0)
    ai_ml_presence    : float = Field(ge=0.0, le=10.0)
    reasoning         : str
    confidence        : str   # "high" | "medium" | "low"

# ─────────────────────────────────────────
# One conflict detected between two LLMs
# ─────────────────────────────────────────
class ConflictFlag(BaseModel):
    rubric : str
    gemini : float
    groq   : float
    delta  : float   # difference between the two scores

# ─────────────────────────────────────────
# Final result after consensus
# ─────────────────────────────────────────
class CandidateResult(BaseModel):
    username      : str
    gemini_scores : RubricScore
    groq_scores   : RubricScore
    final_scores  : dict
    conflicts     : List[ConflictFlag]
    composite     : float   # single score 0-100 for leaderboard