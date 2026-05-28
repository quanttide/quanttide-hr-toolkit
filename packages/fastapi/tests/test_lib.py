from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_quanttide_hr.database import Base, get_db as lib_get_db
from fastapi_quanttide_hr.models.recruitment import Recruitment
from fastapi_quanttide_hr.models.talent import STATUS_TRANSITIONS, Talent, TalentStatus
from fastapi_quanttide_hr.schemas.recruitment import RecruitmentRead
from fastapi_quanttide_hr.schemas.talent import TalentCreate, TalentRead, TalentTransition, TalentUpdate
from fastapi_quanttide_hr.services.pipeline import _talent_to_card, get_pipeline
from fastapi_quanttide_hr.routers import pipeline, recruitments


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        os.unlink(db_path)


@pytest.fixture
def client():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def app_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.dependency_overrides[lib_get_db] = app_get_db
    app.include_router(recruitments.router)
    app.include_router(pipeline.router)
    yield TestClient(app)
    os.unlink(db_path)


# ── Database layer ──

def test_database_base():
    assert Base is not None


def test_get_db_unimplemented():
    with pytest.raises(NotImplementedError):
        next(lib_get_db())


# ── Models ──

def test_recruitment_model(db):
    r = Recruitment()
    db.add(r)
    db.flush()
    assert r.id is not None
    assert r.created_at is not None


def test_talent_model(db):
    r = Recruitment()
    db.add(r)
    db.flush()
    t = Talent(recruitment_id=r.id, email="a@b.com", real_name="测试")
    db.add(t)
    db.flush()
    assert t.id is not None
    assert t.status == TalentStatus.NEW
    assert t.email == "a@b.com"
    assert t.real_name == "测试"
    assert t.created_at is not None
    assert t.updated_at is not None


def test_talent_status_values():
    assert TalentStatus.NEW.value == "new"
    assert TalentStatus.CONTACTED.value == "contacted"
    assert TalentStatus.EXAM_SENT.value == "exam_sent"
    assert TalentStatus.EXAM_RECEIVED.value == "exam_received"
    assert TalentStatus.EVALUATING.value == "evaluating"
    assert TalentStatus.INTERVIEW.value == "interview"
    assert TalentStatus.OFFER.value == "offer"
    assert TalentStatus.CLOSED.value == "closed"


def test_status_transitions_valid():
    assert TalentStatus.CONTACTED in STATUS_TRANSITIONS[TalentStatus.NEW]
    assert TalentStatus.CLOSED in STATUS_TRANSITIONS[TalentStatus.NEW]
    assert TalentStatus.NEW not in STATUS_TRANSITIONS[TalentStatus.CONTACTED]
    assert TalentStatus.NEW not in STATUS_TRANSITIONS[TalentStatus.CLOSED]


def test_status_transitions_all():
    assert STATUS_TRANSITIONS[TalentStatus.NEW] == [TalentStatus.CONTACTED, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.CONTACTED] == [TalentStatus.EXAM_SENT, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.EXAM_SENT] == [TalentStatus.EXAM_RECEIVED, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.EXAM_RECEIVED] == [TalentStatus.EVALUATING, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.EVALUATING] == [TalentStatus.INTERVIEW, TalentStatus.EXAM_SENT, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.INTERVIEW] == [TalentStatus.OFFER, TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.OFFER] == [TalentStatus.CLOSED]
    assert STATUS_TRANSITIONS[TalentStatus.CLOSED] == []


# ── Schemas ──

def test_schema_talent_create():
    s = TalentCreate(email="a@b.com", real_name="张三")
    assert s.email == "a@b.com"
    assert s.real_name == "张三"
    assert s.model_dump() == {"email": "a@b.com", "real_name": "张三"}


def test_schema_talent_read():
    s = TalentRead(id=1, recruitment_id=1, email="a@b.com", real_name="张三", status=TalentStatus.NEW, created_at="2026-01-01T00:00:00")
    assert s.email == "a@b.com"


def test_schema_talent_update():
    s = TalentUpdate(email="new@b.com")
    assert s.email == "new@b.com"
    assert s.real_name is None


def test_schema_talent_update_empty():
    s = TalentUpdate()
    assert s.email is None
    assert s.real_name is None


def test_schema_talent_transition():
    s = TalentTransition(status=TalentStatus.CONTACTED)
    assert s.status == TalentStatus.CONTACTED


def test_schema_recruitment_read():
    s = RecruitmentRead(id=1, created_at="2026-01-01T00:00:00")
    assert s.id == 1


# ── Pipeline Service ──

def test_pipeline_empty(db):
    result = get_pipeline(db)
    assert result["summary"]["total"] == 0
    assert result["summary"]["need_attention"] == 0
    for s in TalentStatus:
        assert result["stages"][s.value] == []


def test_pipeline_with_talent(db):
    r = Recruitment()
    db.add(r)
    db.flush()
    t = Talent(recruitment_id=r.id, email="a@b.com", real_name="测试")
    db.add(t)
    db.commit()

    result = get_pipeline(db)
    assert result["summary"]["total"] == 1
    assert result["stages"]["new"][0]["email"] == "a@b.com"
    assert result["stages"]["new"][0]["real_name"] == "测试"
    assert result["stages"]["new"][0]["status"] == "new"
    assert result["stages"]["new"][0]["recruitment_id"] == r.id


def test_pipeline_need_attention(db):
    r = Recruitment()
    db.add(r)
    db.flush()
    for email, status in [("e1@t.com", TalentStatus.EXAM_RECEIVED), ("e2@t.com", TalentStatus.EVALUATING), ("new@t.com", TalentStatus.NEW)]:
        t = Talent(recruitment_id=r.id, email=email, real_name="T", status=status)
        db.add(t)
    db.commit()

    result = get_pipeline(db)
    assert result["summary"]["total"] == 3
    assert result["summary"]["need_attention"] == 2


