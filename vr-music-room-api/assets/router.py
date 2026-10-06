from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db.database import get_db
from assets.matcher import match_assets, scan_and_register_assets

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/scan")
def scan_assets(db: Session = Depends(get_db)):
    """Scan the static/assets folder and register new files in the DB.
    Run this after adding new pre-made assets."""
    scan_and_register_assets(db)
    return {"message": "Asset scan complete"}

@router.get("/match")
def get_matching_assets(
    tags: str = Query(..., description="Comma-separated mood tags, e.g. 'euphoric,driving'"),
    type: str = Query("skybox", description="'skybox' or 'texture'"),
    db: Session = Depends(get_db),
):
    """Find pre-made assets matching the given mood tags."""
    tag_list = [t.strip() for t in tags.split(",")]
    results = match_assets(tag_list, type, db)

    return {
        "query_tags": tag_list,
        "asset_type": type,
        "matched": len(results) > 0,
        "assets": results,
    }

@router.get("/download/{asset_id}")
def download_asset(asset_id: str, db: Session = Depends(get_db)):
    """Download a specific asset file by ID."""
    from db.models import PreloadedAsset
    asset = db.query(PreloadedAsset).filter(PreloadedAsset.id == asset_id).first()
    if not asset:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(asset.file_path)

@router.get("/list")
def list_all_assets(
    type: str = Query(None, description="Filter by 'skybox' or 'texture'"),
    db: Session = Depends(get_db),
):
    """List all registered pre-made assets."""
    from db.models import PreloadedAsset
    import json

    query = db.query(PreloadedAsset)
    if type:
        query = query.filter(PreloadedAsset.asset_type == type)

    assets = query.all()
    return {
        "total": len(assets),
        "assets": [
            {
                "id": a.id,
                "type": a.asset_type,
                "tags": json.loads(a.tags),
                "file_path": a.file_path,
            }
            for a in assets
        ],
    }