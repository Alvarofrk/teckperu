"use strict";

/**
 * MAIN.JS - TECKPERU
 * Funcionalidad simplificada para sidebar y navbar
 * 
 * Copyright (c) 2025 Alvaro Franco Cerna Ramos
 * Propiedad Intelectual - Plataforma Educativa Seguridad TECK Perú
 * Desarrollado exclusivamente para TECK Perú a través de G.P.D. CONSULTORES S.A.C.
 * Todos los derechos reservados.
 * 
 * Este archivo contiene funcionalidades únicas de navegación y prevención
 * de bloqueos en páginas de examen. Prohibida su reproducción o modificación
 * sin autorización expresa del desarrollador.
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
  checkMobile();
  // Ya no se manipula sidebarOpen ni se llama a toggleSidebar automáticamente
}

// Función específica para limpiar estados problemáticos en páginas de examen
function cleanupExamPageState() {
  try {
    console.log('Limpiando estado de página de examen...');

    // Remover clases problemáticas del navbar
    const topNavbar = document.getElementById('top-navbar');
    if (topNavbar) {
      topNavbar.classList.remove('dim');
      topNavbar.style.pointerEvents = 'auto';
      topNavbar.style.opacity = '1';
    }

    // Restaurar pointer-events en elementos principales
    const sideNav = document.getElementById('side-nav');
    const mainContent = document.getElementById('main-content');

    if (sideNav) {
      sideNav.style.pointerEvents = 'auto';
      sideNav.style.zIndex = '999';
    }

    if (mainContent) {
      mainContent.style.pointerEvents = 'auto';
      mainContent.style.zIndex = '1';
    }

    // Asegurar que el formulario de examen sea interactivo
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
      quizForm.style.pointerEvents = 'auto';
      quizForm.style.zIndex = '10';
      quizForm.style.position = 'relative';

      // Asegurar que todos los elementos del formulario sean interactivos
      const formElements = quizForm.querySelectorAll('*');
      formElements.forEach(element => {
        element.style.pointerEvents = 'auto';
      });
    }

    // Asegurar que el botón de envío funcione
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
      submitBtn.style.pointerEvents = 'auto';
      submitBtn.style.cursor = 'pointer';
      submitBtn.style.zIndex = '11';
    }

    // Asegurar que los modales de examen tengan prioridad
    const instructionModal = document.getElementById('instractionModal');
    if (instructionModal) {
      instructionModal.style.zIndex = '1050';
    }

    console.log('Estado de página de examen limpiado correctamente');

  } catch (error) {
    console.error('Error al limpiar estado de página de examen:', error);
  }
}

// Función para verificar si estamos en una página de examen
function isExamPage() {
  return document.getElementById('quiz-form') !== null ||
    document.querySelector('.quiz-wrapper') !== null ||
    document.querySelector('[data-exam-page="true"]') !== null ||
    window.location.pathname.includes('/quiz/') ||
    window.location.pathname.includes('/exam/') ||
    document.title.includes('Examen') ||
    document.title.includes('Quiz');
}

// Función para prevenir que se agregue la clase dim en páginas de examen
function preventDimInExamPages() {
  if (isExamPage()) {
    // Remover clase dim si existe
    const topNavbar = document.getElementById('top-navbar');
    if (topNavbar) {
      topNavbar.classList.remove('dim');
    }

    // Asegurar que no se pueda agregar la clase dim
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const target = mutation.target;
          if (target.id === 'top-navbar' && target.classList.contains('dim')) {
            target.classList.remove('dim');
            console.log('Clase dim removida automáticamente en página de examen');
          }
        }
      });
    });

    if (topNavbar) {
      observer.observe(topNavbar, { attributes: true });
    }

    // Deshabilitar eventos de foco en el campo de búsqueda
    const searchInput = document.getElementById('primary-search');
    if (searchInput) {
      searchInput.removeEventListener('focus', function () {
        $("#top-navbar").addClass("dim");
      });
      searchInput.removeEventListener('blur', function () {
        $("#top-navbar").removeClass("dim");
      });
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
  console.log('DOM cargado, inicializando...');

  // Verificar estado inicial
  checkMobile();

  // Eliminar lógica automática de apertura/cierre del sidebar en móvil/desktop
  // El sidebar solo responde al botón toggleSidebar()

  // Si estamos en una página de examen, aplicar protecciones especiales
  if (isExamPage()) {
    console.log('Página de examen detectada, aplicando protecciones especiales...');
    preventDimInExamPages();
    cleanupExamPageState();
    setTimeout(function () {
      preventDimInExamPages();
      cleanupExamPageState();
    }, 100);
    setTimeout(function () {
      preventDimInExamPages();
      cleanupExamPageState();
    }, 500);
    setInterval(function () {
      if (isExamPage()) {
        preventDimInExamPages();
      }
    }, 1000);
  }

  // Escuchar cambios de tamaño de ventana
  window.addEventListener('resize', adjustLayout);

  // Configurar scroll de tablas
  setupTableScroll();

  console.log('Inicialización completada');
});

// Hacer la función disponible globalmente
window.toggleSidebar = toggleSidebar;
window.cleanupExamPageState = cleanupExamPageState;

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
  // Solo aplicar estos eventos si NO estamos en una página de examen
  if (!isExamPage()) {
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
  } else {
    // En páginas de examen, asegurar que el campo de búsqueda no cause problemas
    $("#primary-search").off('focus focusout');
    $("#top-navbar").removeClass("dim");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  }
});

// Función para configurar scroll de tablas
function setupTableScroll() {
  const tables = document.querySelectorAll('.table-responsive');

  tables.forEach(table => {
    function checkScroll() {
      const scrollLeft = table.scrollLeft;
      const scrollWidth = table.scrollWidth;
      const clientWidth = table.clientWidth;

      // Agregar/remover clases para indicadores de scroll
      if (scrollLeft > 0) {
        table.classList.add('has-scroll-left');
      } else {
        table.classList.remove('has-scroll-left');
      }

      if (scrollLeft < scrollWidth - clientWidth - 1) {
        table.classList.add('has-scroll-right');
      } else {
        table.classList.remove('has-scroll-right');
      }
    }

    table.addEventListener('scroll', checkScroll);
    checkScroll(); // Verificar estado inicial
  });
}
