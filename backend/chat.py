import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StringConstraints

from backend.answer_question import generate_answer
from backend.auth import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

QuestionText = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
        max_length=2000,
    ),
]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: QuestionText


class SourceReference(BaseModel):
    label: str
    file: str
    version: str
    start_line: int
    end_line: int
    url: str


class ChatResponse(BaseModel):
    answer: str
    answer_language: Literal["Arabic", "English"]
    sources: list[SourceReference]


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    response: Response,
    _user: AuthenticatedUser = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"

    try:
        result = generate_answer(request.question)

        # Return only the sources actually cited in the answer.
        sources = [
            SourceReference(**source)
            for source in result["sources"]
            if f"[{source['label']}]" in result["used_labels"]
        ]

        return ChatResponse(
            answer=result["answer"],
            answer_language=result["answer_language"],
            sources=sources,
        )

    except (Exception, SystemExit) as error:
        # Avoid exposing prompts, credentials, or provider error details.
        logger.error("Chat generation failed: %s", type(error).__name__)

        raise HTTPException(
            status_code=502,
            detail="The answer could not be generated. Please try again later.",
        ) from None
