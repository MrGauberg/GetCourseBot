import httpx
from src.core.settings import application_settings
from typing import Dict, Any, List, Tuple
from src.core.config import user_settings

class AplicationEndpoints:
    BASE_API_URL = application_settings.APPLICATION_URL

    def _course_list_url(self, instructor_id, page):
        # return f"{self.BASE_API_URL}/student-course/courses/{instructor_id}/?page={page}"
        return f"{self.BASE_API_URL}/courses/courses/{instructor_id}/?page={page}&page_size=5"

    def _student_courses_url(self, tg_user_id, page):
        return f"{self.BASE_API_URL}/student/student-courses/{tg_user_id}/?page={page}&page_size=5"

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
        # return f"{self.BASE_API_URL}/student-course/{course_id}/lessons/?page={page}"
        return f"{self.BASE_API_URL}/courses/{course_id}/lessons/?page={page}&page_size=5"

    def _assignment_list_url(self, lesson_id):
        # return f"{self.BASE_API_URL}/student-course/lessons/{lesson_id}/assignments"
        return f"{self.BASE_API_URL}/courses/lessons/{lesson_id}/assignments"

    def _get_tg_user(self, tg_id):
        return f"{self.BASE_API_URL}/student/get_student/{tg_id}/"

    def _update_tg_user(self, tg_id):
        return f"{self.BASE_API_URL}/student/update-student/{tg_id}/"
    
    def _get_calendar_data(self, year, month):
        return f"{self.BASE_API_URL}/event_calendar/{year}/{month}/"


class ApplicationClient(AplicationEndpoints):

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(follow_redirects=True)

    async def close(self) -> None:
        if not self.client.is_closed:
            await self.client.aclose()

    async def authenticate(self) -> None:

        email = user_settings.EMAIL
        password = user_settings.PASSWORD

        """
        Авторизация и получение начальных токенов.
        """
        url = f"{self.BASE_API_URL}/auth/token/"
        try:
            response = await self.client.post(
                url,
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            tokens = response.json()
            self.access_token = tokens.get("access")
            self.refresh_token = tokens.get("refresh")
            print("Authentication successful. Tokens received.")
        except httpx.HTTPError as e:
            print(f"Authentication failed: {e}")
            print(application_settings.APPLICATION_URL)
            raise

    async def ensure_authenticated(self) -> None:
        """
        Гарантирует, что токены присутствуют и действительны.
        """
        if not self.access_token or not self.refresh_token:
            print("Tokens are missing. Authenticating...")
            await self.authenticate()
        
    async def refresh_access_token(self) -> None:
        """
        Обновляет access_token с использованием refresh_token.
        Если refresh_token недействителен, выполняет повторную авторизацию.
        """
        if not self.refresh_token:
            print("Refresh token is missing. Re-authenticating.")
            await self.authenticate()
            return

        url = f"{self.BASE_API_URL}/auth/token/refresh/"
        try:
            response = await self.client.post(
                url,
                json={"refresh": self.refresh_token},
            )
            response.raise_for_status()
            tokens = response.json()
            self.access_token = tokens.get("access")
            self.refresh_token = tokens.get("refresh")
            print("Access token refreshed successfully.")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:  # Если refresh_token просрочился
                print("Refresh token expired. Re-authenticating.")
                await self.authenticate()  # Полная авторизация
            else:
                print(f"Failed to refresh token: {e}")
                raise


    async def _make_request(
        self,
        method: str,
        url: str,
        data: Dict[str, Any] = None,
        files: List[Tuple[str, Tuple[str, bytes, str]]] = None,
        headers: Dict[str, str] = None
    ) -> Any:
        try:
            headers = headers or {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"

            if files:
                response = await self.client.request(method, url, data=data, files=files, headers=headers)
            else:
                response = await self.client.request(method, url, json=data, headers=headers)

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:  # Ошибка авторизации
                print("Access token expired. Attempting to refresh token.")
                try:
                    await self.refresh_access_token()  # Попробовать обновить токен
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = await self.client.request(method, url, json=data, headers=headers)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as refresh_error:
                    if refresh_error.response.status_code == 401:  # Refresh тоже недействителен
                        print("Refresh token expired. Re-authenticating.")
                        await self.authenticate()  # Полная авторизация
                        headers["Authorization"] = f"Bearer {self.access_token}"
                        response = await self.client.request(method, url, json=data, headers=headers)
                        response.raise_for_status()
                        return response.json()
                    else:
                        raise refresh_error
            else:
                raise


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

    async def get_tg_user(self, tg_id):
        return await self._make_request(
            "GET", self._get_tg_user(tg_id)
        )

    async def update_tg_user(self, tg_id, data):
        return await self._make_request(
            "patch", self._update_tg_user(tg_id), data
        )
    
    async def get_calendar_data(self, year, month):
        return await self._make_request(
            "GET", self._get_calendar_data(year, month)
        )



application_client = ApplicationClient()
