"""
Seed skills data into the database
"""
import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_env():
    """Load environment variables from .env.local"""
    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    os.environ[key] = value


def get_db_connection():
    """Get database connection"""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/learnpath"
    )
    return psycopg2.connect(database_url)


def seed_skills():
    """Seed skills from JSON file"""
    # Load skills data
    skills_file = Path(__file__).parent / "seed_skills.json"
    with open(skills_file) as f:
        skills_data = json.load(f)

    print(f"Loading {len(skills_data)} skills...")

    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Create a mapping of slug to UUID for prerequisite relationships
        slug_to_id = {}

        # First pass: insert all skills
        for skill in skills_data:
            cur.execute(
                """
                INSERT INTO skill (name, slug, level_hint, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (slug) DO UPDATE
                SET name = EXCLUDED.name,
                    level_hint = EXCLUDED.level_hint,
                    description = EXCLUDED.description
                RETURNING id
                """,
                (skill["name"], skill["slug"], skill["level_hint"], skill.get("description")),
            )
            skill_id = cur.fetchone()[0]
            slug_to_id[skill["slug"]] = skill_id
            print(f"  [OK] {skill['name']} ({skill['slug']})")

        # Second pass: create prerequisite edges
        edges_created = 0
        for skill in skills_data:
            skill_id = slug_to_id[skill["slug"]]
            for prereq_slug in skill.get("prerequisites", []):
                if prereq_slug in slug_to_id:
                    prereq_id = slug_to_id[prereq_slug]
                    cur.execute(
                        """
                        INSERT INTO skill_edge (from_skill, to_skill)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (prereq_id, skill_id),
                    )
                    edges_created += 1
                else:
                    print(f"  [WARN] Prerequisite '{prereq_slug}' not found for '{skill['slug']}'")

        conn.commit()
        print(f"\n[OK] Successfully seeded {len(skills_data)} skills and {edges_created} prerequisite relationships")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Error seeding skills: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    """Main entry point"""
    load_env()
    seed_skills()


if __name__ == "__main__":
    main()
