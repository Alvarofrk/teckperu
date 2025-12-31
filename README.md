# 🎓 Plataforma Educativa SeguridadTECKPerú

> **Sistema LMS Enterprise para Capacitación en Seguridad Industrial**  
> *Una solución tecnológica integral, segura y escalable para la gestión del aprendizaje corporativo.*

![Python](https://img.shields.io/badge/Python-3.9.18-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Google Cloud](https://img.shields.io/badge/GCP-App_Engine-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-Payments-008CDD?style=for-the-badge&logo=stripe&logoColor=white)

---

## 📑 Tabla de Contenidos

1.  [Descripción General](#-descripción-general)
2.  [Arquitectura del Sistema](#-arquitectura-del-sistema)
3.  [Módulos Nucleares](#-módulos-nucleares)
    *   [Gestión Académica (Cursos)](#-gestión-académica-app-course)
    *   [Sistema de Evaluación (Quiz)](#-sistema-de-evaluación-app-quiz)
    *   [Analítica y Resultados](#-analítica-y-resultados-app-result)
4.  [Infraestructura y Despliegue](#-infraestructura-y-despliegue)
5.  [Seguridad y Compliance](#-seguridad-y-compliance)
6.  [Guía de Instalación](#-guía-de-instalación)
7.  [Propiedad Intelectual](#-propiedad-intelectual)

---

## 📋 Descripción General

**SeguridadTECKPerú** no es solo un LMS (Learning Management System); es una plataforma de certificación industrial de misión crítica. Diseñada específicamente para **TECK Perú**, permite la capacitación masiva de personal operario y administrativo con estándares de auditoría rigurosos.

La plataforma resuelve la necesidad de trazabilidad en la capacitación: **"¿Quién se capacitó? ¿Cuándo? ¿Aprobó realmente el examen? ¿Es su certificado válido?"**.

### Capacidades Clave
*   **Certificación Dinámica:** Generación automática de certificados PDF con códigos únicos antifraude (`certificate_code` secuencial por curso).
*   **Sincronización Video-Documento:** Experiencia de aprendizaje dual donde los videos (Vimeo) se vinculan contextualmente con manuales técnicos (PDF/Excel).
*   **Integridad de Exámenes:** Motores de aleatorización de preguntas y respuestas para prevenir copias.

---

## 🏗️ Arquitectura del Sistema

El sistema opera bajo una arquitectura **Monolítica Modular (Modular Monolith)**, lo que permite la simplicidad de despliegue de un monolito con la separación de intereses de los microservicios.

### Stack Tecnológico Detallado

| Capa | Tecnología | Detalles de Implementación |
| :--- | :--- | :--- |
| **Backend Core** | Django 5.x | Framework de alto nivel. Uso extensivo de *Class Based Views (CBVs)* para lógica reutilizable. |
| **Base de Datos** | PostgreSQL 16 | Modelo relacional estricto. Índices optimizados para búsquedas de alumnos y certificados. |
| **Frontend** | Django Templates | Renderizado servidor (SSR) con **Bootstrap 5** y **Crispy Forms** para formularios responsivos. |
| **Admin UI** | Django JET | Interfaz administrativa moderna con dashboards analíticos y temas oscuros/claros. |
| **API Layer** | Django Rest Framework | (Parcial) Endpoints internos para actualizaciones asíncronas de progreso. |
| **Media Server** | WhiteNoise / GCP Storage | Gestión híbrida de estáticos y archivos multimedia (Videos/PDFs). |

---

## 📦 Módulos Nucleares

### 📚 Gestión Académica (App: `course`)

El corazón del sistema. Maneja la jerarquía de aprendizaje:
`Programa -> Curso -> Materiales (Videos/Archivos)`.

*   **Lógica de Negocio (`Course` Model):**
    *   Gestión de créditos y códigos únicos.
    *   Sistema de slugs automáticos (`unique_slug_generator`) para URLs amigables SEO.
*   **Gestor de Archivos (`Upload` Model):**
    *   Validador estricto de extensiones (`pdf`, `docx`, `xlsx`, `zip`, etc.) para prevenir uploads maliciosos.
    *   Clasificación automática de tipos de archivo para iconos en UI.
*   **Integración Multimedia (`UploadVideo` Model):**
    *   Soporte nativo para videos alojados localmente (`mp4`, `mkv`).
    *   **Integración Vimeo:** Extracción automática de IDs y Thumbnails desde URLs de Vimeo.

### 📝 Sistema de Evaluación (App: `quiz`)

Un motor de exámenes robusto diseñado para prevenir el fraude académico.

*   **Configuración de Exámenes (`Quiz` Model):**
    *   `random_order`: Mezcla aleatoriamente las preguntas para cada intento.
    *   `single_attempt`: Modo estricto para exámenes de certificación final.
    *   `pass_mark`: Umbral configurable (0-100%) para aprobación.
*   **Banco de Preguntas (`Question` Model):**
    *   Soporte polimórfico: Preguntas de Opción Múltiple (`MCQuestion`) y Ensayo (`EssayQuestion`).
    *   Imágenes de soporte (figuras/diagramas) por pregunta.
*   **Motor de Intentos (`Sitting` Model):**
    *   Almacena el estado exacto de cada examen tomado (respuestas del usuario en JSON `user_answers`).
    *   **Cálculo de Score:** Tasa de aciertos en tiempo real.
    *   **Certificados:** Generación de `certificate_code` (formato `NNN`, ej. `005`) solo al aprobar (`check_if_passed`).

### 📊 Analítica y Resultados (App: `result`)

Transforma datos de exámenes en métricas de rendimiento.

*   **Métricas Calculadas:**
    *   **GPA (Grade Point Average):** Promedio ponderado del semestre actual.
    *   **CGPA (Cumulative GPA):** Promedio acumulado histórico.
*   **Sistema de Calificación:**
    *   Escala alfabética internacional (A+, A, B, etc.) mapeada a rangos numéricos (ej. 90-100 = A+).
    *   Estados: `PASS` / `FAIL`.

---

## ☁️ Infraestructura y Despliegue

La plataforma es **Cloud-Native**, optimizada para **Google Cloud Platform (GCP)**.

### Estrategia Serverless (Google App Engine)

El archivo `app.yaml` orquesta el entorno de producción:

```yaml
runtime: python39
instance_class: F2  # Instancias con mayor memoria para procesar PDFs
automatic_scaling:
  min_instances: 1  # Siempre disponible (evita cold-starts)
  max_instances: 10 # Escala según demanda en exámenes masivos
env_variables:
  DJANGO_SETTINGS_MODULE: "config.settings"
  # Conexión segura a Cloud SQL mediante Unix Sockets
  CLOUD_SQL_CONNECTION_NAME: "seguridadteckperu:us-central1:db"
```

### Bases de Datos (Cloud SQL)
*   **Alta Disponibilidad:** Configuración regional con failover automático.
*   **Seguridad:** Encriptación en reposo y tránsito. Acceso restringido vía IAM.

---

## 🔐 Seguridad y Compliance

*   **Control de Acceso Basado en Roles (RBAC):**
    *   Decoradores `@student_required` y `@lecturer_required` protegen vistas críticas.
    *   Jerarquía: `Superuser > Admin > Lecturer > Student`.
*   **Protección de Datos:**
    *   **CSRF Protection:** Tokens obligatorios en todos los formularios `POST`.
    *   **Secure Headers:** HSTS, X-Frame-Options y Content-Type-Options configurados.
*   **Auditoría (`ActivityLog`):**
    *   Registro inmutable de acciones críticas (Creación de cursos, borrado de notas, subida de archivos).

---

## 💳 Pasarelas de Pago

Arquitectura modular preparada para monetización global.

*   **Stripe:** Pagos con tarjeta. Uso de `Stripe.js` para tokenización segura en el cliente (PCI Compliance SAQ-A).
*   **GoPay:** Integración bancaria europea para transferencias y pagos recurrentes.
*   **Modelos:** `Invoice` genera facturas trazables vinculadas a transacciones únicas.

---

## ⚖️ Propiedad Intelectual

> [!CAUTION]
> **PROPIEDAD EXCLUSIVA Y DERECHOS RESERVADOS**

Este software, incluyendo su código fuente, estructura de base de datos, diseño de interfaz y algoritmos de evaluación, es propiedad intelectual exclusiva de **Alvaro Franco Cerna Ramos**.

**Condiciones de Licencia para TECK Perú:**
1.  **Licencia de Uso:** Se otorga una licencia limitada, no exclusiva e intransferible para uso interno.
2.  **Prohibiciones:** Queda estrictamente prohibido copiar, modificar, distribuir, vender o realizar ingeniería inversa sobre cualquier componente del sistema.
3.  **Confidencialidad:** El acceso al código fuente está restringido exclusivamente a personal autorizado por el propietario con fines de mantenimiento.

**Intermediación:**
G.P.D. CONSULTORES S.A.C. actúa como intermediario autorizado para la gestión comercial, sin derechos de propiedad sobre el software.

---

*Copyright © 2025 Alvaro Franco Cerna Ramos. Todos los derechos reservados.*
*Versión de Documentación: 2.0 (Enterprise Release)*
