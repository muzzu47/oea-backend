from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from question_generation.domain.question import Question
from question_generation.repository.database_models import QuestionModel

class QuestionRepository:
    """
    Repository responsible for handling all database operations (CRUD) for Questions.
    """

    def __init__(self, db: Session):
        self.db = db

    def save(self, question: Question) -> QuestionModel:
        """
        Saves a generated domain Question to the database.
        Translates the domain dataclass into the SQLAlchemy database model.
        """
        db_question = QuestionModel(
            subject=question.subject,
            chapter=question.chapter,
            topic=question.topic,
            concept=question.concept,
            topic_weightage=question.topic_weightage,
            question=question.question,
            options=question.options,
            correct_answer=question.correct_answer,
            solution=question.solution,
            difficulty_level=question.difficulty_level,
            question_type=question.question_type,
            exam_type=question.exam_type,
            generated_by=question.generated_by,
            validation_status=question.validation_status,
            validator_remarks=question.validator_remarks,
            source_chunk_id=question.source_chunk_id,
            is_active=question.is_active,
            usage_count=question.usage_count,
            embedding=question.embedding
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)
        return db_question

    def get_by_id(self, question_id: int) -> Optional[QuestionModel]:
        """
        Retrieves a question by its primary key ID.
        """
        stmt = select(QuestionModel).where(QuestionModel.id == question_id)
        return self.db.scalars(stmt).first()

    def get_questions_for_cbt(
        self,
        subject: str,
        exam_type: str,
        count: int,
        difficulty_level: Optional[str] = None,
        chapter: Optional[str] = None,
        concept: Optional[str] = None
    ) -> List[QuestionModel]:
        """
        Retrieves active questions for compilation into an exam (CBT module).
        Utilizes the composite index for maximum speed.
        """
        stmt = select(QuestionModel).where(
            QuestionModel.subject == subject,
            QuestionModel.exam_type == exam_type,
            QuestionModel.is_active == True  # Only fetch active questions
        )
        
        if difficulty_level:
            stmt = stmt.where(QuestionModel.difficulty_level == difficulty_level)
        if chapter:
            stmt = stmt.where(QuestionModel.chapter == chapter)
        if concept:
            stmt = stmt.where(QuestionModel.concept == concept)
            
        stmt = stmt.limit(count)
        return list(self.db.scalars(stmt).all())

    def update_validation_status(
        self, 
        question_id: int, 
        status: str, 
        remarks: str
    ) -> bool:
        """
        Updates the validation status and remarks of a question.
        Returns True if successful, False if question was not found.
        """
        stmt = (
            update(QuestionModel)
            .where(QuestionModel.id == question_id)
            .values(validation_status=status, validator_remarks=remarks)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def get_most_similar_question_with_distance(
        self,
        query_embedding: List[float],
        subject: str
    ) -> Optional[tuple[QuestionModel, float]]:
        """
        Retrieves the single most similar question in the database and returns
        a tuple containing the (QuestionModel, distance_float).
        Cosine distance values: 0 is identical, 2 is opposite.
        """
        # Calculate distance column
        distance_col = QuestionModel.embedding.cosine_distance(query_embedding)
        
        stmt = (
            select(QuestionModel, distance_col)
            .where(
                QuestionModel.subject == subject,
                QuestionModel.is_active == True,
                QuestionModel.embedding.isnot(None)
            )
            .order_by(distance_col)
            .limit(1)
        )
        
        result = self.db.execute(stmt).first()
        # Returns: (QuestionModel, distance) or None
        return result
