"""
Flatten Amadeus Hotel Offers JSON into a tabular structure.
"""

from typing import Dict, List, Any


def flatten_offers(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract core fields (hotelId, check-in/out, nights, total price, refundable flag).
    Returns a list of flat dicts.
    """
    rows: List[Dict[str, Any]] = []

    for batch in raw.get("batches", []):
        data = batch.get("response", {}).get("data", [])
        for entry in data:
            hotel = entry.get("hotel", {})
            hotel_id = hotel.get("hotelId")

            for offer in entry.get("offers", []):
                check_in = offer.get("checkInDate")
                check_out = offer.get("checkOutDate")
                price_total = offer.get("price", {}).get("total")
                currency = offer.get("price", {}).get("currency")

                # nights: difference between check-in and check-out (API doesn't give directly)
                nights = None
                if check_in and check_out:
                    from datetime import date
                    try:
                        ci = date.fromisoformat(check_in)
                        co = date.fromisoformat(check_out)
                        nights = (co - ci).days
                    except Exception:
                        pass

                refundable_flag = None
                policies = offer.get("policies", {})
                if "refundable" in policies:
                    refundable_flag = (
                        policies["refundable"].get("cancellationRefund") != "NON_REFUNDABLE"
                    )

                rows.append(
                    {
                        "hotelId": hotel_id,
                        "checkInDate": check_in,
                        "nights": nights,
                        "totalPrice": price_total,
                        "currency": currency,
                        "refundable": refundable_flag,
                    }
                )

    return rows
