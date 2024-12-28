let searchTimeout = null;

function initModelSearch() {
    const modelInput = document.getElementById('modelNameInput');
    const resultsContainer = document.getElementById('searchResults');

    modelInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        // Annuler la recherche précédente
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Cacher les résultats si la requête est vide
        if (query.length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        // Attendre que l'utilisateur arrête de taper
        searchTimeout = setTimeout(() => {
            searchModels(query);
        }, 300);
    });

    // Cacher les résultats quand on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.ui.search')) {
            resultsContainer.style.display = 'none';
        }
    });
}

async function searchModels(query) {
    try {
        const response = await fetch('/api/models/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: query })
        });

        const data = await response.json();
        displaySearchResults(data.models);
    } catch (error) {
        console.error('Erreur lors de la recherche:', error);
    }
}

function displaySearchResults(models) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!models || models.length === 0) {
        resultsContainer.style.display = 'none';
        return;
    }

    let html = '<div class="ui relaxed divided list">';
    
    models.forEach(model => {
        html += `
            <div class="item" onclick="selectModel('${model.name}')">
                <div class="content">
                    <div class="header">${model.name}</div>
                    <div class="description">
                        ${model.description || ''}
                        ${model.model_size ? `<span class="ui tiny label">${model.model_size}</span>` : ''}
                        ${model.family ? `<span class="ui tiny label">${model.family}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'block';
}

function selectModel(modelName) {
    document.getElementById('modelNameInput').value = modelName;
    document.getElementById('searchResults').style.display = 'none';
}

// Initialiser la recherche au chargement de la page
document.addEventListener('DOMContentLoaded', initModelSearch);
