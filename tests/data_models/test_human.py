"""Tests for the Human data model."""
import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from nira_backend.data_models.human import Human


class TestHumanCreation:
    """Tests for creating Human instances."""
    
    def test_create_valid_human(self):
        """Test creating a valid Human instance."""
        human = Human(
            name="John Doe",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=75.5,
            height=175.0
        )
        assert human.name == "John Doe"
        assert human.gender == "male"
        assert human.date_of_birth == date(1990, 5, 15)
        assert human.weight == 75.5
        assert human.height == 175.0
    
    def test_create_human_with_female_gender(self):
        """Test creating a Human with female gender."""
        human = Human(
            name="Jane Smith",
            gender="female",
            date_of_birth=date(1985, 3, 20),
            weight=65.0,
            height=165.0
        )
        assert human.gender == "female"
    
    def test_create_human_with_undisclosed_gender(self):
        """Test creating a Human with undisclosed gender."""
        human = Human(
            name="Alex Johnson",
            gender="undisclosed",
            date_of_birth=date(1995, 7, 10),
            weight=70.0,
            height=170.0
        )
        assert human.gender == "undisclosed"


class TestHumanNameValidation:
    """Tests for name validation."""
    
    def test_name_cannot_be_empty(self):
        """Test that name cannot be an empty string."""
        with pytest.raises(ValidationError) as exc_info:
            Human(
                name="",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=175.0
            )
        # Empty string caught by min_length validation first
        assert "at least 1 character" in str(exc_info.value)
    
    def test_name_cannot_be_whitespace_only(self):
        """Test that name cannot be only whitespace."""
        with pytest.raises(ValidationError) as exc_info:
            Human(
                name="   ",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=175.0
            )
        assert "Name cannot be empty or just whitespace" in str(exc_info.value)
    
    def test_name_strips_whitespace(self):
        """Test that name is stripped of leading/trailing whitespace."""
        human = Human(
            name="  John Doe  ",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=75.5,
            height=175.0
        )
        assert human.name == "John Doe"


class TestHumanGenderValidation:
    """Tests for gender validation."""
    
    def test_invalid_gender_raises_error(self):
        """Test that invalid gender raises ValidationError."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="other",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=175.0
            )


class TestHumanDateOfBirthValidation:
    """Tests for date of birth validation."""
    
    def test_future_date_raises_error(self):
        """Test that future date of birth raises error."""
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=future_date,
                weight=75.5,
                height=175.0
            )
        assert "Date of birth cannot be later than today" in str(exc_info.value)
    
    def test_too_old_date_raises_error(self):
        """Test that date of birth more than 150 years ago raises error."""
        old_date = date.today() - timedelta(days=151 * 365)
        with pytest.raises(ValidationError) as exc_info:
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=old_date,
                weight=75.5,
                height=175.0
            )
        assert "Date of birth cannot be more than 150 years ago" in str(exc_info.value)
    
    def test_today_date_is_valid(self):
        """Test that today's date is valid for date of birth."""
        human = Human(
            name="Baby Doe",
            gender="male",
            date_of_birth=date.today(),
            weight=3.5,
            height=50.0
        )
        assert human.date_of_birth == date.today()


class TestHumanWeightValidation:
    """Tests for weight validation."""
    
    def test_negative_weight_raises_error(self):
        """Test that negative weight raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=-5.0,
                height=175.0
            )
    
    def test_zero_weight_raises_error(self):
        """Test that zero weight raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=0.0,
                height=175.0
            )
    
    def test_weight_above_max_raises_error(self):
        """Test that weight above 500 kg raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=501.0,
                height=175.0
            )
    
    def test_minimum_valid_weight(self):
        """Test that weight just above 0.5 kg is valid."""
        human = Human(
            name="Baby Doe",
            gender="male",
            date_of_birth=date.today(),
            weight=0.6,
            height=40.0
        )
        assert human.weight == 0.6


class TestHumanHeightValidation:
    """Tests for height validation."""
    
    def test_negative_height_raises_error(self):
        """Test that negative height raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=-10.0
            )
    
    def test_height_below_minimum_raises_error(self):
        """Test that height below 30 cm raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=25.0
            )
    
    def test_height_above_maximum_raises_error(self):
        """Test that height above 300 cm raises error."""
        with pytest.raises(ValidationError):
            Human(
                name="John Doe",
                gender="male",
                date_of_birth=date(1990, 5, 15),
                weight=75.5,
                height=301.0
            )
    
    def test_minimum_valid_height(self):
        """Test that height of exactly 30 cm is valid."""
        human = Human(
            name="Baby Doe",
            gender="male",
            date_of_birth=date.today(),
            weight=0.6,
            height=30.0
        )
        assert human.height == 30.0


class TestHumanAgeCalculation:
    """Tests for age calculation."""
    
    def test_age_calculation_birthday_passed(self):
        """Test age calculation when birthday has passed this year."""
        # Create a person born on January 1st (assuming test runs after that)
        human = Human(
            name="John Doe",
            gender="male",
            date_of_birth=date(1990, 1, 1),
            weight=75.5,
            height=175.0
        )
        expected_age = date.today().year - 1990
        assert human.get_age() == expected_age
    
    def test_age_calculation_for_newborn(self):
        """Test age calculation for someone born today."""
        human = Human(
            name="Baby Doe",
            gender="male",
            date_of_birth=date.today(),
            weight=3.5,
            height=50.0
        )
        assert human.get_age() == 0


class TestHumanBMI:
    """Tests for BMI calculation and categorization."""
    
    def test_bmi_calculation(self):
        """Test BMI calculation."""
        human = Human(
            name="John Doe",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=75.0,
            height=175.0
        )
        # BMI = 75 / (1.75^2) = 24.49
        assert human.bmi == 24.49
    
    def test_bmi_underweight_category(self):
        """Test BMI category for underweight."""
        human = Human(
            name="Thin Person",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=50.0,
            height=175.0
        )
        assert human.bmi_category == "Underweight"
    
    def test_bmi_normal_weight_category(self):
        """Test BMI category for normal weight."""
        human = Human(
            name="Normal Person",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=70.0,
            height=175.0
        )
        assert human.bmi_category == "Normal weight"
    
    def test_bmi_overweight_category(self):
        """Test BMI category for overweight."""
        human = Human(
            name="Heavy Person",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=85.0,
            height=175.0
        )
        assert human.bmi_category == "Overweight"
    
    def test_bmi_obese_category(self):
        """Test BMI category for obese."""
        human = Human(
            name="Obese Person",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=100.0,
            height=175.0
        )
        assert human.bmi_category == "Obese"


class TestHumanSerialization:
    """Tests for serialization."""
    
    def test_date_of_birth_serialization(self):
        """Test that date of birth is serialized in dd-mm-yyyy format."""
        human = Human(
            name="John Doe",
            gender="male",
            date_of_birth=date(1990, 5, 15),
            weight=75.5,
            height=175.0
        )
        json_data = human.model_dump(mode="json")
        assert json_data["date_of_birth"] == "15-05-1990"
    
    def test_full_serialization(self):
        """Test full model serialization to dict."""
        human = Human(
            name="Jane Smith",
            gender="female",
            date_of_birth=date(1985, 12, 25),
            weight=65.0,
            height=165.0
        )
        data = human.model_dump()
        assert data["name"] == "Jane Smith"
        assert data["gender"] == "female"
        assert data["weight"] == 65.0
        assert data["height"] == 165.0
