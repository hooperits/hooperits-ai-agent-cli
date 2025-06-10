#!/bin/bash
# Script de instalación rápida para HOOPERITS AI CODE AGENT

set -e  # Salir si hay errores

echo "🤖 Instalando HOOPERITS AI CODE AGENT..."
echo "========================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado."
    echo "Por favor, instala Python 3.8 o superior."
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Se requiere Python $REQUIRED_VERSION o superior (tienes $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detectado"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv .venv

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate

# Actualizar pip
echo "📥 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Instalar en modo desarrollo
echo "🔨 Instalando HOOPERITS Agent en modo desarrollo..."
pip install -e .

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde plantilla..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Edita el archivo .env y agrega tu GOOGLE_API_KEY"
    echo "   Puedes obtener una clave en: https://makersuite.google.com/app/apikey"
fi

echo ""
echo "✨ ¡Instalación completada!"
echo ""
echo "Para comenzar a usar HOOPERITS Agent:"
echo "1. Activa el entorno virtual: source .venv/bin/activate"
echo "2. Configura tu API key en .env"
echo "3. Ejecuta: hooperits-agent --help"
echo ""
echo "¡Feliz codificación! 🚀" 