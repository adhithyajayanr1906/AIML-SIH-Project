"""
backend/app/history_db.py
=========================
SQLite persistence layer for NER Smart Logistics calculation history and audit reporting.

Schema:
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- created_at: TEXT (ISO8601 UTC)
- origin_name: TEXT
- origin_lat: REAL
- origin_lon: REAL
- dest_name: TEXT
- dest_lat: REAL
- dest_lon: REAL
- transport_mode: TEXT (ROADWAY | AIRWAY)
- route_mode: TEXT (SHORTEST | SAFE | DIRECT_AIR)
- distance_km: REAL
- total_cost: REAL
- segments: INTEGER
- validation_status: TEXT (PASSED | FAILED)
- confidence_score: REAL
- confidence_rating: TEXT
- risk_summary_json: TEXT (JSON string)
- validation_json: TEXT (JSON string)
- coords_json: TEXT (JSON string)
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_PATH = os.path.abspath("c:/NER-Smart-Logistics/data/route_history.db")

def init_db(db_path: str = DB_PATH) -> None:
    """Initializes SQLite database and tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS route_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                origin_name TEXT NOT NULL,
                origin_lat REAL NOT NULL,
                origin_lon REAL NOT NULL,
                dest_name TEXT NOT NULL,
                dest_lat REAL NOT NULL,
                dest_lon REAL NOT NULL,
                transport_mode TEXT NOT NULL,
                route_mode TEXT NOT NULL,
                distance_km REAL NOT NULL,
                total_cost REAL,
                segments INTEGER,
                validation_status TEXT NOT NULL,
                confidence_score REAL,
                confidence_rating TEXT,
                risk_summary_json TEXT,
                validation_json TEXT,
                coords_json TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON route_history(created_at DESC);")
        conn.commit()

def save_route_calculation(
    origin_name: str,
    origin_lat: float,
    origin_lon: float,
    dest_name: str,
    dest_lat: float,
    dest_lon: float,
    transport_mode: str,
    route_mode: str,
    distance_km: float,
    total_cost: Optional[float] = None,
    segments: Optional[int] = None,
    validation_status: str = "PASSED",
    confidence_score: Optional[float] = None,
    confidence_rating: Optional[str] = None,
    risk_summary: Optional[Dict[str, Any]] = None,
    validation_details: Optional[Dict[str, Any]] = None,
    coords: Optional[List[Any]] = None,
    db_path: str = DB_PATH
) -> int:
    """Saves a verified calculation result into SQLite history."""
    init_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO route_history (
                created_at, origin_name, origin_lat, origin_lon,
                dest_name, dest_lat, dest_lon, transport_mode, route_mode,
                distance_km, total_cost, segments, validation_status,
                confidence_score, confidence_rating,
                risk_summary_json, validation_json, coords_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso,
            origin_name or "Unknown Origin",
            origin_lat,
            origin_lon,
            dest_name or "Unknown Destination",
            dest_lat,
            dest_lon,
            transport_mode,
            route_mode,
            distance_km,
            total_cost,
            segments,
            validation_status,
            confidence_score,
            confidence_rating,
            json.dumps(risk_summary) if risk_summary else None,
            json.dumps(validation_details) if validation_details else None,
            json.dumps(coords) if coords else None
        ))
        conn.commit()
        return cursor.lastrowid

def get_route_history(limit: int = 50, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves list of saved route calculations ordered by timestamp descending."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, created_at, origin_name, origin_lat, origin_lon,
                   dest_name, dest_lat, dest_lon, transport_mode, route_mode,
                   distance_km, total_cost, segments, validation_status,
                   confidence_score, confidence_rating, risk_summary_json, validation_json
            FROM route_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "origin_name": r["origin_name"],
                "origin_lat": r["origin_lat"],
                "origin_lon": r["origin_lon"],
                "dest_name": r["dest_name"],
                "dest_lat": r["dest_lat"],
                "dest_lon": r["dest_lon"],
                "transport_mode": r["transport_mode"],
                "route_mode": r["route_mode"],
                "distance_km": r["distance_km"],
                "total_cost": r["total_cost"],
                "segments": r["segments"],
                "validation_status": r["validation_status"],
                "confidence_score": r["confidence_score"],
                "confidence_rating": r["confidence_rating"],
                "risk_summary": json.loads(r["risk_summary_json"]) if r["risk_summary_json"] else None,
                "validation": json.loads(r["validation_json"]) if r["validation_json"] else None
            })
        return results

def get_route_by_id(route_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves full route calculation details including coordinates to reopen on map."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM route_history WHERE id = ?", (route_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return {
            "id": r["id"],
            "created_at": r["created_at"],
            "origin_name": r["origin_name"],
            "origin_lat": r["origin_lat"],
            "origin_lon": r["origin_lon"],
            "dest_name": r["dest_name"],
            "dest_lat": r["dest_lat"],
            "dest_lon": r["dest_lon"],
            "transport_mode": r["transport_mode"],
            "route_mode": r["route_mode"],
            "distance_km": r["distance_km"],
            "total_cost": r["total_cost"],
            "segments": r["segments"],
            "validation_status": r["validation_status"],
            "confidence_score": r["confidence_score"],
            "confidence_rating": r["confidence_rating"],
            "risk_summary": json.loads(r["risk_summary_json"]) if r["risk_summary_json"] else None,
            "validation": json.loads(r["validation_json"]) if r["validation_json"] else None,
            "coords": json.loads(r["coords_json"]) if r["coords_json"] else []
        }

def generate_route_report_text(route: Dict[str, Any]) -> str:
    """Generates an audit-ready, plain-text intelligence report for a saved route."""
    report_lines = [
        "=" * 72,
        "NORTH EASTERN REGION SMART LOGISTICS PLATFORM",
        "INTELLIGENCE ROUTE & RISK AUDIT REPORT",
        "=" * 72,
        f"Calculation ID:   #{route.get('id', 'N/A')}",
        f"Timestamp:        {route.get('created_at', 'N/A')}",
        f"Origin:           {route.get('origin_name')} ({route.get('origin_lat')}, {route.get('origin_lon')})",
        f"Destination:      {route.get('dest_name')} ({route.get('dest_lat')}, {route.get('dest_lon')})",
        f"Transport Mode:   {route.get('transport_mode')}",
        f"Route Mode:       {route.get('route_mode')}",
        f"Distance:         {route.get('distance_km')} km",
        f"Segments:         {route.get('segments', 'N/A')}",
        f"Total Cost Index: {route.get('total_cost', 'N/A')}",
        "-" * 72,
        "CALCULATION VALIDATION & QUALITY ASSURANCE:",
        f"Validation Status: {route.get('validation_status')}",
        f"Confidence Score:  {route.get('confidence_score')}% ({route.get('confidence_rating', 'Unrated')})",
        "Disaster Predictive Accuracy: Not established (uncalibrated heuristic; no ground truth)",
        "-" * 72,
        "METHODOLOGY & LIMITATION STATEMENTS:",
        "1. Roadway distances reflect Dijkstra shortest/safe paths on OpenStreetMap graph.",
        "2. Airway distances are exact Haversine great-circle direct estimates (not flight paths).",
        "3. Confidence reflects snapping distance, component size, and covariate availability.",
        "4. Risk indices are deterministic heuristics; real-world flood predictive accuracy",
        "   is 'Not established' in the absence of verified ground-truth event labels.",
        "=" * 72,
    ]
    return "\n".join(report_lines)
