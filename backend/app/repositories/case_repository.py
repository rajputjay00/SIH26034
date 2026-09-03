from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.domain import InspectionCase, CaseStatus

class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, case: InspectionCase) -> InspectionCase:
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_by_id(self, inspection_id: str) -> Optional[InspectionCase]:
        return self.db.query(InspectionCase).filter(InspectionCase.inspection_id == inspection_id).first()

    def get_by_case_number(self, case_number: str) -> Optional[InspectionCase]:
        return self.db.query(InspectionCase).filter(InspectionCase.case_number == case_number).first()

    def list_cases(self, limit: int = 50, offset: int = 0) -> List[InspectionCase]:
        return self.db.query(InspectionCase)\
            .order_by(InspectionCase.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()

    def list_filtered_cases(
        self,
        status: Optional[str] = None,
        determination: Optional[str] = None,
        officer_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[InspectionCase], int]:
        query = self.db.query(InspectionCase)

        if status:
            query = query.filter(InspectionCase.status == status)
        if determination:
            query = query.filter(InspectionCase.overall_determination == determination)
        if officer_id:
            query = query.filter(InspectionCase.officer_id == officer_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (InspectionCase.case_number.ilike(search_pattern)) |
                (InspectionCase.inspection_id.ilike(search_pattern)) |
                (InspectionCase.notes.ilike(search_pattern))
            )

        total = query.count()
        items = query.order_by(InspectionCase.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def update_status(self, inspection_id: str, new_status: CaseStatus) -> Optional[InspectionCase]:
        case = self.get_by_id(inspection_id)
        if case:
            case.status = new_status
            self.db.commit()
            self.db.refresh(case)
        return case

