CONTENT = """\
\"\"\"Entry point for the {project_name} microservice.\"\"\"

from usvc_lib import Application


def main() -> None:
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
"""
