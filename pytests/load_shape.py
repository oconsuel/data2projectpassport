from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    step_time = 30  # Время каждого шага в секундах
    step_load = 5   # Количество пользователей, добавляемых на каждом шаге
    spawn_rate = 1  # Скорость появления новых пользователей
    time_limit = 120  # Общая продолжительность теста в секундах

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time + 1
        user_count = int(current_step * self.step_load)
        return (user_count, self.spawn_rate)
