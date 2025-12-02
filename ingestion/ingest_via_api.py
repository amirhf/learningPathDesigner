"""
Ingest data via the Ingestion Service API
This script can be used to populate production data
"""
import json
import sys
from pathlib import Path
import requests


def ingest_skills(api_url: str, skills_file: Path, tenant_id: str = "global"):
    """Ingest skills via API"""
    with open(skills_file) as f:
        skills_data = json.load(f)
    
    # Inject tenant_id
    for skill in skills_data:
        skill["tenant_id"] = tenant_id

    print(f"Ingesting {len(skills_data)} skills for tenant '{tenant_id}'...")
    
    response = requests.post(
        f"{api_url}/ingest/skills",
        json={"skills": skills_data},
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Success: {result['success']}/{result['total']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors'][:5]:
                print(f"    - {error}")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)


def ingest_resources(api_url: str, resources_file: Path, generate_embeddings: bool = False, extract_content: bool = False, tenant_id: str = "global"):
    """Ingest resources via API"""
    with open(resources_file) as f:
        resources_data = json.load(f)
    
    # Inject tenant_id
    for resource in resources_data:
        resource["tenant_id"] = tenant_id

    print(f"\nIngesting {len(resources_data)} resources for tenant '{tenant_id}'...")
    if extract_content:
        print("  - Extracting content snippets from URLs")
    if generate_embeddings:
        print("  - Generating embeddings for search")
    
    response = requests.post(
        f"{api_url}/ingest/resources",
        json={
            "resources": resources_data,
            "generate_embeddings": generate_embeddings,
            "extract_content": extract_content
        },
        timeout=600  # Increased timeout for content extraction
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Success: {result['success']}/{result['total']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors'][:5]:
                print(f"    - {error}")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest data via Ingestion Service API")
    parser.add_argument("--api-url", required=True, help="RAG service URL (e.g., https://rag-service-xxx.run.app)")
    parser.add_argument("--skills", action="store_true", help="Ingest skills")
    parser.add_argument("--resources", action="store_true", help="Ingest resources")
    parser.add_argument("--embeddings", action="store_true", help="Generate embeddings for resources")
    parser.add_argument("--extract-content", action="store_true", help="Extract content snippets from URLs for quiz generation")
    parser.add_argument("--tenant-id", default="global", help="Tenant ID to associate data with (default: global)")
    
    args = parser.parse_args()
    
    # Check health
    try:
        response = requests.get(f"{args.api_url}/health", timeout=10)
        health = response.json()
        print(f"Service status: {health.get('status', 'unknown')}")
        if 'qdrant_connected' in health:
            print(f"Qdrant connected: {health['qdrant_connected']}")
        print()
    except Exception as e:
        print(f"✗ Failed to connect to service: {e}")
        sys.exit(1)
    
    # Ingest skills
    if args.skills:
        skills_file = Path(__file__).parent / "seed_skills.json"
        if not skills_file.exists():
            print(f"✗ Skills file not found: {skills_file}")
            sys.exit(1)
        ingest_skills(args.api_url, skills_file, args.tenant_id)
    
    # Ingest resources
    if args.resources:
        resources_file = Path(__file__).parent / "seed_resources.json"
        if not resources_file.exists():
            print(f"✗ Resources file not found: {resources_file}")
            sys.exit(1)
        ingest_resources(args.api_url, resources_file, args.embeddings, args.extract_content, args.tenant_id)
    
    print("\n✓ Ingestion complete!")


if __name__ == "__main__":
    main()
