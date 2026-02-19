"""Templates for dependency update fixes."""

DEPENDENCY_TEMPLATES = {
    "python_requirements_update": {
        "id": "python_requirements_update",
        "name": "Python Requirements Update",
        "description": "Update a Python package in requirements.txt to a fixed version",
        "fix_type": "dependency_update",
        "applicable_to": ["requirements.txt", "python", "pip"],
        "file_pattern": "requirements*.txt",
        "template": """{old_package}=={old_version}
# FIXED: {new_package}=={new_version}""",
        "replacement": "{new_package}=={new_version}",
        "variables": ["old_package", "old_version", "new_package", "new_version"],
        "confidence": "high",
        "test_commands": [
            "pip install -r requirements.txt",
            "pip check",
        ],
    },
    
    "python_pipfile_update": {
        "id": "python_pipfile_update",
        "name": "Python Pipfile Update",
        "description": "Update a Python package in Pipfile",
        "fix_type": "dependency_update",
        "applicable_to": ["Pipfile", "pipenv"],
        "file_pattern": "Pipfile",
        "template": '''{package_name} = "=={old_version}"''',
        "replacement": '''{package_name} = "=={new_version}"''',
        "variables": ["package_name", "old_version", "new_version"],
        "confidence": "high",
        "test_commands": [
            "pipenv install",
            "pipenv check",
        ],
    },
    
    "npm_package_update": {
        "id": "npm_package_update",
        "name": "NPM Package Update",
        "description": "Update an NPM package in package.json",
        "fix_type": "dependency_update",
        "applicable_to": ["package.json", "npm", "node"],
        "file_pattern": "package.json",
        "template": '''"{package_name}": "{old_version}"''',
        "replacement": '''"{package_name}": "{new_version}"''',
        "variables": ["package_name", "old_version", "new_version"],
        "confidence": "high",
        "test_commands": [
            "npm install",
            "npm audit",
        ],
    },
    
    "go_mod_update": {
        "id": "go_mod_update",
        "name": "Go Module Update",
        "description": "Update a Go module in go.mod",
        "fix_type": "dependency_update",
        "applicable_to": ["go.mod", "golang"],
        "file_pattern": "go.mod",
        "template": "{module_path} {old_version}",
        "replacement": "{module_path} {new_version}",
        "variables": ["module_path", "old_version", "new_version"],
        "confidence": "high",
        "test_commands": [
            "go mod tidy",
            "go build ./...",
        ],
    },
}
