"""Fix templates for common vulnerabilities."""

from .dependency_templates import DEPENDENCY_TEMPLATES
from .config_templates import CONFIG_TEMPLATES
from .dockerfile_templates import DOCKERFILE_TEMPLATES
from .template_engine import TemplateEngine

__all__ = [
    "DEPENDENCY_TEMPLATES",
    "CONFIG_TEMPLATES", 
    "DOCKERFILE_TEMPLATES",
    "TemplateEngine",
]
