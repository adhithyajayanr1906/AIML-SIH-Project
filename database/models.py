from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FieldReportModel(Base):
    __tablename__ = "field_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(150), nullable=False)
    incident_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500), nullable=True)
    route_id = Column(String(100), nullable=True)
    reporter_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="Active")

    def to_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "incident_type": self.incident_type,
            "problem_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "route_id": self.route_id,
            "reporter_name": self.reporter_name,
            "timestamp": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "status": self.status
        }
