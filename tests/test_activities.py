"""
Backend tests for Mergington High School Activities API
Tests follow the AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
import copy

# Store original activities data
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


@pytest.fixture
def client():
    """Fixture para proporcionar TestClient"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Fixture para resetear la base de datos antes de cada prueba"""
    from src.app import activities
    # Guardar estado original
    original = copy.deepcopy(ORIGINAL_ACTIVITIES)
    yield
    # Restaurar estado después de la prueba
    activities.clear()
    activities.update(copy.deepcopy(original))


class TestGetActivities:
    """Pruebas para GET /activities"""

    def test_get_all_activities_returns_200(self, client):
        """AAA Test: Verifica que GET /activities devuelve todas las actividades"""
        # Arrange
        expected_activities_count = 3  # En la data inicial hay al menos 3

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= expected_activities_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_has_correct_structure(self, client):
        """AAA Test: Verifica la estructura correcta de una actividad"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert all(field in activity_data for field in required_fields)
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_participants_are_strings(self, client):
        """AAA Test: Verifica que los participantes sean emails (strings)"""
        # Arrange
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_data in activities.values():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Email validation basic


class TestSignupActivity:
    """Pruebas para POST /activities/{activity_name}/signup"""

    def test_signup_new_participant_returns_200(self, client):
        """AAA Test: Registrar un nuevo participante devuelve 200"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_participant_added_to_activity(self, client):
        """AAA Test: El participante se añade correctamente a la lista"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        response = client.get("/activities")

        # Assert
        activities = response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """AAA Test: Registrar en actividad inexistente devuelve 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_participant_returns_400(self, client):
        """AAA Test: Registrar dos veces devuelve 400"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Ya registrado

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_missing_email_returns_error(self, client):
        """AAA Test: Registrar sin email devuelve error"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup"
            # Sin parámetro email
        )

        # Assert
        assert response.status_code != 200


class TestRemoveParticipant:
    """Pruebas para DELETE /activities/{activity_name}/participant/remove"""

    def test_remove_existing_participant_returns_200(self, client):
        """AAA Test: Eliminar un participante existente devuelve 200"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Ya existe

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]

    def test_remove_participant_deleted_from_activity(self, client):
        """AAA Test: El participante se elimina correctamente"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )
        response = client.get("/activities")

        # Assert
        activities = response.json()
        assert email not in activities[activity_name]["participants"]

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """AAA Test: Eliminar de actividad inexistente devuelve 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_nonexistent_participant_returns_404(self, client):
        """AAA Test: Eliminar participante inexistente devuelve 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_same_participant_twice_returns_404(self, client):
        """AAA Test: Eliminar dos veces el mismo participante falla"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act - Primer eliminar (exitoso)
        client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )
        # Segundo intento (fallido)
        response = client.delete(
            f"/activities/{activity_name}/participant/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
