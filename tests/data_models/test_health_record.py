"""Tests for health record data models."""

import pytest
from datetime import date, time
from pydantic import ValidationError

from nira_backend.data_models.health_record import (
    BloodGlucoseRecord,
    BloodPressureRecord,
    HeartRateRecord,
    HealthRecord,
    SleepRecord,
)


class TestBloodPressureRecord:
    def test_create_valid(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=120, diastolic_mmhg=80)
        assert bp.systolic_mmhg == 120
        assert bp.diastolic_mmhg == 80

    def test_with_pulse(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=120, diastolic_mmhg=80, pulse_bpm=72)
        assert bp.pulse_bpm == 72

    def test_diastolic_ge_systolic_raises(self) -> None:
        with pytest.raises(ValueError, match="Diastolic"):
            BloodPressureRecord(systolic_mmhg=80, diastolic_mmhg=80)

    def test_diastolic_gt_systolic_raises(self) -> None:
        with pytest.raises(ValueError, match="Diastolic"):
            BloodPressureRecord(systolic_mmhg=80, diastolic_mmhg=90)

    def test_systolic_too_low_raises(self) -> None:
        with pytest.raises(ValidationError):
            BloodPressureRecord(systolic_mmhg=49, diastolic_mmhg=30)

    def test_category_normal(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=115, diastolic_mmhg=75)
        assert bp.category == "Normal"

    def test_category_elevated(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=125, diastolic_mmhg=79)
        assert bp.category == "Elevated"

    def test_category_stage1(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=135, diastolic_mmhg=85)
        assert bp.category == "High Blood Pressure Stage 1"

    def test_category_stage2(self) -> None:
        bp = BloodPressureRecord(systolic_mmhg=145, diastolic_mmhg=95)
        assert bp.category == "High Blood Pressure Stage 2"


class TestBloodGlucoseRecord:
    def test_create_valid(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=5.5)
        assert g.glucose_mmol_l == 5.5
        assert g.measurement_context == "random"

    def test_fasting_context(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=5.5, measurement_context="fasting")
        assert g.measurement_context == "fasting"

    def test_glucose_mg_dl_conversion(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=5.5)
        assert abs(g.glucose_mg_dl - 99.1) < 0.2

    def test_category_fasting_normal(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=5.0, measurement_context="fasting")
        assert g.category == "Normal"

    def test_category_fasting_low(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=3.5, measurement_context="fasting")
        assert g.category == "Low"

    def test_category_fasting_prediabetic(self) -> None:
        g = BloodGlucoseRecord(glucose_mmol_l=6.5, measurement_context="fasting")
        assert g.category == "Pre-diabetic"

    def test_negative_glucose_raises(self) -> None:
        with pytest.raises(ValidationError):
            BloodGlucoseRecord(glucose_mmol_l=-1.0)

    def test_invalid_context_raises(self) -> None:
        with pytest.raises(ValidationError):
            BloodGlucoseRecord(glucose_mmol_l=5.0, measurement_context="before_bed")  # type: ignore[arg-type]


class TestHeartRateRecord:
    def test_create_valid(self) -> None:
        hr = HeartRateRecord(bpm=65)
        assert hr.bpm == 65
        assert hr.measurement_context == "resting"

    def test_category_normal(self) -> None:
        hr = HeartRateRecord(bpm=70)
        assert hr.category == "Normal"

    def test_category_low(self) -> None:
        hr = HeartRateRecord(bpm=55)
        assert hr.category == "Bradycardic (low)"

    def test_category_high(self) -> None:
        hr = HeartRateRecord(bpm=110)
        assert hr.category == "Tachycardic (high)"

    def test_category_not_resting(self) -> None:
        hr = HeartRateRecord(bpm=110, measurement_context="active")
        assert hr.category == "N/A (non-resting)"

    def test_bpm_too_low_raises(self) -> None:
        with pytest.raises(ValidationError):
            HeartRateRecord(bpm=10)


class TestSleepRecord:
    def test_create_valid(self) -> None:
        s = SleepRecord(duration_hours=7.5, quality=4)
        assert s.duration_hours == 7.5
        assert s.quality == 4

    def test_quality_label(self) -> None:
        assert SleepRecord(duration_hours=8, quality=5).quality_label == "Excellent"
        assert SleepRecord(duration_hours=4, quality=1).quality_label == "Very Poor"

    def test_quality_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            SleepRecord(duration_hours=8, quality=6)

    def test_duration_too_high_raises(self) -> None:
        with pytest.raises(ValidationError):
            SleepRecord(duration_hours=25, quality=3)

    def test_optional_times(self) -> None:
        s = SleepRecord(
            duration_hours=7,
            quality=3,
            bedtime=time(23, 0),
            wake_time=time(6, 0),
        )
        assert s.bedtime == time(23, 0)
        assert s.wake_time == time(6, 0)


class TestHealthRecord:
    def test_create_blood_pressure(self) -> None:
        record = HealthRecord(
            human_name="John Doe",
            record_date=date(2024, 1, 15),
            record_type="blood_pressure",
            measurement=BloodPressureRecord(systolic_mmhg=118, diastolic_mmhg=76),
        )
        assert record.human_name == "John Doe"
        assert record.record_type == "blood_pressure"

    def test_create_blood_glucose(self) -> None:
        record = HealthRecord(
            human_name="Jane",
            record_date=date(2024, 3, 1),
            record_type="blood_glucose",
            measurement=BloodGlucoseRecord(glucose_mmol_l=5.2, measurement_context="fasting"),
        )
        assert record.record_type == "blood_glucose"

    def test_future_date_raises(self) -> None:
        from datetime import timedelta
        with pytest.raises(ValidationError, match="future"):
            HealthRecord(
                human_name="John",
                record_date=date.today() + timedelta(days=1),
                record_type="heart_rate",
                measurement=HeartRateRecord(bpm=70),
            )

    def test_empty_human_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            HealthRecord(
                human_name="",
                record_date=date(2024, 1, 1),
                record_type="heart_rate",
                measurement=HeartRateRecord(bpm=70),
            )

    def test_invalid_record_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            HealthRecord(
                human_name="John",
                record_date=date(2024, 1, 1),
                record_type="temperature",  # type: ignore[arg-type]
                measurement=HeartRateRecord(bpm=70),
            )

    def test_optional_notes(self) -> None:
        record = HealthRecord(
            human_name="Alice",
            record_date=date(2024, 2, 1),
            record_type="sleep",
            measurement=SleepRecord(duration_hours=8, quality=4),
            notes="Slept well",
        )
        assert record.notes == "Slept well"

    def test_name_stripped(self) -> None:
        record = HealthRecord(
            human_name="  Bob  ",
            record_date=date(2024, 1, 1),
            record_type="heart_rate",
            measurement=HeartRateRecord(bpm=65),
        )
        assert record.human_name == "Bob"
