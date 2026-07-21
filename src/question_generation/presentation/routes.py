import os
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db

# Core Services
from question_generation.ingestion_parser.pdf_parser_service import PdfParserService
from question_generation.application.services.gemini_llm_provider import GeminiLlmProvider
from question_generation.application.services.embedding_service import EmbeddingService
from question_generation.application.services.question_generation_service import QuestionGenerationService
from question_generation.application.services.question_validation_service import QuestionValidationService

# Repositories
from question_generation.repository.textbook_repository import TextbookRepository
from question_generation.repository.question_repository import QuestionRepository
from question_generation.repository.pg_vector_store import PgVectorStore

# Validation rules
from question_generation.question_validation.option_validator import OptionValidator
from question_generation.question_validation.explanation_validator import ExplanationValidator
from question_generation.question_validation.duplicate_validator import DuplicateValidator
from question_generation.question_validation.bloom_validator import BloomValidator
from question_generation.question_validation.difficulty_validator import DifficultyValidator

# Orchestrators
from question_generation.application.orchestrator.ingest_textbook_orchestrator import IngestTextbookOrchestrator
from question_generation.application.orchestrator.generate_questions_orchestrator import GenerateQuestionsOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

# --- DEPENDENCY INJECTION HELPERS ---

def get_ingest_orchestrator(db: Session = Depends(get_db)) -> IngestTextbookOrchestrator:
    """Dependency provider for IngestTextbookOrchestrator."""
    parser = PdfParserService()
    llm_provider = GeminiLlmProvider()
    embedding_service = EmbeddingService(llm_provider)
    repo = TextbookRepository(db)
    return IngestTextbookOrchestrator(parser, embedding_service, repo)

def get_generate_orchestrator(db: Session = Depends(get_db)) -> GenerateQuestionsOrchestrator:
    """Dependency provider for GenerateQuestionsOrchestrator."""
    llm_provider = GeminiLlmProvider()
    embedding_service = EmbeddingService(llm_provider)
    vector_store = PgVectorStore(TextbookRepository(db))
    generation_service = QuestionGenerationService(llm_provider)
    
    # Instantiate validators
    opt_val = OptionValidator()
    exp_val = ExplanationValidator()
    dup_val = DuplicateValidator(QuestionRepository(db), embedding_service)
    bloom_val = BloomValidator(llm_provider)
    diff_val = DifficultyValidator(llm_provider)
    
    validation_service = QuestionValidationService(
        option_validator=opt_val,
        explanation_validator=exp_val,
        duplicate_validator=dup_val,
        bloom_validator=bloom_val,
        difficulty_validator=diff_val
    )
    
    repo = QuestionRepository(db)
    return GenerateQuestionsOrchestrator(vector_store, embedding_service, generation_service, validation_service, repo)

# --- REQUEST SCHEMAS ---

class GenerateQuestionsRequestModel(BaseModel):
    subject: str
    chapter: str
    concept: str
    difficulty: str
    target_count: int
    exam_type: Optional[str] = None

# --- HTTP ENDPOINTS ---

@router.post("/ingest", status_code=202)
def ingest_textbook(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    subject_name: str = Form(...),
    author: Optional[str] = Form(None),
    exam_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    orchestrator: IngestTextbookOrchestrator = Depends(get_ingest_orchestrator)
):
    """
    HTTP Form endpoint accepting textbook uploads.
    Fires the ingestion pipeline asynchronously in a background task to prevent request timeouts.
    """
    # Create temporary uploads folder inside the workspace workspace
    uploads_dir = os.path.join(os.getcwd(), "temp_uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    temp_file_path = os.path.join(uploads_dir, file.filename)
    
    # Save the uploaded file locally
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Define background execution closure
    def run_ingestion_pipeline():
        try:
            result = orchestrator.execute(
                file_path=temp_file_path,
                title=title,
                subject_name=subject_name,
                author=author,
                exam_type=exam_type
            )
            logger.info(f"Asynchronous textbook ingestion complete: {result}")
        except Exception as e:
            logger.error(f"Asynchronous textbook ingestion failed: {str(e)}")
        finally:
            # Clean up the temporary upload file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    # Queue task for execution
    background_tasks.add_task(run_ingestion_pipeline)

    return {
        "status": "processing",
        "message": f"Textbook '{title}' uploaded successfully. Ingestion pipeline has started in the background."
    }

@router.post("/generate")
def generate_questions(
    request: GenerateQuestionsRequestModel,
    orchestrator: GenerateQuestionsOrchestrator = Depends(get_generate_orchestrator)
):
    """
    JSON API endpoint to generate, validate, and store a batch of questions from textbook context.
    """
    result = orchestrator.execute(
        subject=request.subject,
        chapter=request.chapter,
        concept=request.concept,
        difficulty=request.difficulty,
        target_count=request.target_count,
        exam_type=request.exam_type
    )
    return result
