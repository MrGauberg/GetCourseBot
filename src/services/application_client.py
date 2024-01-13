import httpx
from src.core.settings import application_settings
from typing import Dict, Any


class AplicationEndpoints:
    BASE_API_URL = application_settings.APPLICATION_URL

    def _course_list_url(self, instructor_id, page):
        return f"{self.BASE_API_URL}/student-course/courses/{instructor_id}/?page={page}"

    def _student_courses_url(self, tg_user_id, page):
        return f"{self.BASE_API_URL}/student/student-courses/{tg_user_id}/?page={page}"

    @property
    def _create_student_url(self):
        return f"{self.BASE_API_URL}/student/create-student/"

    @property
    def _student_paymant_url(self):
        return f"{self.BASE_API_URL}/student/paymant/create/"

    def _check_payment_url(self, student_id, course_id):
        return f"{self.BASE_API_URL}/student/check-payment/{student_id}/{course_id}/"


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

    async def create_students(self, data: Dict) -> Any:
        return await self._make_request("POST", self._create_student_url, data)

    async def create_student_paymant(self, data: Dict) -> Any:
        return await self._make_request("POST", self._student_paymant_url, data)

    async def check_payment(self, student_id, course_id):
        return await self._make_request(
            "GET", self._check_payment_url(student_id, course_id)
        )

    async def get_courses_by_user_id(self, user_id: int, page: int) -> Any:
        url = self._course_list_url(user_id, page)
        return await self._make_request("GET", url)

    async def get_courses_by_student_id(self, tg_user_id: int, page: int) -> Any:
        url = self._student_courses_url(tg_user_id, page)
        return await self._make_request("GET", url)


application_client = ApplicationClient()
