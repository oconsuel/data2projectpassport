from locust import HttpUser, task, between
import os
import re

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def full_flow(self):
        # 1. Создать новый проект
        project_name = "Тестовый проект"
        response = self.client.post(
            "/", 
            data={"name": project_name},
            allow_redirects=False
        )
        location = response.headers.get("Location")
        if not location or "/projects/" not in location:
            response.failure("Проект не создан")
            return
        project_id = re.findall(r"/projects/(\d+)", location)[0]

        # 2. Загрузить три файла
        files_dir = os.path.join(os.path.dirname(__file__), "test_files")
        file_names = ["file1.docx", "file2.pptx"]
        files = []
        try:
            for name in file_names:
                file_path = os.path.join(files_dir, name)
                if os.path.exists(file_path):
                    f = open(file_path, 'rb')
                    files.append(('files', (name, f, 'application/octet-stream')))
                else:
                    print(f"Файл {file_path} не найден.")

            upload_url = f"/projects/{project_id}/upload"
            upload_resp = self.client.post(
                upload_url, 
                files=files, 
                allow_redirects=False,
                catch_response=True
            )
            if upload_resp.status_code == 303:
                upload_resp.success()
            else:
                upload_resp.failure(f"Ошибка загрузки файлов: {upload_resp.status_code}")
        finally:
            # обязательно закрыть файлы!
            for tup in files:
                tup[1][1].close()
