import argparse, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, Base, engine
from app.db.models import LeadModel, JobModel
from app.services.maps_client import search_businesses


def run(keyword: str, location: str, max_results: int):
    Base.metadata.create_all(bind=engine)  # creates leads + jobs tables if missing
    db = SessionLocal()

    job = JobModel(keywords=keyword, location=location, status="running")
    db.add(job)
    db.commit()

    found = search_businesses(keyword, location, max_results=max_results)
    inserted, skipped = 0, 0

    for item in found:
        exists = db.query(LeadModel).filter_by(
            business_name=item["business_name"], website_url=item["website_url"]
        ).first()
        if exists:
            skipped += 1
            continue
        db.add(LeadModel(**item, status="new"))
        inserted += 1

    job.leads_found = inserted
    job.status = "completed"
    db.commit()
    db.close()
    print(f"Done. Inserted {inserted} new leads, skipped {skipped} duplicates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword")
    parser.add_argument("location")
    parser.add_argument("--max", type=int, default=20, dest="max_results")
    args = parser.parse_args()
    run(args.keyword, args.location, args.max_results)