# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Agregado
- Configuración inicial del proyecto con estructura modular
- Sistema de gestión de repositorios Git (clonar, listar, seleccionar)
- Integración con Google Gemini AI para chat y análisis
- Sistema de caché para respuestas de Gemini
- Logging estructurado con niveles configurables
- Estimación de costos para modelos de pago
- Documentación completa (README, docstrings)
- Suite de tests unitarios con pytest
- Configuración de CI/CD con GitHub Actions
- Empaquetado moderno con pyproject.toml
- Utilidades comunes (validación, formateo, sanitización)
- Soporte para múltiples modelos de Gemini con información de tiers

### Mejorado
- Manejo de errores más robusto
- Validación de entradas de usuario
- Configuración mediante variables de entorno
- Interfaz de usuario con Rich para mejor experiencia

### Seguridad
- Validación de rutas para prevenir path traversal
- Sanitización de nombres de archivo
- API keys manejadas de forma segura mediante .env

## [0.1.0] - 2024-01-XX (Por lanzar)

### Notas
- Primera versión alpha del proyecto
- Funcionalidades básicas implementadas
- Listo para pruebas internas 