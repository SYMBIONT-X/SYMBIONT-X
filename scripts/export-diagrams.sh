#!/bin/bash

# SYMBIONT-X Diagram Export Script
# Exports all Mermaid diagrams to PNG

echo "🎨 Exporting SYMBIONT-X diagrams to PNG..."

# Instalar mmdc (Mermaid CLI) si no existe
if ! command -v mmdc &> /dev/null; then
    echo "📦 Installing Mermaid CLI..."
    npm install -g @mermaid-js/mermaid-cli
fi

# Crear carpeta de exports
mkdir -p docs/diagrams/exports

# Exportar diagramas ejecutivos
echo "📊 Exporting executive diagrams..."

mmdc -i docs/diagrams/executive/system-architecture.md \
     -o docs/diagrams/exports/system-architecture-executive.png \
     -w 1920 \
     -H 1080 \
     -t default \
     -b transparent

mmdc -i docs/diagrams/executive/agent-flow.md \
     -o docs/diagrams/exports/agent-flow-executive.png \
     -w 1920 \
     -H 1080 \
     -t default \
     -b transparent

mmdc -i docs/diagrams/executive/sequence-diagram.md \
     -o docs/diagrams/exports/sequence-diagram-executive.png \
     -w 1920 \
     -H 1400 \
     -t default \
     -b transparent

echo "✅ Export complete! Files saved to docs/diagrams/exports/"
ls -lh docs/diagrams/exports/
