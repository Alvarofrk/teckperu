/**
 * NAVBAR OPTIMIZADO TECKPERU
 * Versión simplificada y robusta
 */

(function () {
    'use strict';

    // Esperar a que el DOM esté completamente cargado
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Esperar un poco más para asegurar que Bootstrap esté cargado
        setTimeout(function () {
            setupNavbar();
        }, 100);
    }

    function setupNavbar() {
        try {
            // Configurar búsqueda
            setupSearch();

            // Configurar dropdown del avatar
            setupAvatarDropdown();

            // AJUSTE: Configurar dinámicamente el padding del contenido
            adjustContentPadding();

            // Verificar que Bootstrap esté disponible
            if (typeof bootstrap !== 'undefined') {
                console.log('Bootstrap detectado, inicializando dropdowns...');
                initializeBootstrapDropdowns();
            } else {
                console.warn('Bootstrap no detectado, esperando...');
                setTimeout(setupNavbar, 100);
            }

            console.log('Navbar optimizado inicializado correctamente');
        } catch (error) {
            console.error('Error al inicializar navbar:', error);
        }
    }

    function setupSearch() {
        const searchInput = document.getElementById('primary-search');
        const topNavbar = document.getElementById('top-navbar');
        const sideNav = document.getElementById('side-nav');
        const mainContent = document.getElementById('main-content');

        if (!searchInput || !topNavbar) return;

        searchInput.addEventListener('focus', function () {
            if (topNavbar) topNavbar.classList.add('dim');
            if (sideNav) sideNav.style.pointerEvents = 'none';
            if (mainContent) mainContent.style.pointerEvents = 'none';
        });

        searchInput.addEventListener('blur', function () {
            setTimeout(function () {
                if (topNavbar) topNavbar.classList.remove('dim');
                if (sideNav) sideNav.style.pointerEvents = 'auto';
                if (mainContent) mainContent.style.pointerEvents = 'auto';
            }, 200);
        });
    }

    function setupAvatarDropdown() {
        const dropdown = document.querySelector('#top-navbar .nav-wrapper .dropdown');
        const progressCard = document.getElementById('progress-card');

        if (!dropdown) {
            console.warn('Dropdown del avatar no encontrado');
            return;
        }

        // Configuración básica del dropdown
        const dropdownMenu = dropdown.querySelector('.dropdown-menu');
        const avatar = dropdown.querySelector('.avatar');

        if (dropdownMenu) {
            // Prevenir cierre accidental del dropdown
            dropdownMenu.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }

        // Prevenir que el avatar cierre el dropdown al hacer clic
        if (avatar) {
            avatar.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }

        // Función de respaldo para toggle manual del dropdown
        function toggleDropdown() {
            const isOpen = dropdown.classList.contains('show');

            if (isOpen) {
                dropdown.classList.remove('show');
                if (dropdownMenu) {
                    dropdownMenu.classList.remove('show');
                }
            } else {
                dropdown.classList.add('show');
                if (dropdownMenu) {
                    dropdownMenu.classList.add('show');
                }
            }
        }

        // Agregar evento de clic al avatar como respaldo
        if (avatar) {
            avatar.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                // Intentar usar Bootstrap primero
                if (typeof bootstrap !== 'undefined') {
                    const bsDropdown = bootstrap.Dropdown.getInstance(dropdown);
                    if (bsDropdown) {
                        bsDropdown.toggle();
                    } else {
                        toggleDropdown();
                    }
                } else {
                    toggleDropdown();
                }
            });
        }

        // Manejar conflicto con #progress-card si existe
        if (progressCard) {
            dropdown.addEventListener('show.bs.dropdown', function () {
                progressCard.style.display = 'none';
            });

            dropdown.addEventListener('hide.bs.dropdown', function () {
                setTimeout(function () {
                    progressCard.style.display = '';
                }, 300);
            });
        }

        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', function (e) {
            const toggleBtn = document.querySelector('.toggle-btn');

            // Ignorar clics en el botón de la hamburguesa para no interferir
            if (toggleBtn && toggleBtn.contains(e.target)) {
                return;
            }

            const isOpen = dropdown.classList.contains('show');
            if (isOpen && !dropdown.contains(e.target)) {
                // Intentar usar Bootstrap primero
                if (typeof bootstrap !== 'undefined') {
                    const bsDropdown = bootstrap.Dropdown.getInstance(dropdown);
                    if (bsDropdown) {
                        bsDropdown.hide();
                    } else {
                        dropdown.classList.remove('show');
                        if (dropdownMenu) {
                            dropdownMenu.classList.remove('show');
                        }
                    }
                } else {
                    dropdown.classList.remove('show');
                    if (dropdownMenu) {
                        dropdownMenu.classList.remove('show');
                    }
                }
            }
        });

        console.log('Dropdown del avatar configurado correctamente');
    }

    /**
     * Ajusta el padding-top del contenido principal para evitar
     * que sea solapado por el navbar fijo.
     */
    function adjustContentPadding() {
        const navbar = document.getElementById('top-navbar');
        const mainContent = document.getElementById('main-content');

        if (!navbar) {
            console.error('No se encontró el navbar (#top-navbar).');
            return;
        }

        const setPadding = () => {
            const navbarHeight = navbar.offsetHeight;
            if (mainContent) {
                mainContent.style.paddingTop = `${navbarHeight - 24}px`;
            }
        };

        // Usar ResizeObserver para detectar cambios de altura en el navbar
        const observer = new ResizeObserver(setPadding);
        observer.observe(navbar);

        // Llamada inicial
        setPadding();
    }

    function initializeBootstrapDropdowns() {
        // Inicializar todos los dropdowns de Bootstrap
        const dropdownElementList = document.querySelectorAll('.dropdown-toggle');
        dropdownElementList.forEach(function (dropdownToggleEl) {
            new bootstrap.Dropdown(dropdownToggleEl);
        });

        // También inicializar dropdowns que usan data-bs-toggle
        const dropdownsWithDataBs = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdownsWithDataBs.forEach(function (dropdownEl) {
            new bootstrap.Dropdown(dropdownEl);
        });

        console.log('Dropdowns de Bootstrap inicializados');
    }

    // Exponer función toggleSidebar globalmente para compatibilidad
    window.toggleSidebar = toggleSidebar;

    /**
     * Solución para la franja blanca en el sidebar.
     * Inicia el scroll del sidebar 17px más abajo y evita que vuelva a 0.
     */
    const sideNav = document.getElementById('side-nav');
    if (sideNav) {
        // Iniciar el scroll 17px hacia abajo al cargar
        sideNav.scrollTop = 17;

        // Añadir un listener para mantener el scroll alejado del borde superior
        sideNav.addEventListener('scroll', () => {
            if (sideNav.scrollTop < 17) {
                sideNav.scrollTop = 17;
            }
        });
    }

    // Inicializar todas las funcionalidades del navbar
    init();
})(); 