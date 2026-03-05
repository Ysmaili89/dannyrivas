// =========================================
// MAIN.JS - VERSIÓN CORREGIDA PARA MÓVIL
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Main.js cargado correctamente');
    
    initThemeToggle();
    initMobileMenu(); // ESTE ES EL IMPORTANTE
    initFlashMessages();
    initSmoothScroll();
    initHeaderScroll();
    initNewsletterForm();
});

// ===== MENÚ HAMBURGUESA (CORREGIDO) =====
function initMobileMenu() {
    const menuToggle = document.getElementById('mobileMenuToggle');
    const mainMenu = document.getElementById('mainMenu');
    
    if (!menuToggle || !mainMenu) {
        console.warn('⚠️ Menú móvil: elementos no encontrados');
        return;
    }
    
    console.log('✅ Menú móvil inicializado');
    
    // Remover estilos inline que puedan estar causando problemas
    mainMenu.style.display = '';
    
    menuToggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const isExpanded = this.getAttribute('aria-expanded') === 'true';
        const newState = !isExpanded;
        
        console.log('Menú click, abriendo:', newState);
        
        // Toggle clases
        mainMenu.classList.toggle('show', newState);
        this.setAttribute('aria-expanded', newState);
        
        // Cambiar icono
        const icon = this.querySelector('i');
        if (icon) {
            icon.className = newState ? 'fas fa-times' : 'fas fa-bars';
        }
        
        // Prevenir scroll cuando el menú está abierto
        document.body.style.overflow = newState ? 'hidden' : '';
    });
    
    // Cerrar al hacer click en un enlace
    mainMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                mainMenu.classList.remove('show');
                menuToggle.setAttribute('aria-expanded', 'false');
                menuToggle.querySelector('i').className = 'fas fa-bars';
                document.body.style.overflow = '';
            }
        });
    });
    
    // Cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && 
            mainMenu.classList.contains('show') && 
            !mainMenu.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            
            mainMenu.classList.remove('show');
            menuToggle.setAttribute('aria-expanded', 'false');
            menuToggle.querySelector('i').className = 'fas fa-bars';
            document.body.style.overflow = '';
        }
    });
    
    // Resetear en resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            mainMenu.classList.remove('show');
            mainMenu.style.display = '';
            document.body.style.overflow = '';
        }
    });
}

// ===== TEMA OSCURO/CLARO =====
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    const icon = themeToggle.querySelector('i');
    
    try {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
        }
    } catch (e) {
        console.warn('localStorage no disponible:', e);
    }
    
    themeToggle.addEventListener('click', function() {
        const isDark = document.body.classList.contains('dark-mode');
        
        if (isDark) {
            document.body.classList.remove('dark-mode');
            if (icon) {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
            try { localStorage.setItem('theme', 'light'); } catch(e) {}
        } else {
            document.body.classList.add('dark-mode');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
            try { localStorage.setItem('theme', 'dark'); } catch(e) {}
        }
    });
}

// ===== FLASH MESSAGES =====
function initFlashMessages() {
    document.querySelectorAll('.flash-message').forEach((msg, i) => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 5000 + (i * 500));
    });
}

// ===== SMOOTH SCROLL =====
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// ===== HEADER SCROLL =====
function initHeaderScroll() {
    const header = document.querySelector('header');
    if (!header || window.innerWidth <= 768) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > lastScroll && currentScroll > 100) {
            header.style.transform = 'translateY(-100%)';
        } else {
            header.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
}

// ===== NEWSLETTER FORM =====
function initNewsletterForm() {
    const form = document.querySelector('.newsletter-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        const email = this.querySelector('input[type="email"]');
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
            e.preventDefault();
            alert('❌ Por favor ingresa un email válido');
        }
    });
}