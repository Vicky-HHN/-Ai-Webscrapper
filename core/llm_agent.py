import json
import ollama
from config import OLLAMA_MODEL, OLLAMA_HOST

class LLMAgent:
    def __init__(self, model=OLLAMA_MODEL):
        self.model = model
        self.client = ollama.Client(host=OLLAMA_HOST)

    def interpret_prompt(self, prompt):
        """
        Interprets the user prompt to identify target URL and fields to extract.
        """
        system_prompt = (
            "You are an AI assistant that helps with web scraping. "
            "Given a user prompt, identify the target URL and the data fields they want to extract. "
            "Also suggest additional relevant fields and provide CSS selectors or XPath hints if possible. "
            "Return the response in strictly JSON format with keys: 'url', 'fields', 'suggested_fields', 'selectors'."
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt},
                ],
                format='json'
            )
            return json.loads(response['message']['content'])
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            # Fallback to mistral if llama3 fails or is not available
            if self.model != "mistral":
                print("Attempting fallback to mistral...")
                self.model = "mistral"
                return self.interpret_prompt(prompt)
            raise Exception("Ollama is not running or model is not available. Please start Ollama and pull required models.")

    def validate_data(self, data, prompt):
        """
        Validates whether the scraped data matches the user's intent.
        """
        system_prompt = (
            "You are a data validator. Given a user prompt and some scraped data, "
            "determine if the data looks correct and relevant. "
            "Return a JSON with 'is_valid' (boolean) and 'anomalies' (list of strings)."
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Prompt: {prompt}\nData: {json.dumps(data[:3])}"},
                ],
                format='json'
            )
            return json.loads(response['message']['content'])
        except Exception as e:
            print(f"Error validating data with Ollama: {e}")
            return {"is_valid": True, "anomalies": ["Could not validate with LLM"]}
