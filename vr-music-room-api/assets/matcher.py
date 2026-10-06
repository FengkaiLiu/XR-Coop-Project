import os
import json
from sqlalchemy.orm import Session
from db.models import PreloadedAsset

ASSET_DIR = os.path.join("static", "assets")

def scan_and_register_assets(db: Session):
    """Scan the static/assets folder and register any new files in the database."""
    for asset_type in ["skyboxes", "textures"]:
        type_dir = os.path.join(ASSET_DIR, asset_type)
        if not os.path.exists(type_dir):
            continue

        for mood_folder in os.listdir(type_dir):
            folder_path = os.path.join(type_dir, mood_folder)
            if not os.path.isdir(folder_path):
                continue

            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if not os.path.isfile(file_path):
                    continue

                # Skip if already registered
                existing = db.query(PreloadedAsset).filter(
                    PreloadedAsset.file_path == file_path
                ).first()
                if existing:
                    continue

                # Register new asset with mood folder name as tag
                asset = PreloadedAsset(
                    asset_type="skybox" if asset_type == "skyboxes" else "texture",
                    tags=json.dumps([mood_folder]),
                    file_path=file_path,
                )
                db.add(asset)

        db.commit()

def match_assets(mood_tags: list, asset_type: str, db: Session) -> list:
    """Find pre-made assets that match the given mood tags.
    Returns assets sorted by match score (best first)."""
    all_assets = db.query(PreloadedAsset).filter(
        PreloadedAsset.asset_type == asset_type
    ).all()

    scored = []
    for asset in all_assets:
        asset_tags = json.loads(asset.tags)
        # Count how many mood tags match this asset's tags
        matches = len(set(mood_tags) & set(asset_tags))
        if matches > 0:
            score = matches / max(len(mood_tags), len(asset_tags))
            scored.append({
                "id": asset.id,
                "file_path": asset.file_path,
                "file_url": f"/static/assets/{asset_type}s/{asset_tags[0]}/{os.path.basename(asset.file_path)}",
                "tags": asset_tags,
                "match_score": round(score, 2),
            })

    # Sort by match score, best first
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored