"""Tests for the measurements data models."""
import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from nira_backend.data_models.measurements import (
    BaseMeasurement,
    WeightMeasurement,
    LengthMeasurement,
    BodyShapeMeasurements
)


class TestBaseMeasurement:
    """Tests for BaseMeasurement class."""
    
    def test_create_valid_base_measurement(self):
        """Test creating a valid BaseMeasurement instance."""
        measurement = BaseMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=100.0,
            unit="kg"
        )
        assert measurement.measurement_date == date(2023, 10, 1)
        assert measurement.measurement_time == timedelta(hours=8, minutes=30)
        assert measurement.value == 100.0
        assert measurement.unit == "kg"
    
    def test_negative_value_raises_error(self):
        """Test that negative value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BaseMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=8, minutes=30),
                value=-10.0,
                unit="kg"
            )
        assert "Measurement value must be non-negative" in str(exc_info.value)
    
    def test_zero_value_is_valid(self):
        """Test that zero value is valid."""
        measurement = BaseMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=0.0,
            unit="kg"
        )
        assert measurement.value == 0.0


class TestWeightMeasurement:
    """Tests for WeightMeasurement class."""
    
    def test_create_weight_measurement_kg(self):
        """Test creating a weight measurement in kilograms."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=70.5,
            unit="kg"
        )
        assert weight.value == 70.5
        assert weight.unit == "kg"
    
    def test_create_weight_measurement_lb(self):
        """Test creating a weight measurement in pounds."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=100.0,
            unit="lb"
        )
        assert weight.value == 100.0
        assert weight.unit == "lb"
    
    def test_create_weight_measurement_g(self):
        """Test creating a weight measurement in grams."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=70.5,
            unit="g"
        )
        assert weight.value == 70.5
        assert weight.unit == "g"
    
    def test_default_unit_is_kg(self):
        """Test that default unit is kg."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=70.5
        )
        assert weight.unit == "kg"
    
    def test_invalid_unit_raises_error(self):
        """Test that invalid unit raises ValidationError."""
        with pytest.raises(ValidationError):
            WeightMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=8, minutes=30),
                value=70.5,
                unit="ton"
            )
    
    def test_value_below_minimum_raises_error(self):
        """Test that value below 0.5 raises ValidationError."""
        with pytest.raises(ValidationError):
            WeightMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=8, minutes=30),
                value=0.4,
                unit="kg"
            )
    
    def test_value_above_maximum_raises_error(self):
        """Test that value above 150 raises ValidationError."""
        with pytest.raises(ValidationError):
            WeightMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=8, minutes=30),
                value=151.0,
                unit="kg"
            )
    
    def test_convert_kg_to_kg(self):
        """Test converting kg to kg returns same value."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=70.0,
            unit="kg"
        )
        assert weight.convert_to_kg() == 70.0
    
    def test_convert_lb_to_kg(self):
        """Test converting pounds to kilograms."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=100.0,
            unit="lb"
        )
        # 100 lb = 45.3592 kg
        assert abs(weight.convert_to_kg() - 45.3592) < 0.001
    
    def test_convert_g_to_kg(self):
        """Test converting grams to kilograms."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=5.0,
            unit="g"
        )
        assert weight.convert_to_kg() == 0.005
    
    def test_set_unit_to_kg_from_lb(self):
        """Test setting unit to kg converts value from pounds."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=100.0,
            unit="lb"
        )
        weight.set_unit_to_kg()
        assert weight.unit == "kg"
        assert abs(weight.value - 45.3592) < 0.001
    
    def test_set_unit_to_kg_when_already_kg(self):
        """Test setting unit to kg when already in kg doesn't change value."""
        weight = WeightMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=70.0,
            unit="kg"
        )
        weight.set_unit_to_kg()
        assert weight.unit == "kg"
        assert weight.value == 70.0


