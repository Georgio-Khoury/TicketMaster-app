from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.Models.event import Event, Base
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

scheduler = BackgroundScheduler()

# Cache to store already processed event IDs (expires after 1 hour)
event_cache = {}
CACHE_EXPIRY = timedelta(hours=1)

def is_event_in_cache(event_id: str) -> bool:
    """Check if event is in cache and not expired"""
    cache_entry = event_cache.get(event_id)
    if cache_entry:
        if datetime.now() - cache_entry['timestamp'] < CACHE_EXPIRY:
            return True
        del event_cache[event_id]  # Remove expired entry
    return False

def fetch_ticketmaster_data():
    db: Session = SessionLocal()
    keywords = ["music", "sports", "arts", "theatre", "comedy", "festivals", "concerts", "exhibitions"]
    try:
        # First check for existing events in the last 24 hours
        existing_ids = {event[0] for event in db.query(Event.id).filter(
            Event.created_at >= datetime.now() - timedelta(hours=24)
        ).all()}
        
        response = httpx.get(
            "https://app.ticketmaster.com/discovery/v2/events.json",
            params={
                "apikey": os.getenv("TICKETMASTER_KEY"),
                "keyword": keywords,
                "size": 60
            },
            timeout=30
        )
       
        
        new_events = 0
        for keyword in keywords:
            response = httpx.get(
                "https://app.ticketmaster.com/discovery/v2/events.json",
                params={
                    "apikey": os.getenv("TICKETMASTER_KEY"),
                    "keyword": keyword,
                    "size": 60
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            events_data = data.get("_embedded", {}).get("events", [])
        for event_data in events_data:
            event_id = event_data.get('id')
            if not event_id:
                continue
                
            # Skip if already in database or cache
            if event_id in existing_ids or is_event_in_cache(event_id):
                continue
                
            try:
                # Extract venue information
                venue = event_data.get('_embedded', {}).get('venues', [{}])[0]
                
                # Parse date safely
                start_date = None
                if 'dates' in event_data and 'start' in event_data['dates']:
                    date_str = event_data['dates']['start'].get('dateTime')
                    if date_str:
                        try:
                            start_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                        except ValueError:
                            pass
                
                # Create event object
                event = Event(
                    id=event_id,
                    name=event_data['name'],
                    description=event_data.get('description', ''),
                    start_date=start_date,
                    venue_name=venue.get('name', ''),
                    city=venue.get('city', {}).get('name', ''),
                    country=venue.get('country', {}).get('name', ''),
                    url=event_data.get('url', '')
                )
                
                db.add(event)
                db.commit()
                
                # Add to cache
                event_cache[event_id] = {'timestamp': datetime.now()}
                new_events += 1
                print(f"Added event: {event_data['name']}")
            
            except IntegrityError:
                db.rollback()
                existing_ids.add(event_id)  # Add to existing IDs
                event_cache[event_id] = {'timestamp': datetime.now()}
                print(f"Event {event_id} already exists, skipping")
            
            except KeyError as e:
                db.rollback()
                print(f"Missing required field {str(e)} in event data")
        
        print(f"Added {new_events} new events")
        
    except Exception as e:
        db.rollback()
        print("Error fetching Ticketmaster data:", str(e))
    finally:
        db.close()

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initial fetch
    fetch_ticketmaster_data()
    
    # Schedule regular updates (every 6 hours)
    scheduler.add_job(fetch_ticketmaster_data, "interval", minutes=20)
    scheduler.start()
    yield
    scheduler.shutdown()