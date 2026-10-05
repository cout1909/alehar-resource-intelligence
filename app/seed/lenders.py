"""Demonstration records, not scraped or attributed to Alehar.

Official URL provenance is recorded in docs/seed-sources.md.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Lender, SourceType

DEMO_DESCRIPTION = "Seed record for verification demonstration. Not Alehar data."
SEED_LENDERS = [
    ("HDFC Bank", "https://www.hdfc.bank.in/"),
    ("ICICI Bank", "https://www.icicibank.com/"),
    ("SIDBI", "https://www.sidbi.in/home-product"),
    ("UGRO Capital", "https://www.ugrocapital.com/"),
    ("FlexiLoans", "https://flexiloans.com/regulatory"),
    ("Stride Ventures", "https://strideventures.global/"),
    ("Alteria Capital", "https://alteriacapital.com/"),
    ("Trifecta Capital", "https://www.trifectacapital.in/"),
]


def seed_lenders(session: Session) -> int:
    if session.scalar(select(Lender.id).limit(1)) is not None:
        return 0
    for name, url in SEED_LENDERS:
        session.add(
            Lender(
                name=name,
                country="India",
                lender_type="Demo entry - classification not verified",
                description=DEMO_DESCRIPTION,
                website_url=url,
                alehar_url=None,
                verification_source_url=url,
                source_type=SourceType.OFFICIAL_WEBSITE,
                is_demo=True,
            )
        )
    session.commit()
    logging.getLogger(__name__).info("Seeded %s demo lenders", len(SEED_LENDERS))
    return len(SEED_LENDERS)
