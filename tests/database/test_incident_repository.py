"""Tests for HealthIncidentRepository and HealthIncident model."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from nira_backend.data_models.health_incident import HealthIncident
from nira_backend.database.connection import DatabaseConnection
from nira_backend.database.repositories.incident_repository import HealthIncidentRepository


@pytest.fixture
def db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(db_path=tmp_path / "incident_test.db")


@pytest.fixture
def repo(db: DatabaseConnection) -> HealthIncidentRepository:
    return HealthIncidentRepository(db)


@pytest.fixture
def fever_incident() -> HealthIncident:
    return HealthIncident(
        human_name="Alice",
        incident_date=date.today(),
        description="Felt sick with a fever and sore throat",
        symptoms=["fever", "sore throat", "fatigue"],
        severity="moderate",
        incident_type="illness",
    )


@pytest.fixture
def shoulder_incident() -> HealthIncident:
    return HealthIncident(
        human_name="John",
        incident_date=date.today(),
        description="Shoulder pain after working long hours at desk",
        symptoms=["shoulder pain", "stiffness"],
        severity="mild",
        body_part="shoulder",
        incident_type="pain",
        notes="Started after 10-hour coding session",
    )


@pytest.fixture
def old_incident() -> HealthIncident:
    return HealthIncident(
        human_name="Alice",
        incident_date=date.today() - timedelta(days=45),
        description="Felt very tired",
        incident_type="fatigue",
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestIncidentRepositoryCreate:
    def test_create_returns_integer_id(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        iid = repo.create(fever_incident)
        assert isinstance(iid, int)
        assert iid >= 1

    def test_create_multiple_returns_sequential_ids(
        self,
        repo: HealthIncidentRepository,
        fever_incident: HealthIncident,
        shoulder_incident: HealthIncident,
    ) -> None:
        id1 = repo.create(fever_incident)
        id2 = repo.create(shoulder_incident)
        assert id2 > id1


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class TestIncidentRepositoryRead:
    def test_get_by_id_returns_correct_incident(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        iid = repo.create(fever_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.human_name == "Alice"
        assert fetched.incident_type == "illness"
        assert fetched.severity == "moderate"
        assert "fever" in fetched.symptoms
        assert "sore throat" in fetched.symptoms

    def test_get_by_id_returns_none_for_missing(
        self, repo: HealthIncidentRepository
    ) -> None:
        assert repo.get_by_id(9999) is None

    def test_get_all_returns_all_incidents(
        self,
        repo: HealthIncidentRepository,
        fever_incident: HealthIncident,
        shoulder_incident: HealthIncident,
    ) -> None:
        repo.create(fever_incident)
        repo.create(shoulder_incident)
        assert len(repo.get_all()) == 2

    def test_get_all_empty_returns_empty_list(
        self, repo: HealthIncidentRepository
    ) -> None:
        assert repo.get_all() == []

    def test_get_by_human_filters_by_name(
        self,
        repo: HealthIncidentRepository,
        fever_incident: HealthIncident,
        shoulder_incident: HealthIncident,
    ) -> None:
        repo.create(fever_incident)
        repo.create(shoulder_incident)
        alice_incidents = repo.get_by_human("Alice", days=7)
        assert all(i.human_name == "Alice" for i in alice_incidents)
        assert len(alice_incidents) == 1

    def test_get_by_human_respects_days_window(
        self,
        repo: HealthIncidentRepository,
        fever_incident: HealthIncident,
        old_incident: HealthIncident,
    ) -> None:
        repo.create(fever_incident)
        repo.create(old_incident)
        recent = repo.get_by_human("Alice", days=30)
        assert len(recent) == 1
        assert recent[0].description == fever_incident.description

    def test_get_by_human_partial_match(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        repo.create(fever_incident)
        results = repo.get_by_human("ali", days=7)
        assert len(results) == 1

    def test_get_by_type_filters_correctly(
        self,
        repo: HealthIncidentRepository,
        fever_incident: HealthIncident,
        shoulder_incident: HealthIncident,
    ) -> None:
        repo.create(fever_incident)
        repo.create(shoulder_incident)
        illness_results = repo.get_by_type("illness")
        assert len(illness_results) == 1
        assert illness_results[0].incident_type == "illness"

    def test_get_by_body_part_finds_shoulder(
        self, repo: HealthIncidentRepository, shoulder_incident: HealthIncident
    ) -> None:
        repo.create(shoulder_incident)
        results = repo.get_by_body_part("shoulder")
        assert len(results) == 1
        assert results[0].body_part == "shoulder"

    def test_get_by_body_part_no_match(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        repo.create(fever_incident)
        assert repo.get_by_body_part("knee") == []

    def test_symptoms_roundtrip(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        iid = repo.create(fever_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert set(fetched.symptoms) == {"fever", "sore throat", "fatigue"}

    def test_empty_symptoms_roundtrip(
        self, repo: HealthIncidentRepository, old_incident: HealthIncident
    ) -> None:
        iid = repo.create(old_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.symptoms == []

    def test_notes_preserved(
        self, repo: HealthIncidentRepository, shoulder_incident: HealthIncident
    ) -> None:
        iid = repo.create(shoulder_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.notes == "Started after 10-hour coding session"

    def test_body_part_preserved(
        self, repo: HealthIncidentRepository, shoulder_incident: HealthIncident
    ) -> None:
        iid = repo.create(shoulder_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.body_part == "shoulder"

    def test_none_body_part_stored_as_none(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        iid = repo.create(fever_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.body_part is None

    def test_none_severity_stored_as_none(
        self, repo: HealthIncidentRepository, old_incident: HealthIncident
    ) -> None:
        iid = repo.create(old_incident)
        fetched = repo.get_by_id(iid)
        assert fetched is not None
        assert fetched.severity is None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestIncidentRepositoryDelete:
    def test_delete_removes_incident(
        self, repo: HealthIncidentRepository, fever_incident: HealthIncident
    ) -> None:
        iid = repo.create(fever_incident)
        assert repo.delete(iid) is True
        assert repo.get_by_id(iid) is None

    def test_delete_nonexistent_returns_false(
        self, repo: HealthIncidentRepository
    ) -> None:
        assert repo.delete(9999) is False


# ---------------------------------------------------------------------------
# HealthIncident model validation
# ---------------------------------------------------------------------------


class TestHealthIncidentModel:
    def test_valid_incident(self) -> None:
        inc = HealthIncident(
            human_name="Alice",
            incident_date=date.today(),
            description="Mild headache",
            incident_type="pain",
        )
        assert inc.human_name == "Alice"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(Exception):
            HealthIncident(
                human_name="",
                incident_date=date.today(),
                description="Headache",
            )

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(Exception):
            HealthIncident(
                human_name="   ",
                incident_date=date.today(),
                description="Headache",
            )

    def test_short_description_raises(self) -> None:
        with pytest.raises(Exception):
            HealthIncident(
                human_name="Alice",
                incident_date=date.today(),
                description="x",
            )

    def test_symptoms_whitespace_stripped(self) -> None:
        inc = HealthIncident(
            human_name="Alice",
            incident_date=date.today(),
            description="Feeling unwell",
            symptoms=["  fever  ", " headache "],
        )
        assert inc.symptoms == ["fever", "headache"]

    def test_symptoms_empty_strings_filtered(self) -> None:
        inc = HealthIncident(
            human_name="Alice",
            incident_date=date.today(),
            description="Feeling unwell",
            symptoms=["", "  ", "fever"],
        )
        assert inc.symptoms == ["fever"]

    def test_body_part_normalised_to_lower(self) -> None:
        inc = HealthIncident(
            human_name="Alice",
            incident_date=date.today(),
            description="Shoulder ache",
            body_part="SHOULDER",
        )
        assert inc.body_part == "shoulder"

    def test_invalid_incident_type_raises(self) -> None:
        with pytest.raises(Exception):
            HealthIncident(
                human_name="Alice",
                incident_date=date.today(),
                description="Feeling sick",
                incident_type="broken_leg",  # type: ignore
            )

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(Exception):
            HealthIncident(
                human_name="Alice",
                incident_date=date.today(),
                description="Headache",
                severity="very_bad",  # type: ignore
            )

    def test_default_incident_type_is_other(self) -> None:
        inc = HealthIncident(
            human_name="Alice",
            incident_date=date.today(),
            description="Feeling off today",
        )
        assert inc.incident_type == "other"
