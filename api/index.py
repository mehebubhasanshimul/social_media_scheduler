import os
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import requests

# Supabase database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:shimul965960@db.qfvrgfdoqvlexbrsqqfd.supabase.co:5432/postgres?sslmode=require")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class DBPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)
    content = Column(String)
    schedule_time = Column(String)  # Format: YYYY-MM-DDTHH:MM
    is_published = Column(Boolean, default=False)

# Create tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PostSchema(BaseModel):
    platform: str
    content: str
    schedule_time: str

@app.get("/api/health")
def health_check():
    return {"status": "running", "database": "connected"}

@app.post("/api/schedule")
def schedule_post(post: PostSchema, db: Session = Depends(get_db)):
    db_post = DBPost(
        platform=post.platform,
        content=post.content,
        schedule_time=post.schedule_time,
        is_published=False
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return {
        "status": "success",
        "message": f"Post scheduled successfully for {post.platform} and saved to Supabase!",
        "post_id": db_post.id
    }

def send_to_social_media(platform, content):
    # This is a placeholder function where real API requests go
    # Example for Facebook:
    # page_id = os.getenv("FACEBOOK_PAGE_ID")
    # token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    # r = requests.post(f"https://graph.facebook.com/{page_id}/feed", data={'message': content, 'access_token': token})
    # return r.status_code == 200
    print(f"Simulating posting to {platform}: {content}")
    return True

@app.get("/api/cron-worker")
def cron_worker(db: Session = Depends(get_db), x_vercel_cron: str = Header(None)):
    current_time_str = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    pending_posts = db.query(DBPost).filter(
        DBPost.is_published == False,
        DBPost.schedule_time <= current_time_str
    ).all()
    
    published_count = 0
    for post in pending_posts:
        success = send_to_social_media(post.platform, post.content)
        if success:
            post.is_published = True
            published_count += 1
            
    db.commit()
    return {
        "status": "done",
        "time_checked": current_time_str,
        "posts_published": published_count
    }

@app.get("/api/analytics")
def get_analytics():
    return {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "facebook_clicks": [120, 150, 180, 220, 260, 310],
        "linkedin_clicks": [50, 85, 120, 140, 190, 240],
        "twitter_clicks": [90, 110, 130, 125, 170, 210]
    }
