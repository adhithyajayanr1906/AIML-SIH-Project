import pytest
from database.database import (
    init_db,
    add_field_report,
    get_all_reports,
    get_blocked_routes
)

def test_database_init():
    init_db()
    reports = get_all_reports()
    assert isinstance(reports, list)

def test_add_field_report_and_blockage():
    rep = add_field_report(
        latitude=25.5788,
        longitude=91.8933,
        location_name="Shillong Highway Pass",
        incident_type="Road Blocked",
        severity="Critical",
        description="Massive landslide debris blocking corridor",
        route_id="Guwahati - Shillong",
        reporter_name="PyTest Agent"
    )
    assert rep["id"] is not None
    assert rep["severity"] == "Critical"

    blocked = get_blocked_routes()
    assert "Guwahati - Shillong" in blocked
