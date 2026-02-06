CONTENT = """\
\"\"\"hello_world action handler.\"\"\"

from usvc_lib import action

from actions.hello_world.schemas import HelloWorldInput


@action(name="hello_world")
async def handle(input_data: HelloWorldInput) -> dict:
    \"\"\"Process a hello_world action.\"\"\"
    return {"message": f"Hello, {input_data.name}!"}
"""
