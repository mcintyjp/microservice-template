CONTENT = """\
\"\"\"Input schema for hello_world action.\"\"\"

from pydantic import BaseModel


class HelloWorldInput(BaseModel):
    name: str = "World"
"""
