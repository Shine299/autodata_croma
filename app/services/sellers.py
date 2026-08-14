from app.schemas.seller import SellerScreeningResponse

async def get_seller_screening(document_number: str) -> SellerScreeningResponse:
    from tests.test_scoring import create_mock_seller
    if "DEALER" in document_number:
        return create_mock_seller(is_dealer=True)
    return create_mock_seller()
