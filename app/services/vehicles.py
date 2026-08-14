from app.schemas.vehicle import VehicleInspectionResponse

async def get_vehicle_inspection(plate: str) -> VehicleInspectionResponse:
    from tests.test_scoring import create_mock_vehicle
    if "STOP" in plate:
        return create_mock_vehicle(capture_order=True)
    if "CAUTION" in plate:
        return create_mock_vehicle(accident_count=2)
    return create_mock_vehicle()
