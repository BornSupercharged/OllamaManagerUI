import requests
from flask_babel import gettext
from requests.exceptions import ConnectionError, RequestException, Timeout
from models import ModelUsage
import time
import os
import json

class OllamaClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('OLLAMA_SERVER_URL', 'http://localhost:11434')
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        self.api_key = os.environ.get('OLLAMA_API_KEY')
        self.max_retries = 3
        self.retry_delay = 1
        self._server_status = None
        self._last_check = 0
        self._check_interval = 5
        print( gettext("Initialized OllamaClient with base URL: %s" % self.base_url) )

    def _get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def _handle_request(self, method, endpoint, **kwargs):
        """Generic method to handle requests with retry mechanism"""
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]

        url = f'{self.base_url}/{endpoint}'
        retries = 0
        last_error = None
        current_delay = self.retry_delay

        while retries < self.max_retries:
            try:
                kwargs['timeout'] = kwargs.get('timeout', 30)
                kwargs['headers'] = {**self._get_headers(), **kwargs.get('headers', {})}

                response = method(url, **kwargs)
                if response.status_code == 404:
                    return {'models': []} if 'tags' in endpoint or 'ps' in endpoint else {}

                response.raise_for_status()
                return response.json() if response.content else {}

            except ConnectionError:
                last_error = gettext("Unable to connect to Ollama server")
            except Timeout:
                last_error = gettext("Connection to Ollama server timed out")
            except RequestException as e:
                if hasattr(e, 'response') and e.response and e.response.status_code == 503:
                    last_error = gettext("Ollama server is not running")
                else:
                    last_error = gettext("Server error: %s" % str(e))

            retries += 1
            if retries < self.max_retries:
                time.sleep(current_delay)
                current_delay *= 2

        return {'error': last_error}

    def save_model_config(self, model_name, system=None, template=None, parameters=None):
        """Save model configuration by creating a new custom model"""
        try:
            # Build Model file content
            modelfile = f"FROM {model_name}\n"

            # Add parameters if provided
            if parameters:
                for key, value in parameters.items():
                    modelfile += f'PARAMETER {key} {value}\n'

            # Add system prompt if provided
            if system:
                modelfile += f'SYSTEM """{system}"""\n'

            # Add template if provided    
            if template:
                modelfile += f'TEMPLATE """{template}"""\n'

            print( gettext("Creating model with file: %s" % modelfile) )  # Debug log

            # Create new model using Ollama API with streaming response handling
            url = f'{self.base_url}/api/create'
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    'name': model_name,
                    'modelfile': modelfile
                },
                stream=True
            )

            response.raise_for_status()

            # Process the streaming response
            error = None
            status = None
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'error' in data:
                            error = data['error']
                            break
                        if 'status' in data:
                            status = data['status']
                            if status == 'success':
                                break
                    except json.JSONDecodeError:
                        continue

            if error:
                return {'success': False, 'error': error}

            return {'success': True, 'message': gettext("Configuration for %s saved successfully" % model_name) }

        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_server(self):
        """Check if Ollama server is running with caching"""
        current_time = time.time()
        if self._server_status is not None and (current_time - self._last_check) < self._check_interval:
            return self._server_status

        try:
            if not self.base_url:
                self._server_status = False
                return False

            response = requests.get(
                f'{self.base_url}/api/tags',
                headers=self._get_headers(),
                timeout=5
            )
            self._server_status = response.status_code == 200
        except Exception as e:
            print( gettext("Server check failed with error: %s" % str(e)) )
            self._server_status = False

        self._last_check = current_time
        return self._server_status

    def list_models(self):
        """List all available models with full details"""
        response = self._handle_request(requests.get, 'api/tags')
        if 'error' in response:
            return {'models': [], 'error': response['error']}

        # Fetch additional details for each model
        models = response.get('models', [])
        for model in models:
            details = self.get_model_details(model['name'])
            if 'error' not in details:
                model['modified_at'] = details.get('modified_at', model.get('modified_at', ''))

        return {'models': models}

    def list_running(self):
        """List all running models"""
        response = self._handle_request(requests.get, 'api/ps')
        if 'error' in response:
            return {'models': [], 'error': response['error']}
        return response

    def stop_model(self, model_name):
        """Stop a running model"""
        try:
            # First verify if the model is running
            running_models = self.list_running()
            if 'error' in running_models:
                return {'success': False, 'error': running_models['error']}

            if not any(model['name'] == model_name for model in running_models.get('models', [])):
                return {'success': True, 'message': gettext("The model %s is not running" % model_name)}

            # Send stop command
            response = self._handle_request(
                requests.post,
                'api/generate',
                json={'model': model_name, 'prompt': '', 'keep_alive': '0s'}
            )

            if 'error' in response:
                return {'success': False, 'error': response['error']}

            # Verify the model was stopped
            time.sleep(1)  # Give server time to process
            running_models = self.list_running()
            if 'error' in running_models:
                return {'success': False, 'error': running_models['error']}

            if not any(model['name'] == model_name for model in running_models.get('models', [])):
                return {'success': True, 'message': gettext("The model %s has been stopped successfully" % model_name)}
            else:
                return {'success': False, 'error': gettext("Unable to stop model %s" % model_name)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_model(self, model_name):
        """Delete a model"""
        response = self._handle_request(
            requests.delete,
            'api/delete',
            json={'name': model_name}
        )
        if 'error' in response:
            return {'success': False, 'error': response['error']}
        return {'success': True, 'message': gettext("The model %s was successfully deleted" % model_name)}

    def get_model_stats(self, model_name=None):
        """Get usage statistics for a specific model or all models"""
        return ModelUsage.get_model_stats(model_name)

    def get_model_config(self, model_name):
        """Get model configuration details"""
        try:
            response = self._handle_request(
                requests.post,
                'api/show',
                json={'name': model_name}
            )
            if 'error' in response:
                return {'error': response['error']}

            return {
                'modelfile': response.get('modelfile', ''),
                'parameters': self._extract_parameters(response.get('modelfile', '')),
                'template': self._extract_template(response.get('modelfile', '')),
                'system': self._extract_system(response.get('modelfile', ''))
            }
        except Exception as e:
            return {'error': str(e)}

    def _extract_parameters(self, modelfile):
        parameters = {}
        for line in modelfile.split('\n'):
            if line.startswith('PARAMETER'):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    key = parts[1]
                    value = parts[2].strip('"')
                    parameters[key] = value
        return parameters

    def _extract_template(self, modelfile):
        start = modelfile.find('TEMPLATE')
        if start == -1:
            return ""

        template_line = modelfile[start:].split('\n')[0]
        template = template_line.split('"')[1] if '"' in template_line else ""
        return template

    def _extract_system(self, modelfile):
        start = modelfile.find('SYSTEM')
        if start == -1:
            return ""

        system_line = modelfile[start:].split('\n')[0]
        system = system_line.split('SYSTEM', 1)[1].strip()
        return system

    def get_model_details(self, model_name):
        """Get full model details including creation date"""
        try:
            response = self._handle_request(
                requests.post,
                'api/show',
                json={'name': model_name}
            )
            if 'error' in response:
                return {'error': response['error']}

            return {
                'details': response.get('details', {}),
                'modified_at': response.get('modified_at', '')
            }
        except Exception as e:
            return {'error': str(e)}