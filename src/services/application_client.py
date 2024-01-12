import httpx
from src.core.settings import application_settings
from typing import Dict, Any


class AplicationEndpoints:

    def _course_list_endpoint(self, instructor_id, page):
        print(application_settings.APPLICATION_URL)
        return f"{application_settings.APPLICATION_URL}/student-course/courses/{instructor_id}/?page={page}"


class ApplicationClient(AplicationEndpoints):

    def __init__(self) -> None:
        self.client = httpx.AsyncClient()

    async def close(self) -> None:
        if not self.client.is_closed:
            await self.client.aclose()

    async def _make_request(
            self,
            method: str,
            url: str,
            data: Dict[str, Any] = None
    ) -> Any:
        try:
            response = await self.client.request(method, url, json=data)

            return response.json()
        except httpx.HTTPError as error:
            print(error)

    async def get_courses_by_user_id(self, user_id: int, page: int) -> Any:
        url = self._course_list_endpoint(user_id, page)
        return await self._make_request("GET", url)


application_client = ApplicationClient()