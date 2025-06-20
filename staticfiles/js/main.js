"use strict";

/**
 * MAIN.JS - TECKPERU
 * Funcionalidad principal responsive para sidebar y navbar
 */

(function () {
  'use strict';

  // Variables globales
  let sidebarState = {
    isOpen: true,
    isMobile: false,
    overlay: null
  };

  // Esperar a que el DOM esté completamente cargado
  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }

    // Esperar un poco más para asegurar que Bootstrap esté cargado
    setTimeout(function () {
      setupResponsiveLayout();
      setupSidebar();
      setupNavbar();
      setupOverlays();
      setupTouchOptimizations();
      console.log('TeckPeru responsive layout inicializado correctamente');
    }, 100);
  }

  /**
   * Configurar layout responsive
   */
  function setupResponsiveLayout() {
    const sideNav = document.getElementById('side-nav');
    const topNavbar = document.getElementById('top-navbar');
    const mainContent = document.getElementById('main-content');

    if (!sideNav || !topNavbar || !mainContent) return;

    // Detectar si es móvil
    function checkMobile() {
      const wasMobile = sidebarState.isMobile;
      sidebarState.isMobile = window.innerWidth <= 768;

      // Si cambió de desktop a móvil o viceversa
      if (wasMobile !== sidebarState.isMobile) {
        handleLayoutChange();
      }
    }

    // Manejar cambio de layout
    function handleLayoutChange() {
      if (sidebarState.isMobile) {
        // En móvil, sidebar cerrado por defecto
        closeSidebar();
        adjustNavbarForMobile();
      } else {
        // En desktop, sidebar abierto por defecto
        openSidebar();
        adjustNavbarForDesktop();
      }
    }

    // Ajustar navbar para móvil
    function adjustNavbarForMobile() {
      topNavbar.style.left = '0';
      topNavbar.style.width = '100vw';
      topNavbar.style.borderRadius = '0';
      mainContent.style.marginLeft = '0';
      mainContent.style.marginTop = '60px';
    }

    // Ajustar navbar para desktop
    function adjustNavbarForDesktop() {
      const sidebarWidth = getSidebarWidth();
      topNavbar.style.left = sidebarWidth + 'px';
      topNavbar.style.width = `calc(100vw - ${sidebarWidth}px)`;
      topNavbar.style.borderRadius = '0 0 12px 12px';
      mainContent.style.marginLeft = sidebarWidth + 'px';
      mainContent.style.marginTop = '80px';
    }

    // Obtener ancho del sidebar
    function getSidebarWidth() {
      if (sidebarState.isMobile) return 0;

      if (window.innerWidth <= 1024) return 260;
      return 280;
    }

    // Escuchar cambios de tamaño de ventana
    window.addEventListener('resize', function () {
      checkMobile();
    });

    // Verificación inicial
    checkMobile();
  }

  /**
   * Configurar sidebar
   */
  function setupSidebar() {
    const sideNav = document.getElementById('side-nav');
    if (!sideNav) return;

    // Botón de toggle en el sidebar (móvil)
    const sidebarToggleBtn = sideNav.querySelector('.desktop-hide .toggle-btn');
    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        closeSidebar();
      });
    }

    // Cerrar sidebar al hacer clic en enlaces (móvil)
    const sidebarLinks = sideNav.querySelectorAll('.nav-link');
    sidebarLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        if (sidebarState.isMobile) {
          setTimeout(closeSidebar, 300);
        }
      });
    });

    // Cerrar sidebar al hacer clic fuera (móvil)
    document.addEventListener('click', function (e) {
      if (sidebarState.isMobile && sidebarState.isOpen) {
        if (!sideNav.contains(e.target) && !e.target.closest('.toggle-btn')) {
          closeSidebar();
        }
      }
    });

    // Prevenir cierre accidental al hacer clic dentro del sidebar
    sideNav.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  /**
   * Configurar navbar
   */
  function setupNavbar() {
    const topNavbar = document.getElementById('top-navbar');
    if (!topNavbar) return;

    // Botón de toggle en el navbar - MEJORADO
    const navbarToggleBtn = topNavbar.querySelector('.toggle-btn');
    if (navbarToggleBtn) {
      // Remover event listeners existentes para evitar duplicados
      navbarToggleBtn.removeEventListener('click', handleToggleClick);
      navbarToggleBtn.addEventListener('click', handleToggleClick);

      // También agregar event listener para touch events
      navbarToggleBtn.addEventListener('touchstart', handleToggleClick, { passive: false });
    }

    // Optimizar búsqueda
    const searchInput = topNavbar.querySelector('#primary-search');
    if (searchInput) {
      searchInput.addEventListener('focus', function () {
        if (sidebarState.isMobile) {
          closeSidebar();
        }
      });
    }
  }

  /**
   * Manejador del clic del botón toggle - NUEVA FUNCIÓN
   */
  function handleToggleClick(e) {
    e.preventDefault();
    e.stopPropagation();

    console.log('Botón hamburguesa clickeado - Estado móvil:', sidebarState.isMobile);
    console.log('Sidebar abierto:', sidebarState.isOpen);

    toggleSidebar();
  }

  /**
   * Función principal de toggle del sidebar
   */
  function toggleSidebar() {
    console.log('Ejecutando toggleSidebar...');

    if (sidebarState.isOpen) {
      closeSidebar();
    } else {
      openSidebar();
    }
  }

  /**
   * Configurar overlays
   */
  function setupOverlays() {
    // Crear overlay para sidebar
    sidebarState.overlay = document.createElement('div');
    sidebarState.overlay.className = 'sidebar-overlay';
    sidebarState.overlay.addEventListener('click', closeSidebar);
    document.body.appendChild(sidebarState.overlay);

    // Crear overlay para navbar (si es necesario)
    const navbarOverlay = document.createElement('div');
    navbarOverlay.className = 'navbar-overlay';
    navbarOverlay.addEventListener('click', function () {
      // Cerrar dropdowns si están abiertos
      const dropdowns = document.querySelectorAll('.dropdown.show');
      dropdowns.forEach(function (dropdown) {
        dropdown.classList.remove('show');
      });
    });
    document.body.appendChild(navbarOverlay);
  }

  /**
   * Configurar optimizaciones para dispositivos táctiles
   */
  function setupTouchOptimizations() {
    // Mejorar scroll en dispositivos táctiles
    document.body.style.webkitOverflowScrolling = 'touch';

    // Prevenir zoom en inputs en iOS
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(function (input) {
      input.addEventListener('focus', function () {
        if (sidebarState.isMobile) {
          closeSidebar();
        }
      });
    });

    // Mejorar área de toque para botones
    const buttons = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
    buttons.forEach(function (button) {
      button.style.minHeight = '44px';
      button.style.display = 'flex';
      button.style.alignItems = 'center';
    });
  }

  /**
   * Abrir sidebar
   */
  function openSidebar() {
    const sideNav = document.getElementById('side-nav');
    const topNavbar = document.getElementById('top-navbar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = topNavbar.querySelector('.toggle-btn');

    if (!sideNav || !topNavbar || !mainContent) {
      console.error('Elementos necesarios no encontrados');
      return;
    }

    console.log('Abriendo sidebar...');
    sidebarState.isOpen = true;
    sideNav.classList.remove('toggle-active');

    // Agregar clase activa al botón
    if (toggleBtn) {
      toggleBtn.classList.add('active');
    }

    if (sidebarState.isMobile) {
      // En móvil, mostrar overlay
      if (sidebarState.overlay) {
        sidebarState.overlay.classList.add('active');
      }
      document.body.style.overflow = 'hidden';
    } else {
      // En desktop, ajustar layout
      const sidebarWidth = getSidebarWidth();
      topNavbar.style.left = sidebarWidth + 'px';
      topNavbar.style.width = `calc(100vw - ${sidebarWidth}px)`;
      mainContent.style.marginLeft = sidebarWidth + 'px';
    }

    // Animar entrada
    sideNav.style.transform = 'translateX(0)';
    sideNav.style.boxShadow = '8px 0 32px rgba(0, 0, 0, 0.15)';

    console.log('Sidebar abierto exitosamente');
  }

  /**
   * Cerrar sidebar
   */
  function closeSidebar() {
    const sideNav = document.getElementById('side-nav');
    const topNavbar = document.getElementById('top-navbar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn = topNavbar.querySelector('.toggle-btn');

    if (!sideNav || !topNavbar || !mainContent) {
      console.error('Elementos necesarios no encontrados');
      return;
    }

    console.log('Cerrando sidebar...');
    sidebarState.isOpen = false;
    sideNav.classList.add('toggle-active');

    // Remover clase activa del botón
    if (toggleBtn) {
      toggleBtn.classList.remove('active');
    }

    if (sidebarState.isMobile) {
      // En móvil, ocultar overlay
      if (sidebarState.overlay) {
        sidebarState.overlay.classList.remove('active');
      }
      document.body.style.overflow = '';
    } else {
      // En desktop, ajustar layout
      topNavbar.style.left = '0';
      topNavbar.style.width = '100vw';
      mainContent.style.marginLeft = '0';
    }

    // Animar salida
    sideNav.style.transform = 'translateX(-100%)';
    sideNav.style.boxShadow = 'none';

    console.log('Sidebar cerrado exitosamente');
  }

  /**
   * Obtener ancho del sidebar
   */
  function getSidebarWidth() {
    if (sidebarState.isMobile) return 0;

    if (window.innerWidth <= 1024) return 260;
    return 280;
  }

  /**
   * Ajustar padding del contenido principal
   */
  function adjustContentPadding() {
    const mainContent = document.getElementById('main-content');
    if (!mainContent) return;

    const setPadding = () => {
      const isMobile = window.innerWidth <= 768;
      const sidebarWidth = isMobile ? 0 : (window.innerWidth <= 1024 ? 260 : 280);
      const navbarHeight = isMobile ? 60 : 80;

      mainContent.style.marginLeft = sidebarWidth + 'px';
      mainContent.style.marginTop = navbarHeight + 'px';
      mainContent.style.transition = 'margin 0.3s ease';
    };

    setPadding();
    window.addEventListener('resize', setPadding);
  }

  // Inicializar cuando el DOM esté listo
  init();

  // Exportar funciones para uso global
  window.TeckPeru = {
    toggleSidebar: toggleSidebar,
    openSidebar: openSidebar,
    closeSidebar: closeSidebar,
    isMobile: () => sidebarState.isMobile,
    isSidebarOpen: () => sidebarState.isOpen
  };

  // Hacer toggleSidebar disponible globalmente
  window.toggleSidebar = toggleSidebar;

})();

