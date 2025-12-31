# 🎓 Plataforma Educativa SeguridadTECKPerú

> **Sistema LMS de Alto Rendimiento para Capacitación Industrial**  
> *Desarrollado exclusivamente para TECK Perú bajo licencia.*

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-App_Engine-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-008CDD?style=for-the-badge&logo=stripe&logoColor=white)

---

## 📋 Resumen Ejecutivo

**SeguridadTECKPerú** es una plataforma de gestión de aprendizaje (LMS) robusta y escalable diseñada para optimizar la capacitación en seguridad industrial. A diferencia de los LMS genéricos, este sistema ha sido construido a medida para manejar flujos complejos de certificación, seguimiento de métricas en tiempo real y una experiencia de usuario fluida tanto para instructores como para estudiantes.

El sistema garantiza integridad académica mediante algoritmos antifraude en exámenes, genera certificados oficiales con trazabilidad única y ofrece dashboards analíticos para la toma de decisiones estratégicas.

---

## 🏗️ Arquitectura Técnica

El proyecto sigue una arquitectura **monolítica modular** basada en Django, optimizada para despliegue en la nube (Cloud Native).

### Stack Tecnológico

| Componente | Tecnología | Descripción |
| :--- | :--- | :--- |
| **Backend** | Python 3.9 / Django 5.x | Lógica de negocio, ORM y seguridad. |
| **Base de Datos** | PostgreSQL 16 | Relacional, robusta, alojada en Cloud SQL. |
| **Frontend** | Django Templates + Bootstrap 5 | Renderizado del lado del servidor (SSR) para velocidad y SEO. |
| **Estilos** | Crispy Forms / FontAwesome 6 | UI componentes y formularios reactivos. |
| **Servidor Web** | Gunicorn / WhiteNoise | WSGI server y gestión eficiente de estáticos. |
| **Pagos** | Stripe / GoPay API | Pasarelas seguras para transacciones internacionales. |

### Infraestructura en Google Cloud Platform (GCP)

La aplicación está diseñada para ejecutarse en un entorno **Serverless** para máxima escalabilidad y cero mantenimiento de servidores.

1.  **Google App Engine (Standard Environment):**
    *   Escalado automático de 0 a N instancias según el tráfico.
    *   Gestión de versiones para despliegues Blue/Green.
    *   Configuración mediante `app.yaml` optimizado.

2.  **Google Cloud SQL (PostgreSQL):**
    *   Instancia gestionada de alta disponibilidad.
    *   Conexión segura mediante Cloud SQL Proxy o IP privada.
    *   Backups automáticos diarios.

3.  **Cloud Storage (Recomendado):**
    *   Almacenamiento de objectos (S3 compatible) para archivos multimedia (videos, PDFs de cursos).
    *   CDN global para entrega rápida de contenido.

---

## 📊 Dashboards y Analítica de Datos

Uno de los pilares del proyecto es la capacidad de transformar datos crudos en información accionable para los administradores de TECK Perú.

### 🚀 Panel Administrativo Avanzado (Django JET)
Hemos implementado **Django JET** para modernizar la interfaz de administración por defecto, proporcionando un dashboard visual e interactivo.

*   **KPIs en Tiempo Real:** Visualización de usuarios activos, cursos completados hoy, y tasa de aprobación.
*   **Gráficos Integrados:** Tendencias de registro de usuarios y distribución de notas.
*   **Navegación Intuitiva:** Menús laterales colapsables y búsqueda global avanzada.

### 📈 Sistema de Seguimiento Académico (`Result` App)
El módulo de resultados no solo almacena notas, sino que calcula el rendimiento integral del estudiante:

*   **Cálculo de GPA/CGPA:** Algoritmo ponderado basado en créditos del curso y puntaje obtenido (A+, A, A-, etc.).
*   **Desglose de Evaluación:**
    *   Seguimiento granular: *Asistencia, Tareas, Quiz, Parcial, Final*.
    *   Cada componente tiene un peso configurable en la nota final.
*   **Reportes de Rendimiento:** Identificación automática de estudiantes en riesgo (Grade 'F' o 'NG') para intervención temprana.

---

## 🔐 Seguridad y Pagos

### Pasarelas de Pago
El sistema integra múltiples proveedores para flexibilidad global, centralizado en la app `payments`.

*   **Stripe:** Implementación completa para cobros con tarjeta de crédito/débito. Webhooks configurados para confirmar pagos asincrónicamente.
*   **GoPay:** Integración para pagos bancarios locales (soporte CZE/EUR), con gestión de recurrencia y pagos pre-autorizados.
*   **Extensibilidad:** Arquitectura lista para activar PayPal, Coinbase (Crypto) y Paylike mediante adaptadores modulares.

### Seguridad del Aplicativo
*   **Protección CSRF & XSS:** Activa en todos los formularios y vistas.
*   **Gestión de Sesiones:** Cookies seguras (Httponly, Secure) forzadas en producción.
*   **Roles y Permisos:** Decoradores personalizados (`@student_required`, `@lecturer_required`) aseguran que solo usuarios autorizados accedan a recursos sensibles.

---

## 🚀 Guía de Despliegue en GCP

Siga estos pasos para desplegar una nueva versión en Google Cloud App Engine.

### 1. Pre-requisitos
*   Google Cloud SDK (`gcloud`) instalado y autenticado.
*   Proyecto GCP activo con APIs de App Engine y Cloud SQL habilitadas.

### 2. Configuración de Entorno
Asegúrese de tener el archivo `app.yaml` configurado con sus credenciales de producción (o use Secret Manager):

```yaml
# app.yaml snippet
runtime: python39
env_variables:
  DJANGO_SETTINGS_MODULE: "config.settings"
  CLOUD_SQL_CONNECTION_NAME: "proyecto:region:instancia"
  DB_NAME: "prod_db"
  # ... otras variables
```

### 3. Despliegue
Ejecute el siguiente comando en la terminal:

```bash
gcloud app deploy
```

Este comando:
1.  Empaquetará el código fuente (respetando `.gcloudignore`).
2.  Subirá los archivos a Cloud Build.
3.  Instalará las dependencias de `requirements.txt`.
4.  Lanzará la nueva versión y migrará el tráfico automáticamente.

### 4. Migraciones de Base de Datos
Para aplicar cambios en el esquema de la base de datos en producción:

```bash
# Conectarse a la instancia vía Cloud Shell o Proxy y ejecutar:
python manage.py migrate
```

---

## ⚖️ Propiedad Intelectual y Licencia

> [!CAUTION]
> **PROPIEDAD EXCLUSIVA**: Este software es propiedad intelectual de **Alvaro Franco Cerna Ramos**.

**Términos Clave:**
*   **Cliente con Licencia:** TECK Perú tiene una licencia de uso perpetua, no exclusiva y limitada a sus operaciones internas.
*   **Restricciones:** Queda estrictamente prohibida la venta, redistribución, sublicencia o ingeniería inversa del código fuente.
*   **Intermediario:** G.P.D. CONSULTORES S.A.C. actúa como facilitador autorizado.

*Copyright © 2025 Alvaro Franco Cerna Ramos. Todos los derechos reservados.*
