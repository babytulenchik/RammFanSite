from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Product
import random

SQLALCHEMY_DATABASE_URL = "sqlite:///./rammstein_shop.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    if db.query(Product).count() == 0:
        products = [
            Product(
                name="T-Shirt",
                category="clothing",
                description="Classic black t-shirt with the iconic Rammstein logo",
                price=30.00,
                image_url="/static/img/merch/rammtshirt.png",
            ),
            Product(
                name="Hoodie",
                category="clothing",
                description="Premium black hoodie with the iconic Rammstein logo",
                price=60.00,
                image_url="/static/img/merch/rammhudi.png",
            ),
            Product(
                name="Steel Bracelet",
                category="accessories",
                description="Heavy stainless steel bracelet with engraved logo",
                price=75.00,
                image_url="/static/img/merch/rammbracelet.png",
            ),
            Product(
                name='"Zeit" Limited Vinyl',
                category="music",
                description="Limited edition vinyl",
                price=30.00,
                image_url="/static/img/merch/rammzeit.png",
            ),
            Product(
                name="Patch",
                category="accessories",
                description="High-quality embroidered patch with classic logo",
                price=4.50,
                image_url="/static/img/merch/rammpatch.png",
            ),
            Product(
                name="Collector's Box Set",
                category="special",
                description="Exclusive box set with vinyl and artbook",
                price=150.00,
                image_url="/static/img/merch/rammbox.png",
            ),
            Product(
                name="Army Cap",
                category="clothing",
                description="Black army cap with embroidered logo",
                price=15.00,
                image_url="/static/img/merch/rammcap.png",
            ),
            Product(
                name="Poster",
                category="special",
                description="Limited edition tour poster with unique design",
                price=5.00,
                image_url="/static/img/merch/rammposter.png",
            ),
        ]
        
        db.add_all(products)
        db.commit()
        print("✅ База данных инициализирована с тестовыми товарами")
    
    db.close()