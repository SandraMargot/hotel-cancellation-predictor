"""
Quick test script to fetch hotel offers via AmadeusClient.
This is for manual runs (not part of ETL yet).
"""

import os
from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta

from hotels.amadeus_client import AmadeusClient

if __name__ == "__main__":
    # Init client (credentials come from .env)
    client = AmadeusClient()

    # Step 1: Pick a city
    city_code = os.getenv("CITY_CODE", "NCE")  # Nice as default
    hotels = client.get_hotels_by_geocode(43.7102, 7.2620, radius_km=7, max_hotels=20)
    print(f"Found {len(hotels)} hotels in {city_code}")

    # Step 2: Choose first ~10 hotel IDs
    hotel_ids = [h["hotelId"] for h in hotels[:10]]

    # Step 3: Fetch offers for tomorrow, 1 night
    check_in = (date.today() + timedelta(days=1)).isoformat()
    offers = client.get_hotel_offers(
        hotel_ids=hotel_ids,
        check_in=check_in,
        nights=1,
        adults=1,
        rooms=1,
        currency="EUR",
    )

    # Step 4: Print summary
    total = sum(len(batch["response"].get("data", [])) for batch in offers["batches"])
    print(f"Total offers fetched: {total}")
    print("Example hotel IDs:", hotel_ids[:3])

from pathlib import Path
import json
from datetime import datetime

Path("data/raw").mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = Path(f"data/raw/offers_{stamp}.json")
with out_path.open("w", encoding="utf-8") as f:
    json.dump(offers, f, ensure_ascii=False, indent=2)
print(f"Saved raw offers to {out_path}")

from hotels.flatten import flatten_offers
import pandas as pd

flat = flatten_offers(offers)
df = pd.DataFrame(flat)
print(df.head())

# Save to processed folder
from pathlib import Path

Path("data/processed").mkdir(parents=True, exist_ok=True)
flat_path = Path(f"data/processed/offers_flat_{stamp}.csv")
df.to_csv(flat_path, index=False)
print(f"Saved flattened offers to {flat_path}")

# Also save/overwrite a "latest" version for easy access
latest_path = Path("data/processed/offers_latest.csv")
df.to_csv(latest_path, index=False)
print(f"Saved latest flattened offers to {latest_path}")
