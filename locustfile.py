from locust import HttpUser, task, between

class AdminUser(HttpUser):
    wait_time = between(1, 1)
    token = None

    def on_start(self):
        response = self.client.post("/api/token/", json={
            "username": "admin",
            "password": "admin"
        })
        if response.status_code == 200:
            self.token = response.json().get("access")
        else:
            print("Failed to login:", response.text)

    @task
    def get_vendors_list(self):
        if self.token:
            self.client.get(
                "/api/vendors/",
                headers={"Authorization": f"Bearer {self.token}"}
            )
