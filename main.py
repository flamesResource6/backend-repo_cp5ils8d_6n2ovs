import os
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import create_document

app = FastAPI(title="WINX Fairy Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnswerSubmission(BaseModel):
    name: str
    answers: List[str]

FAIRY_TYPES = {
    "Bloom": {
        "title": "Fairy of the Dragon Flame",
        "aura": "#ff6b6b",
        "blurb": "Blazing heart, fearless spirit, and a destiny that lights the way.",
    },
    "Stella": {
        "title": "Fairy of the Shining Sun",
        "aura": "#ffd166",
        "blurb": "Radiant charm, dazzling style, and sunshine that follows you around.",
    },
    "Flora": {
        "title": "Fairy of Nature",
        "aura": "#7bd88f",
        "blurb": "Gentle growth, deep roots, and a kindness that heals.",
    },
    "Musa": {
        "title": "Fairy of Music",
        "aura": "#6c63ff",
        "blurb": "Rhythm in your veins, harmony in your soul, and vibes that never miss.",
    },
    "Tecna": {
        "title": "Fairy of Technology",
        "aura": "#5cc8ff",
        "blurb": "Logic meets magic — inventive, precise, and brilliantly curious.",
    },
    "Aisha": {
        "title": "Fairy of Waves",
        "aura": "#00d1b2",
        "blurb": "Fluid strength, fearless motion, and tides that answer your call.",
    },
}

QUIZ_QUESTIONS = [
    {
        "id": "setting",
        "question": "The Moon whispers a challenge. Where do you accept it?",
        "options": [
            {"key": "bloom", "label": "On a balcony lit by starlight — heart blazing."},
            {"key": "stella", "label": "In a mirror maze — only light will guide me."},
            {"key": "flora", "label": "Among glowing flowers — the forest approves."},
            {"key": "musa", "label": "Backstage — a song will steady me."},
            {"key": "tecna", "label": "In a lab — I love a good puzzle."},
            {"key": "aisha", "label": "By the sea — the waves are on my side."},
        ],
    },
    {
        "id": "artifact",
        "question": "Choose the artifact that calls your name.",
        "options": [
            {"key": "bloom", "label": "A warm ember that never dies."},
            {"key": "stella", "label": "A prism shimmering with dawn."},
            {"key": "flora", "label": "A seed that glows when held."},
            {"key": "musa", "label": "A note crystal that hums softly."},
            {"key": "tecna", "label": "A cube that rearranges itself."},
            {"key": "aisha", "label": "A vial of living water."},
        ],
    },
    {
        "id": "trial",
        "question": "A playful spirit tests you — how do you respond?",
        "options": [
            {"key": "bloom", "label": "Lead with courage and warmth."},
            {"key": "stella", "label": "Charm them with wit and glow."},
            {"key": "flora", "label": "Offer kindness and patience."},
            {"key": "musa", "label": "Turn it into a rhythm and dance."},
            {"key": "tecna", "label": "Outsmart them with logic."},
            {"key": "aisha", "label": "Meet them head-on with agility."},
        ],
    },
    {
        "id": "companion",
        "question": "Pick your tiny familiar in the dark woods.",
        "options": [
            {"key": "bloom", "label": "A phoenix hatchling."},
            {"key": "stella", "label": "A giggling sun-mote."},
            {"key": "flora", "label": "A mossy sprite."},
            {"key": "musa", "label": "A beatboxing moth."},
            {"key": "tecna", "label": "A clicking data-firefly."},
            {"key": "aisha", "label": "A bubble-riding seahorse."},
        ],
    },
]

SCORES = {
    "bloom": "Bloom",
    "stella": "Stella",
    "flora": "Flora",
    "musa": "Musa",
    "tecna": "Tecna",
    "aisha": "Aisha",
}

@app.get("/")
def read_root():
    return {"message": "WINX Fairy Finder API is live"}

@app.get("/api/quiz/questions")
def get_questions():
    return {"questions": QUIZ_QUESTIONS}

@app.post("/api/quiz/submit")
def submit_quiz(payload: AnswerSubmission):
    if len(payload.answers) != len(QUIZ_QUESTIONS):
        raise HTTPException(status_code=400, detail="Answer count does not match question count")

    # Tally
    tally: Dict[str, int] = {k: 0 for k in SCORES.keys()}
    for ans in payload.answers:
        if ans in tally:
            tally[ans] += 1

    # Determine winner
    top_key = max(tally, key=lambda k: tally[k])
    fairy = SCORES[top_key]
    meta = FAIRY_TYPES[fairy]

    # Save result
    try:
        from schemas import QuizResult
        doc = QuizResult(
            name=payload.name,
            answers=payload.answers,
            fairy_type=fairy,
            score_breakdown={k: int(v) for k, v in tally.items()},
            aura_color=meta["aura"],
        )
        create_document("quizresult", doc)
    except Exception:
        # Database optional; continue even if not configured
        pass

    return {
        "fairy": fairy,
        "title": meta["title"],
        "aura": meta["aura"],
        "blurb": meta["blurb"],
        "tally": tally,
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
