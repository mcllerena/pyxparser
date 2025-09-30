# pyxparser

A Python parser for ANAREDE electrical power system files.

## Description

pyxparser is a Python library designed to parse and process ANAREDE (Análise de Redes Elétricas) files used in electrical power system analysis (Brazil). It provides a simple and efficient way to read, parse, and convert ANAREDE data formats.

## Features

- Parse ANAREDE bus data (DBAR records)
- Convert fixed-width format to structured data
- Configurable field mappings
- Support for multiple ANAREDE data types
- Type hints and modern Python support (3.12+)

## Installation

### From PyPI (when published)
```bash
uv pip install pyxparser
```

### From source
```bash
git clone https://github.com/yourusername/pyxparser.git
cd pyxparser
pip install -e .
```

### Development installation
```bash
git clone https://github.com/yourusername/pyxparser.git
cd pyxparser
uv venv
uv sync --dev
```

## Configuration

The parser uses JSON configuration files to define field mappings.
See `src/pyxparser/defaults/anarede_mapping.json` for the default ANAREDE format specification.

## Current Support Fields

| Record Type | Description | Status |
|-------------|-------------|--------|
| **DBAR** | AC Bus data | ✅ Supported |
| **DLIN** | Transmission line data | ✅ Supported |
| **DGER** | Generator data | ✅ Supported  |
| **DCSC** | CSC* data | 🔄 Planned |
| **DCER** | SVC* data | 🔄 Planned |
| **DELO** | DC Link nominal data | 🔄 Planned |
| **DCBA** | DC Bus data | 🔄 Planned |
| **DCLI** | DC Line data | 🔄 Planned |
| **DCNV** | AC-DC converter data | 🔄 Planned |
| **DCCV** | AC-DC converter control data | 🔄 Planned |

*CSC: Controllable Series Compensator

*SVC: Static VAR Compensator

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pyxparser.git
cd pyxparser

# Create virtual environment with uv
uv venv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality (`uv run pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- ANAREDE (2015) documentation and format specifications
