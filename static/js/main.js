"use strict";

/**
 * MAIN.JS - TECKPERU
 * Funcionalidad simplificada para sidebar y navbar
 */

// Variables globales
let sidebarOpen = true;
let isMobile = false;

// Función para detectar si es móvil
function checkMobile() {
  isMobile = window.innerWidth <= 768;
  return isMobile;
}

// Función principal de toggle del sidebar
function toggleSidebar() {
  console.log('toggleSidebar ejecutado');

  const sideNav = document.getElementById('side-nav');
  const topNavbar = document.getElementById('top-navbar');
  const mainContent = document.getElementById('main');
  const toggleBtn = document.querySelector('.toggle-btn');

  if (!sideNav || !topNavbar || !mainContent) {
    console.error('Elementos necesarios no encontrados');
    return;
  }

  // Cambiar estado
  sidebarOpen = !sidebarOpen;

  // Aplicar clases CSS
  sideNav.classList.toggle('toggle-active');
  topNavbar.classList.toggle('toggle-active');
  mainContent.classList.toggle('toggle-active');

  // Aplicar estilos inline solo al navbar para asegurar que funcione
  if (sidebarOpen) {
    // Abrir sidebar
    console.log('Abriendo sidebar');

    if (isMobile) {
      // En móvil, mostrar overlay
      topNavbar.style.left = '0';
      topNavbar.style.width = '100vw';
    } else {
      // En desktop, ajustar layout del navbar
      const sidebarWidth = window.innerWidth <= 1024 ? 260 : 280;
      topNavbar.style.left = sidebarWidth + 'px';
      topNavbar.style.width = `calc(100vw - ${sidebarWidth}px)`;
    }

    // Activar botón
    if (toggleBtn) {
      toggleBtn.classList.add('active');
    }

  } else {
    // Cerrar sidebar
    console.log('Cerrando sidebar');

    // En todos los casos, expandir completamente el navbar
    topNavbar.style.left = '0';
    topNavbar.style.width = '100vw';

    // Desactivar botón
    if (toggleBtn) {
      toggleBtn.classList.remove('active');
    }
  }

  console.log('Estado del sidebar:', sidebarOpen ? 'abierto' : 'cerrado');
}

// Función para ajustar layout al cambiar tamaño de ventana
function adjustLayout() {
  const wasMobile = isMobile;
  checkMobile();

  // Si cambió de móvil a desktop o viceversa
  if (wasMobile !== isMobile) {
    if (isMobile) {
      // En móvil, cerrar sidebar por defecto
      if (sidebarOpen) {
        toggleSidebar();
      }
    } else {
      // En desktop, abrir sidebar por defecto
      if (!sidebarOpen) {
        toggleSidebar();
      }
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
  console.log('DOM cargado, inicializando...');

  // Verificar estado inicial
  checkMobile();

  // Ajustar layout inicial
  if (isMobile) {
    // En móvil, sidebar cerrado por defecto
    sidebarOpen = false;
    const sideNav = document.getElementById('side-nav');
    const topNavbar = document.getElementById('top-navbar');
    const mainContent = document.getElementById('main');

    if (sideNav && topNavbar && mainContent) {
      sideNav.classList.add('toggle-active');
      topNavbar.style.left = '0';
      topNavbar.style.width = '100vw';
    }
  }

  // Escuchar cambios de tamaño de ventana
  window.addEventListener('resize', adjustLayout);

  // Configurar scroll de tablas
  setupTableScroll();

  console.log('Inicialización completada');
});

// Hacer la función disponible globalmente
window.toggleSidebar = toggleSidebar;

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
    $("#top-navbar").addClass("dim");
    $("#side-nav").css("pointer-events", "none");
    $("#main-content").css("pointer-events", "none");
  });
  $("#primary-search").focusout(function () {
    $("#top-navbar").removeClass("dim");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  });
});

// Función para mejorar el scroll horizontal de tablas en móviles
function setupTableScroll() {
  const tableResponsives = document.querySelectorAll('.table-responsive');

  tableResponsives.forEach(function (container) {
    const table = container.querySelector('.table');
    if (!table) return;

    // Función para verificar si necesita scroll
    function checkScroll() {
      const needsScroll = table.scrollWidth > container.clientWidth;

      if (needsScroll) {
        container.classList.add('has-scroll');

        // Agregar indicador de scroll si no existe
        if (!container.querySelector('.scroll-indicator')) {
          const indicator = document.createElement('div');
          indicator.className = 'scroll-indicator';
          indicator.innerHTML = '<i class="fas fa-arrows-alt-h"></i>';
          indicator.style.cssText = `
            position: absolute;
            bottom: 5px;
            right: 5px;
            background: rgba(186, 96, 34, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            z-index: 100;
            pointer-events: none;
            opacity: 0.8;
            transition: opacity 0.3s ease;
          `;
          container.style.position = 'relative';
          container.appendChild(indicator);
        }
      } else {
        container.classList.remove('has-scroll');
        const indicator = container.querySelector('.scroll-indicator');
        if (indicator) {
          indicator.remove();
        }
      }
    }

    // Verificar al cargar
    checkScroll();

    // Verificar al cambiar tamaño de ventana
    window.addEventListener('resize', checkScroll);

    // Verificar al hacer scroll
    container.addEventListener('scroll', function () {
      const indicator = container.querySelector('.scroll-indicator');
      if (indicator) {
        indicator.style.opacity = '0.3';
        clearTimeout(indicator.fadeTimeout);
        indicator.fadeTimeout = setTimeout(function () {
          indicator.style.opacity = '0.8';
        }, 1000);
      }
    });
  });
}
