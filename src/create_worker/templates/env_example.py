CONTENT = """\
# {project_name} configuration
MICROSERVICE_NAME={project_name}

# Dev mode (uses in-memory queue instead of Oracle)
DEV_MODE=true

# Polling
POLLING_INTERVAL_SECONDS=5
MAX_CONCURRENT_JOBS=10

# HTTP server
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Oracle (required when DEV_MODE=false)
# ORACLE_DSN=XEPDB1
# ORACLE_USER=
# ORACLE_PASSWORD=
# ORACLE_TABLE=MICRO_SVC

# Logging
LOG_CONSOLE_JSON=false
# OTEL_EXPORTER_OTLP_ENDPOINT=
"""