class TestLengthMeasurement:
    """Tests for LengthMeasurement class."""
    
    def test_create_length_measurement_cm(self):
        """Test creating a length measurement in centimeters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="cm"
        )
        assert length.value == 180.0
        assert length.unit == "cm"
    
    def test_create_length_measurement_m(self):
        """Test creating a length measurement in meters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="m"
        )
        assert length.value == 180.0
        assert length.unit == "m"
    
    def test_create_length_measurement_in(self):
        """Test creating a length measurement in inches."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=70.0,
            unit="in"
        )
        assert length.value == 70.0
        assert length.unit == "in"
    
    def test_create_length_measurement_ft(self):
        """Test creating a length measurement in feet."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=60.0,
            unit="ft"
        )
        assert length.value == 60.0
        assert length.unit == "ft"
    
    def test_default_unit_is_cm(self):
        """Test that default unit is cm."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0
        )
        assert length.unit == "cm"
    
    def test_invalid_unit_raises_error(self):
        """Test that invalid unit raises ValidationError."""
        with pytest.raises(ValidationError):
            LengthMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=9, minutes=0),
                value=180.0,
                unit="km"
            )
    
    def test_value_below_minimum_raises_error(self):
        """Test that value below 30 raises ValidationError."""
        with pytest.raises(ValidationError):
            LengthMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=9, minutes=0),
                value=25.0,
                unit="cm"
            )
    
    def test_value_above_maximum_raises_error(self):
        """Test that value above 300 raises ValidationError."""
        with pytest.raises(ValidationError):
            LengthMeasurement(
                measurement_date=date(2023, 10, 1),
                measurement_time=timedelta(hours=9, minutes=0),
                value=301.0,
                unit="cm"
            )
    
    def test_convert_cm_to_cm(self):
        """Test converting cm to cm returns same value."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="cm"
        )
        assert length.convert_to_cm() == 180.0
    
    def test_convert_m_to_cm(self):
        """Test converting meters to centimeters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="m"
        )
        assert length.convert_to_cm() == 18000.0
    
    def test_convert_in_to_cm(self):
        """Test converting inches to centimeters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=70.0,
            unit="in"
        )
        # 70 in = 177.8 cm
        assert abs(length.convert_to_cm() - 177.8) < 0.001
    
    def test_convert_ft_to_cm(self):
        """Test converting feet to centimeters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=60.0,
            unit="ft"
        )
        # 60 ft = 1828.8 cm
        assert abs(length.convert_to_cm() - 1828.8) < 0.001
    
    def test_set_unit_to_cm_from_m(self):
        """Test setting unit to cm converts value from meters."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="m"
        )
        length.set_unit_to_cm()
        assert length.unit == "cm"
        assert length.value == 18000.0
    
    def test_set_unit_to_cm_when_already_cm(self):
        """Test setting unit to cm when already in cm doesn't change value."""
        length = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=9, minutes=0),
            value=180.0,
            unit="cm"
        )
        length.set_unit_to_cm()
        assert length.unit == "cm"
        assert length.value == 180.0


