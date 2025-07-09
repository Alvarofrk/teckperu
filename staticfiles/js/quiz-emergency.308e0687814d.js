/**
 * SCRIPT DE EMERGENCIA PARA DESBLOQUEAR PÁGINAS DE EXAMEN
 * 
 * Este script se puede ejecutar manualmente desde la consola del navegador
 * cuando la pantalla del examen se bloquea, especialmente después del modal de instrucciones.
 * 
 * Uso: Copiar y pegar todo este código en la consola del navegador (F12)
 */

(function () {
    'use strict';

    console.log('🚨 EJECUTANDO SCRIPT DE EMERGENCIA PARA EXAMEN 🚨');

    // Función principal de desbloqueo
    function emergencyUnlock() {
        try {
            console.log('🔧 Iniciando proceso de desbloqueo...');

            // 1. ELIMINAR COMPLETAMENTE TODOS LOS MODALES Y BACKDROPS
            removeAllModalsAndBackdrops();

            // 2. Remover todas las clases dim
            const elementsWithDim = document.querySelectorAll('.dim');
            elementsWithDim.forEach(function (element) {
                element.classList.remove('dim');
                console.log('✅ Clase dim removida de:', element);
            });

            // 3. Limpiar navbar específicamente
            const topNavbar = document.getElementById('top-navbar');
            if (topNavbar) {
                topNavbar.classList.remove('dim');
                topNavbar.style.boxShadow = '0 4px 20px rgba(186, 96, 34, 0.3)';
                topNavbar.style.pointerEvents = 'auto';
                topNavbar.style.zIndex = '1001';
                topNavbar.style.opacity = '1';
                topNavbar.style.background = 'linear-gradient(135deg, #BA6022 0%, #A0521E 100%)';
                console.log('✅ Navbar limpiado');
            }

            // 4. Restaurar interactividad del sidebar
            const sideNav = document.getElementById('side-nav');
            if (sideNav) {
                sideNav.style.pointerEvents = 'auto';
                sideNav.style.zIndex = '1000';
                console.log('✅ Sidebar restaurado');
            }

            // 5. Restaurar interactividad del contenido principal
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.style.pointerEvents = 'auto';
                mainContent.style.zIndex = '1';
                console.log('✅ Contenido principal restaurado');
            }

            // 6. Asegurar que el formulario de examen funcione
            const quizForm = document.getElementById('quiz-form');
            if (quizForm) {
                quizForm.style.pointerEvents = 'auto';
                quizForm.style.zIndex = '1060';
                quizForm.style.position = 'relative';

                // Asegurar que todos los elementos del formulario sean interactivos
                const formElements = quizForm.querySelectorAll('*');
                formElements.forEach(function (element) {
                    element.style.pointerEvents = 'auto';
                });
                console.log('✅ Formulario de examen restaurado');
            }

            // 7. Asegurar que el botón de envío funcione
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.style.pointerEvents = 'auto';
                submitBtn.style.cursor = 'pointer';
                submitBtn.style.zIndex = '1070';
                submitBtn.style.position = 'relative';
                submitBtn.disabled = false;
                console.log('✅ Botón de envío restaurado');
            }

            // 8. Deshabilitar eventos problemáticos del campo de búsqueda
            const searchInput = document.getElementById('primary-search');
            if (searchInput) {
                // Remover todos los event listeners
                const newSearchInput = searchInput.cloneNode(true);
                searchInput.parentNode.replaceChild(newSearchInput, searchInput);

                // Agregar eventos seguros
                newSearchInput.addEventListener('focus', function (e) {
                    e.stopPropagation();
                    // NO hacer nada que pueda bloquear
                });

                newSearchInput.addEventListener('blur', function (e) {
                    e.stopPropagation();
                    // NO hacer nada que pueda bloquear
                });

                console.log('✅ Eventos del campo de búsqueda deshabilitados');
            }

            // 9. Marcar la página como página de examen
            document.body.setAttribute('data-exam-page', 'true');

            // 10. Aplicar estilos CSS de emergencia
            applyEmergencyStyles();

            // 11. Configurar protección continua
            setupContinuousProtection();

            console.log('🎉 ¡DESBLOQUEO COMPLETADO! La página debería estar completamente funcional ahora.');

            // Mostrar mensaje visual al usuario
            showSuccessMessage();

        } catch (error) {
            console.error('❌ Error durante el desbloqueo:', error);
            showErrorMessage();
        }
    }

    // Función para eliminar completamente todos los modales y backdrops
    function removeAllModalsAndBackdrops() {
        console.log('🗑️ Eliminando todos los modales y backdrops...');

        // 1. Cerrar TODOS los modales de Bootstrap
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const allModals = document.querySelectorAll('.modal');
            allModals.forEach(function (modal) {
                try {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) {
                        bsModal.hide();
                        console.log('✅ Modal de Bootstrap cerrado:', modal.id);
                    }
                } catch (e) {
                    console.log('⚠️ Error al cerrar modal de Bootstrap:', e);
                }
            });
        }

        // 2. Remover TODOS los modal-backdrop
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(function (backdrop) {
            backdrop.remove();
            console.log('✅ Modal backdrop removido');
        });

        // 3. Remover TODOS los elementos con clase modal
        const modals = document.querySelectorAll('.modal');
        modals.forEach(function (modal) {
            modal.remove();
            console.log('✅ Modal removido completamente:', modal.id);
        });

        // 4. Remover cualquier overlay problemático
        const overlays = document.querySelectorAll('[style*="box-shadow"]');
        overlays.forEach(function (overlay) {
            if (overlay.style.boxShadow && overlay.style.boxShadow.includes('10000px') ||
                overlay.style.boxShadow && overlay.style.boxShadow.includes('100vmax')) {
                overlay.style.boxShadow = 'none';
                console.log('✅ Overlay removido:', overlay);
            }
        });

        // 5. Remover cualquier elemento con backdrop-filter que pueda bloquear
        const backdropElements = document.querySelectorAll('[style*="backdrop-filter"]');
        backdropElements.forEach(function (element) {
            if (element.style.backdropFilter && element.style.backdropFilter.includes('blur')) {
                element.style.backdropFilter = 'none';
                console.log('✅ Backdrop filter removido:', element);
            }
        });

        // 6. Limpiar cualquier estado de body que pueda estar causando problemas
        document.body.classList.remove('modal-open');
        document.body.style.overflow = 'auto';
        document.body.style.paddingRight = '';

        console.log('✅ Limpieza completa de modales y backdrops realizada');
    }

    // Función para aplicar estilos CSS de emergencia
    function applyEmergencyStyles() {
        const emergencyCSS = `
            <style id="emergency-styles">
                /* Estilos de emergencia para páginas de examen */
                body[data-exam-page="true"] * {
                    pointer-events: auto !important;
                }
                
                body[data-exam-page="true"] #quiz-form,
                body[data-exam-page="true"] #quiz-form * {
                    pointer-events: auto !important;
                    z-index: 1060 !important;
                    position: relative !important;
                }
                
                body[data-exam-page="true"] #submit-btn {
                    pointer-events: auto !important;
                    cursor: pointer !important;
                    z-index: 1070 !important;
                    position: relative !important;
                }
                
                /* ELIMINAR COMPLETAMENTE TODOS LOS MODALES Y BACKDROPS */
                body[data-exam-page="true"] .modal,
                body[data-exam-page="true"] .modal-backdrop,
                body[data-exam-page="true"] .modal-dialog,
                body[data-exam-page="true"] .modal-content {
                    display: none !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                    z-index: -1 !important;
                }
                
                body[data-exam-page="true"] #top-navbar.dim {
                    opacity: 1 !important;
                    pointer-events: auto !important;
                    box-shadow: 0 4px 20px rgba(186, 96, 34, 0.3) !important;
                    background: linear-gradient(135deg, #BA6022 0%, #A0521E 100%) !important;
                }
                
                /* Asegurar que no haya elementos que bloqueen */
                body[data-exam-page="true"] *[style*="pointer-events: none"] {
                    pointer-events: auto !important;
                }
                
                body[data-exam-page="true"] *[style*="z-index: -1"] {
                    z-index: auto !important;
                }
                
                /* Prevenir overlays problemáticos */
                body[data-exam-page="true"] *[style*="box-shadow: 0 0 0 10000px"] {
                    box-shadow: none !important;
                }
                
                body[data-exam-page="true"] *[style*="box-shadow: 0 0 0 100vmax"] {
                    box-shadow: none !important;
                }
                
                /* Asegurar que el navbar sea siempre funcional */
                body[data-exam-page="true"] #top-navbar {
                    opacity: 1 !important;
                    pointer-events: auto !important;
                    z-index: 1001 !important;
                }
                
                /* Asegurar que el sidebar sea funcional */
                body[data-exam-page="true"] #side-nav {
                    pointer-events: auto !important;
                    z-index: 1000 !important;
                }
                
                /* Asegurar que el contenido principal sea funcional */
                body[data-exam-page="true"] #main-content {
                    pointer-events: auto !important;
                    z-index: 1 !important;
                }
                
                /* Prevenir que se abran modales */
                body[data-exam-page="true"] .modal.show {
                    display: none !important;
                }
                
                body[data-exam-page="true"] .modal-backdrop.show {
                    display: none !important;
                }
            </style>
        `;

        // Remover estilos de emergencia anteriores si existen
        const existingStyles = document.getElementById('emergency-styles');
        if (existingStyles) {
            existingStyles.remove();
        }

        // Agregar nuevos estilos
        document.head.insertAdjacentHTML('beforeend', emergencyCSS);
        console.log('✅ Estilos de emergencia aplicados');
    }

    // Función para configurar protección continua
    function setupContinuousProtection() {
        // Monitorear continuamente para prevenir bloqueos
        setInterval(function () {
            // Verificar que la clase dim no esté presente
            const topNavbar = document.getElementById('top-navbar');
            if (topNavbar && topNavbar.classList.contains('dim')) {
                topNavbar.classList.remove('dim');
                console.log('🛡️ Clase dim removida automáticamente');
            }

            // Verificar que el formulario sea interactivo
            const quizForm = document.getElementById('quiz-form');
            if (quizForm && quizForm.style.pointerEvents !== 'auto') {
                quizForm.style.pointerEvents = 'auto';
                console.log('🛡️ Formulario restaurado automáticamente');
            }

            // Verificar que el botón de envío sea interactivo
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn && submitBtn.style.pointerEvents !== 'auto') {
                submitBtn.style.pointerEvents = 'auto';
                submitBtn.style.cursor = 'pointer';
                console.log('🛡️ Botón de envío restaurado automáticamente');
            }

            // Verificar que no haya backdrops problemáticos
            const backdrops = document.querySelectorAll('.modal-backdrop');
            if (backdrops.length > 0) {
                backdrops.forEach(function (backdrop) {
                    backdrop.remove();
                });
                console.log('🛡️ Backdrops removidos automáticamente');
            }

            // Verificar que no haya modales abiertos
            const modals = document.querySelectorAll('.modal.show');
            if (modals.length > 0) {
                modals.forEach(function (modal) {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                });
                console.log('🛡️ Modales cerrados automáticamente');
            }
        }, 2000); // Verificar cada 2 segundos

        console.log('✅ Protección continua configurada');
    }

    // Función para mostrar mensaje de éxito
    function showSuccessMessage() {
        const message = document.createElement('div');
        message.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                z-index: 9999;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                max-width: 300px;
            ">
                <strong>✅ ¡Página desbloqueada!</strong><br>
                El examen debería funcionar correctamente ahora.
            </div>
        `;
        document.body.appendChild(message);

        // Remover el mensaje después de 5 segundos
        setTimeout(function () {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 5000);
    }

    // Función para mostrar mensaje de error
    function showErrorMessage() {
        const message = document.createElement('div');
        message.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #dc3545;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                z-index: 9999;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                max-width: 300px;
            ">
                <strong>❌ Error en el desbloqueo</strong><br>
                Revisa la consola para más detalles.
            </div>
        `;
        document.body.appendChild(message);

        // Remover el mensaje después de 5 segundos
        setTimeout(function () {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 5000);
    }

    // Ejecutar desbloqueo inmediatamente
    emergencyUnlock();

    // Ejecutar desbloqueo adicional después de delays
    setTimeout(emergencyUnlock, 100);
    setTimeout(emergencyUnlock, 500);
    setTimeout(emergencyUnlock, 1000);

    // Crear función global para uso manual
    window.emergencyUnlockExam = emergencyUnlock;

    console.log('💡 Para desbloquear manualmente en el futuro, ejecuta: emergencyUnlockExam()');

})(); 