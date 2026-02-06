CONTENT = """\
\"\"\"Tests for the hello_world action.\"\"\"

import pytest

from actions.hello_world.handler import handle
from actions.hello_world.schemas import HelloWorldInput


@pytest.mark.asyncio
async def test_hello_world_default_name():
    input_data = HelloWorldInput()
    result = await handle(input_data)
    assert result == {"message": "Hello, World!"}


@pytest.mark.asyncio
async def test_hello_world_custom_name():
    input_data = HelloWorldInput(name="Alice")
    result = await handle(input_data)
    assert result == {"message": "Hello, Alice!"}
"""