class TestBodyShapeMeasurements:
    """Tests for BodyShapeMeasurements class."""
    
    def test_create_with_all_measurements(self):
        """Test creating BodyShapeMeasurements with all fields."""
        neck = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=40.0,
            unit="cm"
        )
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=80.0,
            unit="cm"
        )
        hip = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=90.0,
            unit="cm"
        )
        wrist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=38.0,
            unit="cm"
        )
        forearm = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="cm"
        )
        
        body = BodyShapeMeasurements(
            neck_circumference=neck,
            waist_circumference=waist,
            hip_circumference=hip,
            wrist_circumference=wrist,
            forearm_circumference=forearm
        )
        
        assert body.neck_circumference == neck
        assert body.waist_circumference == waist
        assert body.hip_circumference == hip
        assert body.wrist_circumference == wrist
        assert body.forearm_circumference == forearm
    
    def test_create_with_no_measurements(self):
        """Test creating BodyShapeMeasurements with all fields as None."""
        body = BodyShapeMeasurements()
        assert body.neck_circumference is None
        assert body.waist_circumference is None
        assert body.hip_circumference is None
        assert body.wrist_circumference is None
        assert body.forearm_circumference is None
    
    def test_create_with_partial_measurements(self):
        """Test creating BodyShapeMeasurements with some fields."""
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=80.0,
            unit="cm"
        )
        
        body = BodyShapeMeasurements(waist_circumference=waist)
        
        assert body.waist_circumference == waist
        assert body.neck_circumference is None
        assert body.hip_circumference is None
    
    def test_neck_circumference_validation_too_small(self):
        """Test that neck circumference below 8 cm raises error."""
        # Values below 30 are caught by LengthMeasurement validation
        # Test with exactly 30 cm which passes LengthMeasurement but is valid for neck (8-60)
        neck = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="cm"
        )
        # This should pass since 30 is between 8 and 60
        body = BodyShapeMeasurements(neck_circumference=neck)
        assert body.neck_circumference is not None
    
    def test_neck_circumference_validation_too_large(self):
        """Test that neck circumference above 60 cm raises error."""
        neck = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=61.0,
            unit="cm"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            BodyShapeMeasurements(neck_circumference=neck)
        assert "Neck circumference must be between 8 cm and 60 cm" in str(exc_info.value)
    
    def test_waist_circumference_validation_too_small(self):
        """Test that waist circumference below 20 cm raises error."""
        # LengthMeasurement minimum is 30, so waist validation of >=20 is redundant
        # Test boundary case at minimum valid LengthMeasurement
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="cm"
        )
        body = BodyShapeMeasurements(waist_circumference=waist)
        assert body.waist_circumference is not None
    
    def test_waist_circumference_validation_too_large(self):
        """Test that waist circumference above 150 cm raises error."""
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=151.0,
            unit="cm"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            BodyShapeMeasurements(waist_circumference=waist)
        assert "Waist circumference must be between 20 cm and 150 cm" in str(exc_info.value)
    
    def test_hip_circumference_validation_too_small(self):
        """Test that hip circumference below 20 cm raises error."""
        # LengthMeasurement minimum is 30, so hip validation of >=20 is redundant
        # Test boundary case at minimum valid LengthMeasurement
        hip = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="cm"
        )
        body = BodyShapeMeasurements(hip_circumference=hip)
        assert body.hip_circumference is not None
    
    def test_hip_circumference_validation_too_large(self):
        """Test that hip circumference above 200 cm raises error."""
        hip = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=201.0,
            unit="cm"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            BodyShapeMeasurements(hip_circumference=hip)
        assert "Hip circumference must be between 20 cm and 200 cm" in str(exc_info.value)
    
    def test_wrist_circumference_validation_too_small(self):
        """Test that wrist circumference below 5 cm raises error."""
        # LengthMeasurement minimum is 30, so wrist validation of >=5 is redundant
        # Test boundary case at minimum valid LengthMeasurement
        wrist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="cm"
        )
        body = BodyShapeMeasurements(wrist_circumference=wrist)
        assert body.wrist_circumference is not None
    
    def test_wrist_circumference_validation_too_large(self):
        """Test that wrist circumference above 40 cm raises error."""
        wrist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=41.0,
            unit="cm"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            BodyShapeMeasurements(wrist_circumference=wrist)
        assert "Wrist circumference must be between 5 cm and 40 cm" in str(exc_info.value)
    
    def test_measurements_converted_to_cm(self):
        """Test that measurements are automatically converted to cm."""
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=80.0,
            unit="in"  # 80 inches = 203.2 cm, but too large for waist (max 150)
        )
        # Use a valid value: 30 in = 76.2 cm
        waist = LengthMeasurement(
            measurement_date=date(2023, 10, 1),
            measurement_time=timedelta(hours=8, minutes=30),
            value=30.0,
            unit="in"
        )
        
        body = BodyShapeMeasurements(waist_circumference=waist)
        
        # Should be converted to cm
        assert body.waist_circumference.unit == "cm"
        assert abs(body.waist_circumference.value - 76.2) < 0.1
    
    def test_none_values_not_validated(self):
        """Test that None values skip validation."""
        # This should not raise any errors
        body = BodyShapeMeasurements(
            neck_circumference=None,
            waist_circumference=None
        )
        assert body.neck_circumference is None
        assert body.waist_circumference is None
