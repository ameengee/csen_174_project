import os

import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.server.rate_limit import RateLimit, limiter

router = APIRouter()


class TailorRequest(BaseModel):
    resume: str
    job_description: str


@router.post("/")
@limiter.limit(RateLimit.AI)
async def tailor_resume(request: Request, req: TailorRequest):
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are an expert technical recruiter. 
        Compare this master resume to the job description below. 
        Rewrite the top 3 bullet points of the resume to perfectly highlight the skills most relevant to this specific job. 
        Keep it professional, action-oriented, and truthful. Do not invent experience.
        
        JOB DESCRIPTION:
        {req.job_description}
        
        MASTER RESUME:
        {req.resume}
        """

        response = model.generate_content(prompt)
        return {"tailored_text": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
