# Ollama Model Manager

![Ollama Model Manager Interface](ollama_manager.png)

## Description
A web interface to manage your Ollama models, built with Flask and Semantic UI.

## Features
- Model management (search, download, delete, configure)
- Dark/Light mode (To improve)
- Responsive interface 
- Model usage statistics (Not yet)
- Model configuration  (In progress, not working yet for Huggingface's models)
- Model comparison (In progress)
- Search and pull models directly from HuggingFace or Ollama.com
- English and French languages

## Requirements
- Python 3.8+
- Ollama installed and running
- pip or another Python package manager

## Installation
1. Clone the repository:
```bash
git clone https://github.com/BornSupercharged/OllamaManagerUI.git
cd OllamaManagerUI
```

2. Configuration:
- Copy the example.env file over to ".env" and update the Ollama server URL if necessary:
```bash
OLLAMA_SERVER_URL=http://localhost:11434
```

## Run Using Python
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the application:
```bash
python main.py
```
The application will be accessible at `http://localhost:5000`

## Run Using Docker
1. Clone the repository:
```bash
git clone https://github.com/BornSupercharged/OllamaManagerUI.git
cd OllamaManagerUI
```

2. Update your Ollama environment to fit your needs in `docker-compose.yml`:
```yaml
    environment:
      - OLLAMA_SERVER_URL=http://127.0.0.1:11434
      - FLASK_SECRET_KEY=dev_key_123
      - BABEL_DEFAULT_LOCALE=en
      - BABEL_DEFAULT_TIMEZONE=America/Chicago
      - BABEL_DEFAULT_DATE_FORMAT=YYYY-MM-DD
```

3. Build and start the container:
```bash
docker compose up -d --build
```
The application will be available at `http://localhost:5000`

## Usage
- Access the web interface through your browser
- Use the theme button at the top left to switch between light and dark modes
- Manage your models through the intuitive interface
- View usage statistics
- Configure models individually or in batches

## Python Virtual Environment
```
source venv/bin/activate
```

# Language Translations
## Add translations for a new language 
1. To generate the translation file for all the strings in the project
```
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```

2. To create a brand new translation for a new language
```
pybabel init -i messages.pot -d translations -l fr
```

3. To update the translation file with new translations
```
pybabel update -i messages.pot -d translations
```

4. Re-compile the translations
```
pybabel compile -d translations
```

## Update an existing language's translations
1. To generate the translation file for all the strings in the project
```
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```

2. To update the translation file with new translations
```
pybabel update -i messages.pot -d translations
```

3. Re-compile the translations
```
pybabel compile -d translations
```

## Contribution
Contributions are welcome! Feel free to open an issue or a pull request.

## License
MIT

