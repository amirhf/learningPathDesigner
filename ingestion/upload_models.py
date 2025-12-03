"""
Script to download models from Hugging Face and upload to GCS.
Run this locally to populate the cache bucket.
"""
import os
import logging
import shutil
import subprocess
from pathlib import Path
from huggingface_hub import snapshot_download

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BUCKET_NAME = "learnpath-models-learnpath-prod"
MODELS = {
    "embedding": "intfloat/e5-base-v2",
    "reranker": "BAAI/bge-reranker-base"
}
LOCAL_CACHE_DIR = Path("./temp_model_cache")

def download_and_upload():
    """Download from HF and upload to GCS"""
    for model_type, model_id in MODELS.items():
        logger.info(f"Processing {model_type} model: {model_id}")
        
        # 1. Download from HF
        local_model_path = LOCAL_CACHE_DIR / model_type
        if not local_model_path.exists():
            logger.info(f"Downloading {model_id} from Hugging Face...")
            snapshot_download(repo_id=model_id, local_dir=local_model_path)
        else:
            logger.info(f"Model already downloaded locally at {local_model_path}")

        # 2. Upload to GCS using gcloud CLI
        gcs_path = f"gs://{BUCKET_NAME}/{model_type}"
        logger.info(f"Uploading {model_id} to {gcs_path}...")
        
        # Use recursive copy
        cmd = ["gcloud", "storage", "cp", "-r", str(local_model_path), f"gs://{BUCKET_NAME}/"]
        
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully uploaded {model_type}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to upload {model_type}: {e}")

    # Cleanup
    logger.info("Cleaning up local cache...")
    shutil.rmtree(LOCAL_CACHE_DIR)
    logger.info("Done!")

if __name__ == "__main__":
    download_and_upload()
