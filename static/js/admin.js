// =========================================
// PANEL ADMIN - FUNCIONALIDADES GENERALES
// =========================================

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS cargado correctamente');
    
    // Inicializar menú móvil (NUEVO - CORREGIDO)
    initMobileMenu();
    
    // Inicializar tooltips
    initTooltips();
    
    // Selectores mejorados
    initSelects();
    
    // Validación de formularios
    initFormValidation();
    
    // Cargar notificaciones
    loadNotifications();
    
    // Inicializar búsqueda global
    initGlobalSearch();
    
    // Inicializar modales
    initModals();
    
    // Inicializar botones de exportación
    initExportButtons();
    
    // Inicializar previews de imagen
    initImagePreviews();
    
    // Inicializar filtros de URL
    initUrlFilters();
});

// =========================================
// MENÚ HAMBURGUESA PARA ADMIN (NUEVO)
// =========================================

function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('adminSidebar');
    
    if (!menuToggle || !sidebar) {
        console.warn('⚠️ Elementos del menú móvil no encontrados');
        return;
    }
    
    console.log('✅ Menú móvil de admin inicializado');
    
    // Remover estilos inline que puedan interferir
    sidebar.classList.remove('open');
    
    menuToggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Toggle clase 'open' en el sidebar
        sidebar.classList.toggle('open');
        
        // Cambiar icono (opcional)
        const icon = this.querySelector('i');
        if (icon) {
            if (sidebar.classList.contains('open')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
        
        console.log('Menú admin toggled:', sidebar.classList.contains('open') ? 'abierto' : 'cerrado');
    });
    
    // Cerrar menú al hacer click fuera (solo en móvil)
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && 
            sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            
            sidebar.classList.remove('open');
            const icon = menuToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
    
    // Cerrar menú al hacer click en un enlace (móvil)
    sidebar.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
                const icon = menuToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    });
    
    // Resetear en resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
            const icon = menuToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
}

// =========================================
// TOOLTIPS
// =========================================

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const target = e.target;
    const tooltipText = target.dataset.tooltip;
    
    // Crear elemento tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'admin-tooltip';
    tooltip.textContent = tooltipText;
    tooltip.setAttribute('role', 'tooltip');
    
    // Posicionar
    document.body.appendChild(tooltip);
    
    const rect = target.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    tooltip.style.top = rect.top - tooltipRect.height - 10 + window.scrollY + 'px';
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltipRect.width / 2) + 'px';
    
    // Mostrar con animación
    setTimeout(() => tooltip.classList.add('show'), 10);
    
    // Guardar referencia
    target._tooltip = tooltip;
}

function hideTooltip(e) {
    const target = e.target;
    
    if (target._tooltip) {
        target._tooltip.classList.remove('show');
        
        setTimeout(() => {
            if (target._tooltip && target._tooltip.parentNode) {
                target._tooltip.remove();
            }
            delete target._tooltip;
        }, 200);
    }
}

// =========================================
// SELECTORES MEJORADOS
// =========================================

function initSelects() {
    document.querySelectorAll('select.select-enhanced').forEach(select => {
        // Aquí puedes implementar un select personalizado si lo necesitas
        // Por ahora, solo agregamos una clase para estilos
        select.classList.add('enhanced');
    });
}

// =========================================
// VALIDACIÓN DE FORMULARIOS
// =========================================

function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', validateForm);
        
        // Validación en tiempo real
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                removeFieldError(this);
            });
        });
    });
}

function validateForm(e) {
    const form = e.target;
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    let firstError = null;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
            if (!firstError) firstError = field;
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        
        // Hacer scroll al primer error
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
        
        // Mostrar notificación de error
        showNotification('Por favor completa todos los campos requeridos', 'error');
    }
}

function validateField(field) {
    removeFieldError(field);
    
    let isValid = true;
    let errorMessage = '';
    
    if (field.required && !field.value.trim()) {
        isValid = false;
        errorMessage = 'Este campo es requerido';
    } else if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
        isValid = false;
        errorMessage = 'Email inválido';
    } else if (field.type === 'url' && field.value && !isValidUrl(field.value)) {
        isValid = false;
        errorMessage = 'URL inválida';
    } else if (field.minLength && field.value.length < field.minLength) {
        isValid = false;
        errorMessage = `Mínimo ${field.minLength} caracteres`;
    }
    
    if (!isValid) {
        field.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = errorMessage;
        
        field.parentNode.appendChild(errorDiv);
    } else {
        field.classList.remove('error');
    }
    
    return isValid;
}

function removeFieldError(field) {
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) existingError.remove();
}

function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// =========================================
// NOTIFICACIONES
// =========================================

function loadNotifications() {
    const badge = document.querySelector('.notification-badge .badge-count');
    if (!badge) return;
    
    fetch('/admin/notificaciones')
        .then(response => response.json())
        .then(data => {
            if (data.count > 0) {
                updateNotificationBadge(data.count);
            }
        })
        .catch(error => console.error('Error loading notifications:', error));
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge .badge-count');
    if (badge) {
        badge.textContent = count;
        badge.style.display = 'flex';
        
        if (count > 0) {
            badge.classList.add('has-notifications');
        }
    }
}

// =========================================
// BÚSQUEDA GLOBAL
// =========================================

function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;
    
    searchInput.addEventListener('keyup', debounce(function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 3) {
            hideSearchResults();
            return;
        }
        
        performSearch(query);
    }, 500));
}

