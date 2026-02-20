CONTENT = """\
\"\"\"Entry point for the $project_name microservice.\"\"\"

from usvc_lib import Application

from ${module_name}.config import Settings


def main() -> None:
    app = Application(settings_class=Settings)
    app.run()


if __name__ == "__main__":
    main()
"""
