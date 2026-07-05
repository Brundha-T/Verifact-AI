from locust import HttpUser, task, between

class VeriFactUser(HttpUser):
    # Wait between 2 to 5 seconds between tasks
    wait_time = between(2, 5)

    @task
    def ask_question(self):
        # Simulate a user asking a question to the API
        payload = {
            "question": "What is Machine Learning and what are its main subsets?"
        }
        
        # We target the FastAPI /ask endpoint
        with self.client.post("/ask", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
