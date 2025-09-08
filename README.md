# Hotel Cancellation Predictor

This project predicts which hotel bookings are likely to be canceled, using **Amadeus API offers** combined with **historical booking data**.  
It implements an **MLOps pipeline** with CI/CD, monitoring, and a Streamlit app for insights.

---

## Project Structure
hotels/
├── configs/        # YAML settings and config files
├── data/           # Raw and processed datasets (ignored in Git)
├── scripts/        # Helper scripts (fetch, feature engineering, quick runs)
├── src/hotels/     # Core Python package
├── .env            # Local secrets (not in Git)
├── .env.example    # Example environment variables
├── .gitignore
├── requirements.txt
└── README.md


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