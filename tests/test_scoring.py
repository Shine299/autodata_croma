import pytest
from app.services.scoring import calculate_score
from app.schemas.vehicle import VehicleInspectionResponse, Insurance, Infractions, TaxDebt, CaptureOrder, SourceSummary
from app.schemas.seller import SellerScreeningResponse, Taxpayer, PersonalDebt
from app.schemas.common import Verdict, SourceStatus

def create_mock_vehicle(
    capture_order=False, 
    accident_count=0, 
    debt_total=0.0, 
    infraction_total=0.0, 
    active_soat=True,
    error_sources=0
) -> VehicleInspectionResponse:
    sources_summary = []
    for i in range(error_sources):
        sources_summary.append(SourceSummary(source=f"ErrorSource{i}", status=SourceStatus.ERROR, latency_ms=100))
    for i in range(6 - error_sources):
        sources_summary.append(SourceSummary(source=f"OkSource{i}", status=SourceStatus.OK, latency_ms=100))

    return VehicleInspectionResponse(
        inspection_id="insp_123",
        plate="ABC123",
        created_at="2026-08-14T00:00:00Z",
        insurance=Insurance(
            status=SourceStatus.OK,
            has_active_soat=active_soat,
            accident_count=accident_count
        ),
        infractions=Infractions(
            status=SourceStatus.OK,
            has_infractions=infraction_total > 0,
            total=infraction_total
        ),
        tax_debt=TaxDebt(
            status=SourceStatus.OK,
            has_debt=debt_total > 0,
            total=debt_total
        ),
        capture_order=CaptureOrder(
            status=SourceStatus.OK,
            has_capture_order=capture_order
        ),
        sources_summary=sources_summary
    )

def create_mock_seller(is_dealer=False, error_sources=0) -> SellerScreeningResponse:
    sources_summary = []
    for i in range(error_sources):
        sources_summary.append(SourceSummary(source=f"ErrorSourceS{i}", status=SourceStatus.ERROR, latency_ms=100))
    for i in range(2 - error_sources):
        sources_summary.append(SourceSummary(source=f"OkSourceS{i}", status=SourceStatus.OK, latency_ms=100))

    return SellerScreeningResponse(
        screening_id="scr_123",
        document_type="DNI",
        document_masked="****1234",
        created_at="2026-08-14T00:00:00Z",
        taxpayer=Taxpayer(
            status=SourceStatus.OK,
            is_vehicle_trader=is_dealer
        ),
        personal_debt=PersonalDebt(status=SourceStatus.OK),
        sources_summary=sources_summary
    )

def test_scoring_clean_vehicle_go():
    vehicle = create_mock_vehicle()
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.GO
    assert result.risk_score == 0
    assert len(result.flags) == 0

def test_scoring_capture_order_stop():
    vehicle = create_mock_vehicle(capture_order=True)
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.STOP
    assert result.risk_score == 100
    assert any(f.code == "CAPTURE_ORDER" for f in result.flags)

def test_scoring_high_accidents_caution():
    vehicle = create_mock_vehicle(accident_count=2)
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.CAUTION
    assert result.risk_score == 30
    assert any(f.code == "HIGH_ACCIDENTS" for f in result.flags)

def test_scoring_high_debt_caution():
    vehicle = create_mock_vehicle(debt_total=600, infraction_total=450) # Total 1050
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.CAUTION
    assert result.risk_score == 20
    assert any(f.code == "HIGH_DEBT" for f in result.flags)

def test_scoring_soat_expired_caution():
    vehicle = create_mock_vehicle(active_soat=False)
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.CAUTION
    assert result.risk_score == 20
    assert any(f.code == "SOAT_EXPIRED" for f in result.flags)

def test_scoring_seller_is_dealer_caution():
    vehicle = create_mock_vehicle()
    seller = create_mock_seller(is_dealer=True)
    result = calculate_score(vehicle, seller, claimed_role="PARTICULAR")
    assert result.verdict == Verdict.CAUTION
    assert result.risk_score == 30
    assert any(f.code == "SELLER_IS_DEALER" for f in result.flags)

def test_scoring_multiple_errors_caution():
    # Todo limpio, pero 2 fuentes fallaron
    vehicle = create_mock_vehicle(error_sources=2)
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.CAUTION
    assert result.risk_score == 0 # El risk score no aumenta, pero el veredicto es CAUTION
    assert any(f.code == "SOURCES_UNAVAILABLE" for f in result.flags)

def test_scoring_multiple_infractions_cap_risk_score():
    # Vehiculo con todo malo
    vehicle = create_mock_vehicle(
        capture_order=True,
        accident_count=3,
        debt_total=2000,
        active_soat=False
    )
    result = calculate_score(vehicle)
    assert result.verdict == Verdict.STOP
    assert result.risk_score == 100 # capped at 100
    assert len(result.flags) == 4
