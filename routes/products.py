from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.databases import get_db
from models.product import Product
from schemas.product import ProductResponse
from dsa.hash_map import HashMap
from dsa.max_heap import MaxHeap
from dsa.min_heap import MinHeap

router = APIRouter(prefix="/products", tags=["Products"])
product_hash_map = HashMap()
@router.get("/sorted", response_model=list[ProductResponse])
def get_sorted_products(
    restaurant_id: int,
    order: str,
    db: Session = Depends(get_db),
):
    if order not in ["high_to_low", "low_to_high"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order param. Use 'high_to_low' or 'low_to_high'"
        )

    products = db.query(Product).filter(Product.restaurant_id == restaurant_id).all()

    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    heap = MaxHeap() if order == "high_to_low" else MinHeap()

    for p in products:
        heap.insert(p.price, p)

    sorted_products = []

    while not heap.is_empty():
        price, product_obj = (
            heap.extract_max() if order == "high_to_low" else heap.extract_min()
        )
        sorted_products.append(ProductResponse.from_orm(product_obj))

    return sorted_products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    cached_product = product_hash_map.get(product_id)
    if cached_product:
        return cached_product

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_response = ProductResponse.from_orm(product)
    product_hash_map.put(product_id, product_response)

    return product_response