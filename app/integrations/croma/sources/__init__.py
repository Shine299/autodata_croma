"""Sources adapters for Croma API responses to domain schemas."""

from app.integrations.croma.sources.apeseg import map_apeseg_soat, merge_insurance_sources
from app.integrations.croma.sources.callao import map_callao_infractions, merge_infractions
from app.integrations.croma.sources.sat_captures import map_sat_capture_order
from app.integrations.croma.sources.sat_debt import map_sat_tax_debt
from app.integrations.croma.sources.sat_seller import map_sat_seller_debt
from app.integrations.croma.sources.sbs import map_sbs_soat
from app.integrations.croma.sources.sutran import map_sutran_infractions
from app.integrations.croma.sources.sunat import map_sunat_taxpayer

__all__ = [
    "map_sbs_soat",
    "map_apeseg_soat",
    "merge_insurance_sources",
    "map_sutran_infractions",
    "map_callao_infractions",
    "merge_infractions",
    "map_sat_tax_debt",
    "map_sat_capture_order",
    "map_sunat_taxpayer",
    "map_sat_seller_debt",
]
