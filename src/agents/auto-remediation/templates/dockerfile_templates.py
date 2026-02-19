"""Templates for Dockerfile fixes."""

DOCKERFILE_TEMPLATES = {
    "use_specific_base_image": {
        "id": "use_specific_base_image",
        "name": "Use Specific Base Image Tag",
        "description": "Replace 'latest' tag with specific version",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "FROM", "latest"],
        "patterns": [
            ("FROM python:latest", "FROM python:3.11-slim"),
            ("FROM node:latest", "FROM node:20-alpine"),
            ("FROM ubuntu:latest", "FROM ubuntu:22.04"),
            ("FROM nginx:latest", "FROM nginx:1.25-alpine"),
        ],
        "confidence": "high",
    },
    
    "add_user_instruction": {
        "id": "add_user_instruction",
        "name": "Add Non-Root User",
        "description": "Run container as non-root user",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "root", "user"],
        "addition_before_cmd": """
# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
""",
        "confidence": "high",
    },
    
    "add_healthcheck": {
        "id": "add_healthcheck",
        "name": "Add Health Check",
        "description": "Add HEALTHCHECK instruction",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "health"],
        "addition": """
# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1
""",
        "variables": ["port"],
        "confidence": "medium",
    },
    
    "remove_sudo": {
        "id": "remove_sudo",
        "name": "Remove sudo from Dockerfile",
        "description": "Remove unnecessary sudo usage",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "sudo"],
        "patterns": [
            ("RUN sudo ", "RUN "),
            ("sudo apt-get", "apt-get"),
            ("sudo pip", "pip"),
        ],
        "confidence": "high",
    },
    
    "use_copy_instead_of_add": {
        "id": "use_copy_instead_of_add",
        "name": "Use COPY Instead of ADD",
        "description": "Replace ADD with COPY when not extracting archives",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "ADD"],
        "pattern_regex": r"ADD\s+([^\s]+\.(?!tar|gz|zip|bz2)[^\s]+)\s+",
        "replacement": r"COPY \1 ",
        "confidence": "high",
    },
    
    "pin_apt_versions": {
        "id": "pin_apt_versions",
        "name": "Clean APT Cache",
        "description": "Add apt cache cleanup to reduce image size",
        "fix_type": "dockerfile_fix",
        "applicable_to": ["Dockerfile", "apt-get install"],
        "patterns": [
            (
                "RUN apt-get update && apt-get install -y",
                "RUN apt-get update && apt-get install -y --no-install-recommends"
            ),
        ],
        "addition_after": " && rm -rf /var/lib/apt/lists/*",
        "confidence": "high",
    },
}
