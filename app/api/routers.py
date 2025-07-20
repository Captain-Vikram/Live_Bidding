from fastapi import APIRouter
from app.api.routes import general, auth, listings, commodities, admin, seller, bidding, websocket, price_tracking, mobile, notifications, recommendations

main_router = APIRouter()
main_router.include_router(general.router, prefix="/general", tags=["General"])
main_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
main_router.include_router(listings.router, prefix="/listings", tags=["Listings"])
main_router.include_router(commodities.router, prefix="/commodities", tags=["Commodities"])
main_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
main_router.include_router(seller.router, prefix="/seller", tags=["Seller"])
main_router.include_router(bidding.router, prefix="/bidding", tags=["Bidding"])
main_router.include_router(websocket.router, prefix="/realtime", tags=["Real-time"])
main_router.include_router(price_tracking.router, prefix="/price-tracking", tags=["Price Tracking"])
main_router.include_router(mobile.router, prefix="/mobile", tags=["Mobile & Notifications"])
main_router.include_router(notifications.router, prefix="/api", tags=["Notifications"])
main_router.include_router(recommendations.router, prefix="/ml", tags=["ML Recommendations"])
