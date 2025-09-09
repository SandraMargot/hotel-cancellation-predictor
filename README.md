# Hotel Cancellation Predictor

This project predicts which hotel bookings are likely to be canceled, using **Amadeus API offers** combined with **historical booking data**.  
It implements an **MLOps pipeline** with CI/CD, monitoring, and a Streamlit app for insights.

---

## Project Structure
hotels
├── .env                # Local secrets (ignored in Git)
├── .env.example        # Example environment variables (safe to share)
├── .gitignore          # Ignore rules for Git
├── README.md           # Project documentation
├── app/                # Streamlit application
│ └── app.py            # Entry point for the dashboard
├── configs/            # YAML settings and configs
│ └── settings.yaml     # Pipeline configuration
├── data/               # Raw and processed datasets
│ ├── processed/
│ │ └── .gitkeep        # Keeps folder in Git (data ignored)
│ └── raw/
│ └── .gitkeep          # Keeps folder in Git (data ignored)
├── logs/               # Logs output
│ └── .gitkeep          # Keeps folder in Git (logs ignored)
├── requirements.txt    # Python dependencies
├── scripts/            # Helper scripts
│ ├── fetch_offers.py   # Pull hotel offers from Amadeus
│ ├── make_features.py  # Feature engineering
│ └── quick_run.py      # Quick local run
├── src/                # Source code
│ └── hotels/           # Core Python package
│ ├── init.py
│ ├── amadeus_client.py # API client logic
│ ├── config.py         # Load env + YAML settings
│ ├── db.py             # Database connection helpers
│ ├── flatten.py        # Normalize nested API JSON
│ └── storage.py        # Save/load raw and processed data
└── tests/              # Unit and integration tests
└── test_smoke.py       # Basic PyTest check


---

## Setup

1. Create environment:
        ```bash
        conda create -n amadeus python=3.11 -y
        conda activate amadeus
2. Install dependencies:
        pip install -r requirements.txt
3. Copy .env.example → .env and fill in your credentials:
        cp .env.example .env