def test_talent_to_card(db):
    r = Recruitment()
    db.add(r)
    db.flush()
    t = Talent(recruitment_id=r.id, email="c@d.com", real_name="卡")
    db.add(t)
    db.flush()

    card = _talent_to_card(t)
    assert card["id"] == t.id
    assert card["email"] == "c@d.com"
    assert card["real_name"] == "卡"
    assert card["recruitment_id"] == r.id
    assert card["status"] == "new"
    assert "created_at" in card


# ── API ──

def test_create_recruitment(client):
    r = client.post("/recruitments")
    assert r.status_code == 201
    assert "id" in r.json()


def test_list_recruitments_empty(client):
    r = client.get("/recruitments")
    assert r.status_code == 200
    assert r.json() == []


def test_list_recruitments(client):
    client.post("/recruitments")
    r = client.get("/recruitments")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_recruitment(client):
    created = client.post("/recruitments").json()
    r = client.get(f"/recruitments/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_recruitment_404(client):
    r = client.get("/recruitments/999")
    assert r.status_code == 404


def test_delete_recruitment(client):
    created = client.post("/recruitments").json()
    r = client.delete(f"/recruitments/{created['id']}")
    assert r.status_code == 204
    r = client.get(f"/recruitments/{created['id']}")
    assert r.status_code == 404


def test_delete_recruitment_404(client):
    r = client.delete("/recruitments/999")
    assert r.status_code == 404


def test_create_talent(client):
    rec_id = client.post("/recruitments").json()["id"]
    r = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "张三"})
    assert r.status_code == 201
    assert r.json()["status"] == "new"
    assert r.json()["email"] == "a@b.com"


def test_create_talent_invalid_recruitment(client):
    r = client.post("/recruitments/999/talents", json={"email": "a@b.com", "real_name": "X"})
    assert r.status_code == 404


def test_list_talents(client):
    rec_id = client.post("/recruitments").json()["id"]
    client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"})
    client.post(f"/recruitments/{rec_id}/talents", json={"email": "b@b.com", "real_name": "B"})
    r = client.get(f"/recruitments/{rec_id}/talents")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_talents_recruitment_not_found(client):
    r = client.get("/recruitments/999/talents")
    assert r.status_code == 404


def test_list_talents_filter_by_status(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    client.post(f"/recruitments/{rec_id}/talents", json={"email": "b@b.com", "real_name": "B"})
    client.post(f"/recruitments/{rec_id}/talents/{t['id']}/transition", json={"status": "contacted"})
    r = client.get(f"/recruitments/{rec_id}/talents?status=contacted")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_talent(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    r = client.get(f"/recruitments/{rec_id}/talents/{t['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == t["id"]


def test_get_talent_404(client):
    rec_id = client.post("/recruitments").json()["id"]
    r = client.get(f"/recruitments/{rec_id}/talents/999")
    assert r.status_code == 404


def test_update_talent(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    r = client.patch(f"/recruitments/{rec_id}/talents/{t['id']}", json={"email": "new@b.com", "real_name": "B"})
    assert r.status_code == 200
    assert r.json()["email"] == "new@b.com"
    assert r.json()["real_name"] == "B"


def test_update_talent_partial(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    r = client.patch(f"/recruitments/{rec_id}/talents/{t['id']}", json={"real_name": "B"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"
    assert r.json()["real_name"] == "B"


def test_update_talent_404(client):
    rec_id = client.post("/recruitments").json()["id"]
    r = client.patch(f"/recruitments/{rec_id}/talents/999", json={"email": "x@y.com"})
    assert r.status_code == 404


def test_delete_talent(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    r = client.delete(f"/recruitments/{rec_id}/talents/{t['id']}")
    assert r.status_code == 204
    r = client.get(f"/recruitments/{rec_id}/talents")
    assert r.json() == []


def test_delete_talent_404(client):
    rec_id = client.post("/recruitments").json()["id"]
    r = client.delete(f"/recruitments/{rec_id}/talents/999")
    assert r.status_code == 404


def test_transition_full_chain(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    for status in ["contacted", "exam_sent", "exam_received", "evaluating", "interview", "offer", "closed"]:
        r = client.post(f"/recruitments/{rec_id}/talents/{t['id']}/transition", json={"status": status})
        assert r.status_code == 200
        assert r.json()["status"] == status


def test_transition_invalid(client):
    rec_id = client.post("/recruitments").json()["id"]
    t = client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"}).json()
    r = client.post(f"/recruitments/{rec_id}/talents/{t['id']}/transition", json={"status": "offer"})
    assert r.status_code == 400
    assert "Cannot transition" in r.json()["detail"]


def test_transition_404(client):
    rec_id = client.post("/recruitments").json()["id"]
    r = client.post(f"/recruitments/{rec_id}/talents/999/transition", json={"status": "contacted"})
    assert r.status_code == 404


def test_pipeline_api(client):
    rec_id = client.post("/recruitments").json()["id"]
    client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"})
    r = client.get("/pipeline")
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 1
    assert "stages" in data
    assert "summary" in data


def test_cascade_delete(client):
    rec_id = client.post("/recruitments").json()["id"]
    client.post(f"/recruitments/{rec_id}/talents", json={"email": "a@b.com", "real_name": "A"})
    client.delete(f"/recruitments/{rec_id}")
    r = client.get(f"/recruitments/{rec_id}/talents")
    assert r.status_code == 404
