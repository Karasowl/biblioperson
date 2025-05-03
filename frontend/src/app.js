// JavaScript para la Biblioteca de Conocimiento Personal

// Variables globales
const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5000' // URL para desarrollo local
    : 'https://biblioperson.onrender.com'; // URL para producción

let currentPage = 1;
let resultsPerPage = 10;
let currentResults = [];

// Inicialización cuando el DOM está cargado
document.addEventListener('DOMContentLoaded', function() {
    // Configurar navegación
    setupNavigation();
    
    // Cargar datos iniciales
    loadInitialData();
    
    // Configurar eventos
    setupEventListeners();
    
    // Mostrar URLs de API en la documentación
    document.querySelectorAll('[id^="api-url"]').forEach(el => {
        el.textContent = API_BASE_URL;
    });
});

// Configurar navegación entre secciones
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remover clase active de todos los links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Añadir clase active al link actual
            this.classList.add('active');
            
            // Ocultar todas las secciones
            sections.forEach(section => section.classList.remove('active'));
            
            // Mostrar la sección correspondiente
            const targetId = this.id.replace('nav-', '') + '-section';
            document.getElementById(targetId).classList.add('active');
        });
    });
}

// Cargar datos iniciales
async function loadInitialData() {
    try {
        // Cargar estadísticas generales
        const infoResponse = await fetch(`${API_BASE_URL}/api/info`);
        const infoData = await infoResponse.json();
        
        // Actualizar estadísticas en la página
        document.getElementById('total-contenidos').textContent = infoData.total_contenidos || '0';
        
        // Formatear fechas
        if (infoData.rango_fechas) {
            const primeraFecha = new Date(infoData.rango_fechas.primera);
            const ultimaFecha = new Date(infoData.rango_fechas.ultima);
            
            document.getElementById('primera-fecha').textContent = primeraFecha.toLocaleDateString();
            document.getElementById('ultima-fecha').textContent = ultimaFecha.toLocaleDateString();
        }
        
        // Crear gráfico de distribución de plataformas
        if (infoData.distribucion_plataformas && infoData.distribucion_plataformas.length > 0) {
            createPlatformChart(infoData.distribucion_plataformas);
        }
        
        // Llenar selector de plataformas
        if (infoData.distribucion_plataformas) {
            const plataformaSelect = document.getElementById('plataforma-filter');
            plataformaSelect.innerHTML = '<option value="">Todas las plataformas</option>';
            
            infoData.distribucion_plataformas.forEach(plat => {
                const option = document.createElement('option');
                option.value = plat.plataforma;
                option.textContent = `${plat.plataforma} (${plat.cantidad})`;
                plataformaSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error al cargar datos iniciales:', error);
        alert('Error al cargar datos iniciales. Por favor, verifica que la API esté funcionando correctamente.');
    }
}

// Crear gráfico de distribución de plataformas
function createPlatformChart(distribucion) {
    const ctx = document.getElementById('platform-chart').getContext('2d');
    
    const labels = distribucion.map(item => item.plataforma);
    const data = distribucion.map(item => item.cantidad);
    const colors = [
        '#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545',
        '#fd7e14', '#ffc107', '#198754', '#20c997', '#0dcaf0'
    ];
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

// Configurar eventos
function setupEventListeners() {
    // Búsqueda rápida
    document.getElementById('quick-search-btn').addEventListener('click', performQuickSearch);
    document.getElementById('quick-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performQuickSearch();
        }
    });
    
    // Búsqueda avanzada
    document.getElementById('advanced-search-btn').addEventListener('click', function() {
        document.getElementById('nav-explore').click();
    });
    
    // Aplicar filtros
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    
    // Generación de contenido
    document.getElementById('generar-contenido').addEventListener('click', generarContenido);
}

// Realizar búsqueda rápida
function performQuickSearch() {
    const searchText = document.getElementById('quick-search').value.trim();
    
    if (searchText) {
        // Navegar a la sección de exploración
        document.getElementById('nav-explore').click();
        
        // Establecer el texto en el campo de búsqueda
        document.getElementById('texto-search').value = searchText;
        
        // Limpiar otros filtros
        document.getElementById('tema-filter').value = '';
        document.getElementById('plataforma-filter').value = '';
        document.getElementById('fecha-inicio').value = '';
        document.getElementById('fecha-fin').value = '';
        
        // Aplicar filtros
        applyFilters();
    }
}

// Aplicar filtros de búsqueda
async function applyFilters() {
    const tema = document.getElementById('tema-filter').value;
    const plataforma = document.getElementById('plataforma-filter').value;
    const fechaInicio = document.getElementById('fecha-inicio').value;
    const fechaFin = document.getElementById('fecha-fin').value;
    const texto = document.getElementById('texto-search').value.trim();
    
    // Construir URL con parámetros
    let url = `${API_BASE_URL}/api/contenido?`;
    const params = [];
    
    if (tema) params.push(`tema=${tema}`);
    if (plataforma) params.push(`plataforma=${plataforma}`);
    if (fechaInicio) params.push(`fecha_inicio=${fechaInicio}`);
    if (fechaFin) params.push(`fecha_fin=${fechaFin}`);
    if (texto) params.push(`texto=${encodeURIComponent(texto)}`);
    
    // Añadir límite
    params.push(`limite=100`);
    
    url += params.join('&');
    
    try {
        // Mostrar indicador de carga
        document.getElementById('results-container').innerHTML = '<p class="text-center">Cargando resultados...</p>';
        
        // Realizar petición
        const response = await fetch(url);
        const data = await response.json();
        
        // Guardar resultados actuales
        currentResults = data;
        currentPage = 1;
        
        // Mostrar resultados
        displayResults(data);
        
    } catch (error) {
        console.error('Error al aplicar filtros:', error);
        document.getElementById('results-container').innerHTML = '<p class="text-center text-danger">Error al cargar resultados. Por favor, intenta de nuevo.</p>';
    }
}

// Mostrar resultados de búsqueda
function displayResults(results) {
    const container = document.getElementById('results-container');
    
    if (!results || results.length === 0) {
        container.innerHTML = '<p class="text-center">No se encontraron resultados para los filtros seleccionados.</p>';
        document.getElementById('pagination').innerHTML = '';
        return;
    }
    
    // Calcular páginas
    const totalPages = Math.ceil(results.length / resultsPerPage);
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = Math.min(startIndex + resultsPerPage, results.length);
    const currentPageResults = results.slice(startIndex, endIndex);
    
    // Generar HTML para resultados
    let html = `<p>Mostrando ${startIndex + 1}-${endIndex} de ${results.length} resultados</p>`;
    
    currentPageResults.forEach(result => {
        // Formatear fecha
        const fecha = new Date(result.fecha).toLocaleDateString();
        
        // Generar badges para temas
        let temasBadges = '';
        if (result.temas && result.temas.length > 0) {
            result.temas.forEach(tema => {
                temasBadges += `<span class="badge bg-secondary">${tema.nombre}</span> `;
            });
        }
        
        html += `
            <div class="result-item">
                <div class="d-flex justify-content-between">
                    <span class="date">${fecha}</span>
                    <span class="platform">${result.plataforma}</span>
                </div>
                <div class="content">${result.texto}</div>
                <div class="topics">${temasBadges}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Generar paginación
    generatePagination(totalPages);
}

// Generar controles de paginación
function generatePagination(totalPages) {
    const paginationContainer = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination">';
    
    // Botón anterior
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>
        </li>
    `;
    
    // Páginas
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Botón siguiente
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}">Siguiente</a>
        </li>
    `;
    
    html += '</ul></nav>';
    
    paginationContainer.innerHTML = html;
    
    // Añadir eventos a los enlaces de paginación
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const page = parseInt(this.getAttribute('data-page'));
            
            if (page >= 1 && page <= totalPages) {
                currentPage = page;
                displayResults(currentResults);
            }
        });
    });
}

// Generar material para nuevo contenido
async function generarContenido() {
    const tema = document.getElementById('generar-tema').value;
    const tipo = document.getElementById('generar-tipo').value;
    const longitud = document.getElementById('generar-longitud').value;
    
    if (!tema) {
        alert('Por favor, selecciona un tema para generar contenido.');
        return;
    }
    
    try {
        // Mostrar indicador de carga
        document.getElementById('generated-content-container').innerHTML = '<p class="text-center">Generando material...</p>';
        
        // Realizar petición
        const response = await fetch(`${API_BASE_URL}/api/generar?tema=${tema}&tipo=${tipo}&longitud=${longitud}`);
        const data = await response.json();
        
        if (!data.material || data.material.length === 0) {
            document.getElementById('generated-content-container').innerHTML = '<p class="text-center">No se encontró suficiente material para generar contenido sobre este tema.</p>';
            return;
        }
        
        // Generar HTML para el material
        let html = `<h4>Material para ${data.tipo} sobre "${data.tema}"</h4>`;
        
        // Estructura sugerida
        html += '<div class="generated-structure mb-4">';
        html += '<h5>Estructura Sugerida</h5>';
        
        if (data.estructura_sugerida) {
            if (data.estructura_sugerida.titulo) {
                html += `<p><strong>Título:</strong> ${data.estructura_sugerida.titulo}</p>`;
            }
            
            if (data.estructura_sugerida.introduccion) {
                html += `<p><strong>Introducción:</strong> ${data.estructura_sugerida.introduccion}</p>`;
            }
            
            if (data.estructura_sugerida.puntos_clave) {
                html += '<p><strong>Puntos Clave:</strong></p><ul>';
                data.estructura_sugerida.puntos_clave.forEach(punto => {
                    html += `<li>${punto}</li>`;
                });
                html += '</ul>';
            }
            
            if (data.estructura_sugerida.secciones) {
                html += '<p><strong>Secciones:</strong></p>';
                data.estructura_sugerida.secciones.forEach(seccion => {
                    html += `<p>- <strong>${seccion.titulo}:</strong> ${seccion.contenido}</p>`;
                });
            }
            
            if (data.estructura_sugerida.segmentos) {
                html += '<p><strong>Segmentos:</strong></p>';
                data.estructura_sugerida.segmentos.forEach(segmento => {
                    html += `<p>- <strong>${segmento.tiempo}:</strong> ${segmento.contenido}</p>`;
                });
            }
            
            if (data.estructura_sugerida.conclusion) {
                html += `<p><strong>Conclusión:</strong> ${data.estructura_sugerida.conclusion}</p>`;
            }
            
            if (data.estructura_sugerida.recursos) {
                html += '<p><strong>Recursos:</strong></p><ul>';
                data.estructura_sugerida.recursos.forEach(recurso => {
                    html += `<li>${recurso}</li>`;
                });
                html += '</ul>';
            }
        }
        html += '</div>';
        
        // Material de referencia
        html += '<h5>Material de Referencia</h5>';
        
        data.material.forEach((item, index) => {
            const fecha = new Date(item.fecha).toLocaleDateString();
            
            html += `
                <div class="generated-material">
                    <div class="d-flex justify-content-between mb-2">
                        <span class="date">${fecha}</span>
                        <span class="relevancia">Relevancia: ${Math.round(item.relevancia * 100)}%</span>
                    </div>
                    <div class="content">${item.texto}</div>
                </div>
            `;
        });
        
        document.getElementById('generated-content-container').innerHTML = html;
        
    } catch (error) {
        console.error('Error al generar contenido:', error);
        document.getElementById('generated-content-container').innerHTML = '<p class="text-center text-danger">Error al generar material. Por favor, intenta de nuevo.</p>';
    }
}
