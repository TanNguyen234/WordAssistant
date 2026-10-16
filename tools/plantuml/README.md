# PlantUML Standalone Integration

This directory contains the standalone PlantUML engine used by WordAssistant to render UML diagrams directly into PNG/SVG images for inclusion in Word (.docx) documents.

- **Upstream Repository**: [https://github.com/plantuml/plantuml](https://github.com/plantuml/plantuml)
- **Version**: 1.2026.8
- **Engine**: `plantuml.jar` with internal Smetana (pure Java Graphviz implementation)
- **License**: GPL / LGPL / ASL / EPL / MIT (PlantUML license matrix)

## Usage

### Windows:
```cmd
tools\plantuml\plantuml.bat input.puml -tpng
```

### Linux / macOS:
```bash
./tools/plantuml/plantuml input.puml -tpng
```

### WordAssistant CLI:
```bash
wordassistant plantuml doctor
wordassistant plantuml render diagram.puml --output diagram.png
```