// #################################
// popup

var c = 0;
function pop() {
  if (c == 0) {
    document.getElementById("popup-box").style.display = "block";
    c = 1;
  } else {
    document.getElementById("popup-box").style.display = "none";
    c = 0;
  }
}

// const popupMessagesButtons = document.querySelectorAll('popup-btn-messages')

// popupMessagesButtons.forEach(button, () => {
//     button.addEventListener('click', () => {
//         document.getElementById('popup-box-messages').style.display = 'none';
//     })
// })

// const popupMessagesButtom = document.getElementById('popup-btn-messages')
// popupMessagesButtom.addEventListener('click', () => {
//     document.getElementById('popup-box-messages').style.display = 'none';
// })
// ##################################

// Example starter JavaScript for disabling form submissions if there are invalid fields
// Fetch all the forms we want to apply custom Bootstrap validation styles to
var forms = document.getElementsByClassName("needs-validation");

// Loop over them and prevent submission
Array.prototype.filter.call(forms, function (form) {
  form.addEventListener(
    "submit",
    function (event) {
      if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false
  );
});
// ##################################

// extend and collapse
function showCourses(btn) {
  var btn = $(btn);

  if (collapsed) {
    btn.html('Collapse <i class="fas fa-angle-up"></i>');
    $(".hide").css("max-height", "unset");
    $(".white-shadow").css({ background: "unset", "z-index": "0" });
  } else {
    btn.html('Expand <i class="fas fa-angle-down"></i>');
    $(".hide").css("max-height", "150");
    $(".white-shadow").css({
      background: "linear-gradient(transparent 50%, rgba(255,255,255,.8) 80%)",
      "z-index": "2",
    });
  }
  collapsed = !collapsed;
}

$(document).ready(function () {
  $("#primary-search").focus(function () {
    $("#top-navbar").attr("class", "dim");
    $("#side-nav").css("pointer-events", "none");
    $("#main-content").css("pointer-events", "none");
  });
  $("#primary-search").focusout(function () {
    $("#top-navbar").removeAttr("class");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  });
});
