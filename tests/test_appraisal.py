import pytest
from app.services.appraisal import calculate_appraisal
from tests.test_scoring import create_mock_vehicle

def test_appraisal_clean():
    vehicle = create_mock_vehicle()
    res = calculate_appraisal("verif_1", vehicle, 30000.0)
    assert res.fair_price == 30000.0
    assert res.total_deduction == 0.0
    assert res.recommendation == "PRECIO_JUSTO"
    assert len(res.deductions) == 0

def test_appraisal_capture_order():
    vehicle = create_mock_vehicle(capture_order=True)
    res = calculate_appraisal("verif_1", vehicle, 30000.0)
    assert res.fair_price == 0.0
    assert res.recommendation == "NO_COMPRAR"
    assert "no recomiendo" in res.negotiation_script.lower()

def test_appraisal_debts_and_soat():
    # Deuda 1000 + SOAT vencido (350) = 1350
    vehicle = create_mock_vehicle(debt_total=1000.0, active_soat=False)
    res = calculate_appraisal("verif_1", vehicle, 30000.0)
    assert res.fair_price == 28650.0
    assert res.total_deduction == 1350.0
    assert len(res.deductions) == 2
    assert res.recommendation == "NEGOCIAR"

def test_appraisal_accidents():
    # 2 accidentes = 8%. 8% de 30,000 = 2400
    vehicle = create_mock_vehicle(accident_count=2)
    res = calculate_appraisal("verif_1", vehicle, 30000.0)
    assert res.fair_price == 27600.0
    assert res.total_deduction == 2400.0
    
def test_appraisal_max_accidents():
    # 10 accidentes = 40%, pero el max es 20%. 20% de 30,000 = 6000
    vehicle = create_mock_vehicle(accident_count=10)
    res = calculate_appraisal("verif_1", vehicle, 30000.0)
    assert res.fair_price == 24000.0
    assert res.total_deduction == 6000.0
