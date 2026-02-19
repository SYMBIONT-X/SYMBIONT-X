"""Templates for configuration fixes."""

CONFIG_TEMPLATES = {
    "disable_debug_mode": {
        "id": "disable_debug_mode",
        "name": "Disable Debug Mode",
        "description": "Disable debug mode in production configuration",
        "fix_type": "config_change",
        "applicable_to": ["debug", "DEBUG", "production"],
        "patterns": [
            ("DEBUG = True", "DEBUG = False"),
            ("debug: true", "debug: false"),
            ("DEBUG=true", "DEBUG=false"),
            ('"debug": true', '"debug": false'),
        ],
        "confidence": "high",
        "test_commands": [],
    },
    
    "secure_cookie_settings": {
        "id": "secure_cookie_settings",
        "name": "Secure Cookie Settings",
        "description": "Enable secure cookie flags",
        "fix_type": "config_change",
        "applicable_to": ["cookie", "session", "security"],
        "additions": [
            "SESSION_COOKIE_SECURE = True",
            "SESSION_COOKIE_HTTPONLY = True",
            "SESSION_COOKIE_SAMESITE = 'Strict'",
        ],
        "confidence": "high",
    },
    
    "enable_https_redirect": {
        "id": "enable_https_redirect",
        "name": "Enable HTTPS Redirect",
        "description": "Force HTTPS redirects",
        "fix_type": "config_change",
        "applicable_to": ["http", "https", "ssl", "tls"],
        "additions": [
            "SECURE_SSL_REDIRECT = True",
            "SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')",
        ],
        "confidence": "medium",
    },
    
    "fix_cors_settings": {
        "id": "fix_cors_settings",
        "name": "Restrict CORS Settings",
        "description": "Replace wildcard CORS with specific origins",
        "fix_type": "config_change",
        "applicable_to": ["cors", "CORS", "origin"],
        "patterns": [
            ('CORS_ALLOW_ALL_ORIGINS = True', 'CORS_ALLOW_ALL_ORIGINS = False'),
            ('Access-Control-Allow-Origin: *', '# TODO: Set specific allowed origins'),
            ("allow_origins=['*']", "allow_origins=['https://yourdomain.com']"),
        ],
        "confidence": "medium",
    },
    
    "bind_localhost_only": {
        "id": "bind_localhost_only",
        "name": "Bind to Localhost Only",
        "description": "Change binding from 0.0.0.0 to localhost",
        "fix_type": "config_change",
        "applicable_to": ["bind", "host", "0.0.0.0"],
        "patterns": [
            ('host = "0.0.0.0"', 'host = "127.0.0.1"'),
            ("host: 0.0.0.0", "host: 127.0.0.1"),
            ('HOST = "0.0.0.0"', 'HOST = "127.0.0.1"'),
        ],
        "confidence": "medium",
        "warning": "May break external access - review before applying",
    },
    
    "remove_hardcoded_secret": {
        "id": "remove_hardcoded_secret",
        "name": "Remove Hardcoded Secret",
        "description": "Replace hardcoded secrets with environment variables",
        "fix_type": "secret_rotation",
        "applicable_to": ["secret", "password", "api_key", "token"],
        "template": '''# OLD: {variable_name} = "{secret_value}"
{variable_name} = os.environ.get("{env_var_name}")''',
        "imports_needed": ["import os"],
        "confidence": "high",
        "requires_env_setup": True,
    },
}
