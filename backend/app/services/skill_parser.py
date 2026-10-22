import re
from typing import Dict, List, Optional, Any


def parse_skill_md(content: str) -> Dict[str, Any]:
    """
    Parse SKILL.md frontmatter (YAML-like) and return extracted metadata.

    Expected frontmatter format:
    ---
    name: skill-name
    display_name: "Display Name"
    description: "Skill description"
    version: "1.0.0"
    author: "Author Name"
    license: "MIT"
    homepage: "https://example.com"
    tags: [tag1, tag2, tag3]
    ---
    """
    result = {}

    # Extract frontmatter between --- delimiters
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)

    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)

        # Parse key-value pairs (simple YAML subset)
        for line in frontmatter.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle key: value format
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Handle array-like tags: [tag1, tag2]
                if key == "tags" and value.startswith("[") and value.endswith("]"):
                    value = value[1:-1]
                    tags = [tag.strip().strip('"\'') for tag in value.split(",") if tag.strip()]
                    result[key] = tags
                else:
                    result[key] = value

    # Ensure name is present (fallback to parsing from content)
    if "name" not in result:
        # Try to find first heading as name
        heading_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if heading_match:
            result["name"] = heading_match.group(1).strip()

    return result


def extract_sections(content: str) -> Dict[str, str]:
    """Extract markdown sections after frontmatter."""
    sections = {}

    # Remove frontmatter
    content_without_fm = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Split by headings
    current_section = "intro"
    current_content = []

    for line in content_without_fm.split("\n"):
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            # Start new section
            current_section = heading_match.group(2).lower().replace(" ", "-")
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def validate_skill_metadata(metadata: Dict[str, Any]) -> List[str]:
    """Validate required skill metadata fields. Returns list of errors."""
    errors = []

    if not metadata.get("name"):
        errors.append("Missing required field: name")

    if not metadata.get("description"):
        errors.append("Missing required field: description")

    # Validate name format (kebab-case)
    name = metadata.get("name", "")
    if name and not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        errors.append("Field 'name' must be kebab-case (lowercase with hyphens)")

    return errors