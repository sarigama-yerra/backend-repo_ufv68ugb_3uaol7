import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="CraftsFusion API", description="Backend for CraftsFusion fantasy-themed fashion storefront")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Models
# ----------------------------
class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    image: Optional[str] = None
    tag: Optional[str] = None
    color: Optional[str] = None

class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    image: Optional[str] = None
    tag: Optional[str] = None
    color: Optional[str] = None

    @classmethod
    def from_mongo(cls, doc: dict):
        return cls(
            id=str(doc.get("_id")),
            title=doc.get("title", ""),
            description=doc.get("description"),
            price=float(doc.get("price", 0)),
            category=doc.get("category", ""),
            image=doc.get("image"),
            tag=doc.get("tag"),
            color=doc.get("color"),
        )


# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def read_root():
    return {"message": "CraftsFusion Backend Running"}


@app.get("/api/products", response_model=List[ProductOut])
def list_products(category: Optional[str] = None, q: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    filt = {}
    if category:
        filt["category"] = category
    if q:
        filt["title"] = {"$regex": q, "$options": "i"}

    docs = get_documents("product", filt)
    return [ProductOut.from_mongo(d) for d in docs]


@app.post("/api/products/seed", response_model=List[ProductOut])
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # If products already exist, return them
    existing = list(db["product"].find({}).limit(1))
    if existing:
        docs = get_documents("product")
        return [ProductOut.from_mongo(d) for d in docs]

    seed_data: List[ProductCreate] = [
        ProductCreate(
            title="Moonlit Petal Gown",
            description="Flowing chiffon gown with iridescent petals and a subtle stardust shimmer.",
            price=189.0,
            category="Dresses",
            image="https://images.unsplash.com/photo-1520975922284-7bcd429ebfd5?q=80&w=1600&auto=format&fit=crop",
            tag="New",
            color="#FDE3E3",
        ),
        ProductCreate(
            title="Sylvan Whisper Blouse",
            description="Sheer organza blouse with embroidered leaves and pearl buttons.",
            price=79.0,
            category="Tops",
            image="https://images.unsplash.com/photo-1520975940279-d6cc6e4be0c3?q=80&w=1600&auto=format&fit=crop",
            tag="Trending",
            color="#E8F5E9",
        ),
        ProductCreate(
            title="Aurora Veil Skirt",
            description="Layered tulle midi skirt that shifts color like the northern lights.",
            price=98.0,
            category="Bottoms",
            image="https://images.unsplash.com/photo-1503342330407-5a4cd4fd63d6?q=80&w=1600&auto=format&fit=crop",
            tag="Bestseller",
            color="#EDE7F6",
        ),
        ProductCreate(
            title="Glimmerleaf Headband",
            description="Delicate headband with glass leaves and starlit crystals.",
            price=32.0,
            category="Accessories",
            image="https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=1600&auto=format&fit=crop",
            tag="Limited",
            color="#FFF8E1",
        ),
        ProductCreate(
            title="Stardrop Perfume Satchel",
            description="Velvet micro bag adorned with a vintage atomizer charm.",
            price=56.0,
            category="Bags",
            image="https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?q=80&w=1600&auto=format&fit=crop",
            tag="Editor’s pick",
            color="#FFE0B2",
        ),
        ProductCreate(
            title="Petal Mist Kimono",
            description="Lightweight satin kimono with hand-painted florals and golden thread.",
            price=129.0,
            category="Outerwear",
            image="https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1600&auto=format&fit=crop",
            tag="New",
            color="#FFF3E0",
        ),
    ]

    ids = []
    for item in seed_data:
        _id = create_document("product", item)
        ids.append(_id)

    docs = get_documents("product")
    return [ProductOut.from_mongo(d) for d in docs]


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
