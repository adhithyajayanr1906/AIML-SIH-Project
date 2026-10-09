import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import DB_PATH
from database.models import Base, FieldReportModel

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DB_PATH}")

def add_field_report(
    latitude: float,
    longitude: float,
    location_name: str,
    incident_type: str,
    severity: str,
    description: str = "",
    route_id: str = "",
    reporter_name: str = "Field Agent",
    problem_type: str = None
) -> Dict[str, Any]:
    init_db()
    session = SessionLocal()
    
    actual_incident_type = incident_type or problem_type or "Road Blocked"
    
    report = FieldReportModel(
        latitude=float(latitude),
        longitude=float(longitude),
        location_name=location_name,
        incident_type=actual_incident_type,
        severity=severity,
        description=description,
        route_id=route_id,
        reporter_name=reporter_name,
        created_at=datetime.utcnow(),
        status="Active"
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    res = report.to_dict()
    session.close()
    return res

def get_all_reports() -> List[Dict[str, Any]]:
    init_db()
    session = SessionLocal()
    reports = session.query(FieldReportModel).order_by(FieldReportModel.created_at.desc()).all()
    res = [r.to_dict() for r in reports]
    session.close()
    return res

def get_blocked_routes() -> List[str]:
    """
    Retrieve route IDs that are currently affected by Critical/High severity reports
    or explicit Road Blocked incidents.
    """
    reports = get_all_reports()
    blocked = set()
    for r in reports:
        if r.get("status") == "Active":
            sev = str(r.get("severity", "")).lower()
            inc = str(r.get("incident_type", "") or r.get("problem_type", "")).lower()
            if sev in ["critical", "high"] or "blocked" in inc or "landslide" in inc or "bridge" in inc:
                route_id = r.get("route_id")
                if route_id:
                    blocked.add(route_id)
    return list(blocked)

if __name__ == "__main__":
    init_db()
    reports = get_all_reports()
    print(f"Total reports in database: {len(reports)}")
