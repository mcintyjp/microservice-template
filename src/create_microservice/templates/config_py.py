CONTENT = """\
\"\"\"Custom settings for the $project_name microservice.

Add environment variables specific to this microservice below.
All base settings (MICROSERVICE_NAME, DEV_MODE, etc.) are inherited.
\"\"\"

from usvc_lib import WorkerSettings


class Settings(WorkerSettings):
    # Add your custom environment variables here, e.g.:
    # MY_API_KEY: str = ""
    # CUSTOM_TIMEOUT: int = 30
    pass
"""
