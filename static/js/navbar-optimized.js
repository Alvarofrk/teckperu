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
            adjustMainContentPadding();

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

        if (!dropdown) return;

        // Prevenir cierre accidental del dropdown
        const dropdownMenu = dropdown.querySelector('.dropdown-menu');
        if (dropdownMenu) {
            dropdownMenu.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }

        // SOLUCIÓN QUE FUNCIONABA: Crear portal para el dropdown original
        setupDropdownPortal(dropdown, dropdownMenu);

        // Manejar conflicto con #progress-card
        if (progressCard) {
            // Observar cambios en el dropdown usando MutationObserver
            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const isOpen = dropdown.classList.contains('show');
                        handleProgressCardVisibility(isOpen, progressCard);
                    }
                });
            });

            observer.observe(dropdown, {
                attributes: true,
                attributeFilter: ['class']
            });

            // También escuchar eventos de Bootstrap
            dropdown.addEventListener('show.bs.dropdown', function () {
                handleProgressCardVisibility(true, progressCard);
            });

            dropdown.addEventListener('hide.bs.dropdown', function () {
                setTimeout(function () {
                    handleProgressCardVisibility(false, progressCard);
                }, 300);
            });
        }

        // Prevenir que el avatar cierre el dropdown al hacer clic
        const avatar = dropdown.querySelector('.avatar');
        if (avatar) {
            avatar.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }
    }

    /**
     * SOLUCIÓN QUE FUNCIONABA: Crear un portal para el dropdown
     */
    function setupDropdownPortal(dropdown, dropdownMenu) {
        if (!dropdown || !dropdownMenu) return;

        // Crear un contenedor para el dropdown en el body
        let portalContainer = document.getElementById('dropdown-portal');
        if (!portalContainer) {
            portalContainer = document.createElement('div');
            portalContainer.id = 'dropdown-portal';
            portalContainer.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 999999;
            `;
            document.body.appendChild(portalContainer);
        }

        // Clonar el dropdown menu
        const clonedMenu = dropdownMenu.cloneNode(true);
        clonedMenu.id = 'dropdown-menu-portal';

        // Añadir una clase para aplicar estilos desde el CSS
        clonedMenu.classList.add('dropdown-menu-portal-styled');

        portalContainer.appendChild(clonedMenu);

        // Escuchar eventos del dropdown original
        dropdown.addEventListener('show.bs.dropdown', function () {
            console.log('🚀 Mostrando dropdown en portal...');
            clonedMenu.style.display = 'block';

            // Ocultar el dropdown original para evitar el "flicker"
            if (dropdownMenu) {
                dropdownMenu.style.setProperty('opacity', '0', 'important');
                dropdownMenu.style.setProperty('visibility', 'hidden', 'important');
                dropdownMenu.style.setProperty('pointer-events', 'none', 'important');
            }

            // Ocultar todos los elementos que puedan interferir
            hideInterferingElements();
        });

        dropdown.addEventListener('hide.bs.dropdown', function () {
            console.log('🔒 Ocultando dropdown del portal...');
            clonedMenu.style.display = 'none';

            // Restaurar los estilos del dropdown original
            if (dropdownMenu) {
                dropdownMenu.style.removeProperty('opacity');
                dropdownMenu.style.removeProperty('visibility');
                dropdownMenu.style.removeProperty('pointer-events');
            }
        });

        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', function (e) {
            const toggleBtn = document.querySelector('.toggle-btn');

            // Ignorar clics en el botón de la hamburguesa para no interferir
            if (toggleBtn && toggleBtn.contains(e.target)) {
                return;
            }

            const isOpen = dropdown.classList.contains('show');
            if (isOpen && !dropdown.contains(e.target) && !clonedMenu.contains(e.target)) {
                const bsDropdown = bootstrap.Dropdown.getInstance(dropdown);
                if (bsDropdown) {
                    bsDropdown.hide();
                }
            }
        });
    }

    /**
     * Ocultar elementos que puedan interferir
     */
    function hideInterferingElements() {
        // Ocultar #progress-card
        const progressCard = document.getElementById('progress-card');
        if (progressCard) {
            progressCard.style.display = 'none';
            progressCard.style.visibility = 'hidden';
            progressCard.style.opacity = '0';
            progressCard.style.zIndex = '-1';
        }

        // Ocultar cualquier modal
        const modals = document.querySelectorAll('.modal, .modal-backdrop, [class*="overlay"], [class*="modal"]');
        modals.forEach(function (modal) {
            if (modal.id !== 'dropdown-portal' && !modal.id.includes('dropdown')) {
                modal.style.display = 'none';
                modal.style.visibility = 'hidden';
                modal.style.opacity = '0';
                modal.style.zIndex = '-1';
            }
        });

        // Ocultar elementos con z-index alto
        const allElements = document.querySelectorAll('*');
        allElements.forEach(function (element) {
            const style = window.getComputedStyle(element);
            const zIndex = parseInt(style.zIndex);

            if (zIndex > 1000 && zIndex !== 999999 &&
                element.id !== 'dropdown-portal' &&
                !element.id.includes('dropdown')) {

                element.style.zIndex = '1';
            }
        });
    }

    function handleProgressCardVisibility(isOpen, progressCard) {
        if (!progressCard) return;

        if (isOpen) {
            // Ocultar #progress-card cuando dropdown está abierto
            progressCard.style.display = 'none';
            progressCard.style.visibility = 'hidden';
            progressCard.style.opacity = '0';
            progressCard.style.zIndex = '-1';
        } else {
            // Restaurar #progress-card cuando dropdown se cierra
            setTimeout(function () {
                progressCard.style.display = '';
                progressCard.style.visibility = '';
                progressCard.style.opacity = '';
                progressCard.style.zIndex = '';
            }, 300);
        }
    }

    /**
     * Ajusta el padding-top del contenido principal para evitar
     * que sea solapado por el navbar fijo.
     */
    function adjustMainContentPadding() {
        const navbar = document.getElementById('top-navbar');
        const mainContent = document.getElementById('main');

        if (!navbar || !mainContent) {
            console.error('No se encontró el navbar o el contenido principal para ajustar el padding.');
            return;
        }

        // Usar ResizeObserver para detectar cambios de altura en el navbar
        const observer = new ResizeObserver(entries => {
            for (let entry of entries) {
                const navbarHeight = entry.target.offsetHeight;
                console.log(`Ajustando padding-top de #main a: ${navbarHeight}px`);
                mainContent.style.paddingTop = `${navbarHeight}px`;
            }
        });

        // Empezar a observar el navbar
        observer.observe(navbar);
    }

    // Exponer función toggleSidebar globalmente para compatibilidad
    window.toggleSidebar = toggleSidebar;

    // Inicializar
    init();

})(); 