function performSearch(query) {
    fetch(`/admin/buscar?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            showSearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            showNotification('Error al buscar', 'error');
        });
}

function showSearchResults(results) {
    let resultsContainer = document.getElementById('searchResults');
    
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'searchResults';
        resultsContainer.className = 'search-results';
        document.querySelector('.admin-topbar').appendChild(resultsContainer);
    }
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No se encontraron resultados</div>';
    } else {
        resultsContainer.innerHTML = results.map(item => `
            <a href="${item.url}" class="search-result-item">
                <i class="fas ${item.icon}"></i>
                <div>
                    <strong>${item.title}</strong>
                    <small>${item.subtitle || ''}</small>
                </div>
            </a>
        `).join('');
    }
    
    resultsContainer.classList.add('show');
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer) {
        resultsContainer.classList.remove('show');
    }
}

// =========================================
// MODALES
// =========================================

function initModals() {
    // Abrir modal
    document.querySelectorAll('[data-modal]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            openModal(modalId);
        });
    });
    
    // Cerrar con botón close
    document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) closeModal(modal.id);
        });
    });
    
    // Cerrar con overlay
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// =========================================
// EXPORTACIÓN DE DATOS
// =========================================

function initExportButtons() {
    document.querySelectorAll('[data-export]').forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.dataset.export;
            const format = this.dataset.format || 'csv';
            exportData(type, format);
        });
    });
}

function exportData(type, format = 'csv') {
    const url = `/admin/exportar/${type}?format=${format}`;
    
    showNotification('Generando exportación...', 'info');
    
    // Crear un enlace temporal para descargar
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.click();
}

// =========================================
// PREVIEW DE IMAGEN
// =========================================

function initImagePreviews() {
    document.querySelectorAll('[data-preview]').forEach(input => {
        input.addEventListener('change', function() {
            const previewId = this.dataset.preview;
            previewImage(this, previewId);
        });
    });
}

function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        
        // Validar tipo de archivo
        if (!file.type.startsWith('image/')) {
            showNotification('El archivo no es una imagen válida', 'error');
            input.value = '';
            return;
        }
        
        // Validar tamaño (5MB por defecto)
        const maxSize = parseInt(input.dataset.maxSize) || 5 * 1024 * 1024;
        if (file.size > maxSize) {
            showNotification(`La imagen no puede ser mayor a ${maxSize / (1024*1024)}MB`, 'error');
            input.value = '';
            return;
        }
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            
            // Si hay un contenedor de preview, mostrarlo
            const container = preview.closest('.preview-container');
            if (container) {
                container.classList.add('has-image');
            }
        };
        
        reader.readAsDataURL(file);
    }
}

// =========================================
// FILTROS DE URL
// =========================================

function initUrlFilters() {
    const filters = getUrlParams();
    
    // Aplicar filtros a selects y inputs
    Object.keys(filters).forEach(key => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input) {
            input.value = filters[key];
            
            // Disparar evento change
            const event = new Event('change', { bubbles: true });
            input.dispatchEvent(event);
        }
    });
}

function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    
    for (const [key, value] of params) {
        result[key] = value;
    }
    
    return result;
}

function updateUrlParams(params) {
    const url = new URL(window.location.href);
    
    Object.keys(params).forEach(key => {
        if (params[key] && params[key] !== '') {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    window.history.pushState({}, '', url);
}

// =========================================
// COPIAR AL PORTAPAPELES
// =========================================

function copyToClipboard(text, showNotification_ = true) {
    navigator.clipboard.writeText(text).then(() => {
        if (showNotification_) {
            showNotification('Copiado al portapapeles', 'success');
        }
    }).catch(() => {
        if (showNotification_) {
            showNotification('Error al copiar', 'error');
        }
    });
}

// =========================================
// NOTIFICACIONES TOAST
// =========================================

function showNotification(message, type = 'info') {
    // Eliminar toasts existentes del mismo tipo
    const existingToasts = document.querySelectorAll('.admin-toast');
    if (existingToasts.length > 3) {
        existingToasts[0].remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `admin-toast toast-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Mostrar con animación
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-cerrar
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// =========================================
// CONFIRMAR ACCIÓN
// =========================================

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// =========================================
// FORMATEAR FECHA
// =========================================

function formatDate(date, includeTime = true) {
    const d = new Date(date);
    
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return d.toLocaleDateString('es-ES', options);
}

// =========================================
// SCROLL SUAVE
// =========================================

function smoothScroll(element) {
    if (!element) return;
    
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// =========================================
// DEBOUNCE HELPER
// =========================================

function debounce(func, wait) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// =========================================
// THROTTLE HELPER
// =========================================

function throttle(func, limit) {
    let inThrottle;
    
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// =========================================
// ESC KEY HANDLER
// =========================================

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        // Cerrar modales
        document.querySelectorAll('.modal.show').forEach(modal => {
            modal.classList.remove('show');
        });
        
        // Cerrar dropdowns
        document.querySelectorAll('.dropdown-menu[style*="display: block"]').forEach(menu => {
            menu.style.display = 'none';
        });
        
        // Cerrar resultados de búsqueda
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.classList.remove('show');
        }
    }
});

// =========================================
// CLICK OUTSIDE HANDLER
// =========================================

document.addEventListener('click', function(e) {
    // Cerrar dropdowns al hacer clic fuera
    if (!e.target.closest('.user-dropdown')) {
        document.querySelectorAll('.dropdown-menu[style*="display: block"]').forEach(menu => {
            menu.style.display = 'none';
        });
    }
    
    // Cerrar resultados de búsqueda al hacer clic fuera
    if (!e.target.closest('#globalSearch') && !e.target.closest('#searchResults')) {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.classList.remove('show');
        }
    }
});