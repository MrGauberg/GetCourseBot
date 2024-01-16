import httpx
from src.core.settings import application_settings
from typing import Dict, Any
from aiogram.types import Document


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
    def _create_assignment_response_url(self):
        return f"{self.BASE_API_URL}/student/create-assignment-response/"

    @property
    def _student_paymant_url(self):
        return f"{self.BASE_API_URL}/student/paymant/create/"

    def _check_payment_url(self, student_id, course_id):
        return f"{self.BASE_API_URL}/student/check-payment/{student_id}/{course_id}/"

    def _check_assignment_response_url(self, student_id, assignment_id):
        return f"{self.BASE_API_URL}/student/check-assignment-response/{student_id}/{assignment_id}/"

    def _lesson_list_url(self, course_id, page):
        return f"{self.BASE_API_URL}/student-course/{course_id}/lessons/?page={page}"

    def _assignment_list_url(self, lesson_id):
        return f"{self.BASE_API_URL}/student-course/lessons/{lesson_id}/assignments"


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
        data: Dict[str, Any] = None,
        files: Dict[str, Any] = None
    ) -> Any:
        try:
            if files:
                # Подготовка данных и файлов для мультипарт-формы
                multipart_data = {}
                for key, value in data.items():
                    multipart_data[key] = (None, str(value))
                for file_key, file_value in files.items():
                    multipart_data[file_key] = file_value
                response = await self.client.request(method, url, files=multipart_data)
            else:
                # Отправка данных в формате JSON, если файлов нет
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

    async def check_assignment_response(self, student_id, assignment_id):
        return await self._make_request(
            "GET", self._check_assignment_response_url(student_id, assignment_id)
        )

    async def get_courses_by_user_id(self, user_id: int, page: int) -> Any:
        url = self._course_list_url(user_id, page)
        return await self._make_request("GET", url)

    async def get_courses_by_student_id(self, tg_user_id: int, page: int) -> Any:
        url = self._student_courses_url(tg_user_id, page)
        return await self._make_request("GET", url)

    async def get_lessons_by_course_id(self, course_id,  page: int):
        return await self._make_request(
            "GET", self._lesson_list_url(course_id, page)
        )

    async def get_assignments_by_lesson_id(self, lesson_id):
        return await self._make_request(
            "GET", self._assignment_list_url(lesson_id)
        )

    async def create_assignment_response(self, data: Dict, files=None) -> Any:

        return await self._make_request(
            "POST", self._create_assignment_response_url, data, files
        )


application_client = ApplicationClient()
