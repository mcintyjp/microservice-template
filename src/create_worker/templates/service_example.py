CONTENT = """\
\"\"\"Example REST API service integration.

Uncomment and customize this to add an external API service.
Register it in your main.py with app.register_service(ExampleAPI).
\"\"\"

# from usvc_lib import RestAPIConfig, RestAPIService
#
#
# class ExampleAPI(RestAPIService):
#     \"\"\"Example external API client.\"\"\"
#
#     name = "example_api"
#     config = RestAPIConfig(
#         BASE_URL="https://api.example.com",
#         RATE_LIMIT_REQUESTS=100,
#         RATE_LIMIT_WINDOW_SECONDS=60.0,
#         MAX_RETRIES=3,
#     )
#
#     async def get_resource(self, resource_id: str) -> dict:
#         \"\"\"Fetch a resource from the external API.\"\"\"
#         response = await self.request("GET", f"{{self.config.BASE_URL}}/resources/{{resource_id}}")
#         response.raise_for_status()
#         return response.json()
"""
