# pyxparser

A Python parser for ANAREDE electrical power system files.

> [![image](https://img.shields.io/pypi/v/r2x.svg)](https://pypi.python.org/pypi/r2x)
> [![image](https://img.shields.io/pypi/l/r2x.svg)](https://pypi.python.org/pypi/r2x)
>[![codecov](https://codecov.io/gh/yourusername/pyxparser/branch/main/graph/badge.svg)](https://codecov.io/gh/mcllerena/pyxparser)
>[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
>[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://mcllerena.github.io/pyxparser)

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Installation](#installation)
  - [From PyPI (when published)](#from-pypi-when-published)
  - [From source](#from-source)
  - [Development installation](#development-installation)
- [Configuration](#configuration)
- [Current Support Fields](#current-support-fields)
- [Setup Development Environment](#setup-development-environment)
- [CLI Usage](#cli-usage)
  - [Options](#options)
  - [Example](#example)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

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
| **DLIN** | AC Circuit data | ✅ Supported |
| **DGER** | Generator data | ✅ Supported  |
| **DCSC** | CSC* data | ✅ Supported |
| **DCER** | SVC** data | ✅ Supported |
| **DBSH** | Bus Capacitor/reactor*** banks data | ✅ Supported |
| **DSHL** | AC Circuit shunt data | ✅ Supported |
| **DCAI** | Individualized load data**** | 🟡 Partially |
| **DELO** | DC Link nominal data | 🔄 Planned |
| **DCBA** | DC Bus data | 🔄 Planned |
| **DCLI** | DC Line data | 🔄 Planned |
| **DCNV** | AC-DC converter data | 🔄 Planned |
| **DCCV** | AC-DC converter control data | 🔄 Planned |

*CSC: Controllable Series Compensator

**SVC: Static VAR Compensator

***Capacitor/Reactor Banks: For groups or banks of individualized capacitors and/or reactors connected to the same bus, the settings for minimum and maximum voltage control range, controlled bus, and voltage control strategy must always be identical. Different settings for banks connected to the same bus would cause conflicts between voltage adjustment controls and are therefore not permitted. In this regard, individualized capacitor/reactor banks connected to a transmission line are considered to be connected to the bus corresponding to the line terminal where they are installed [1].

****DCAI: For each individualized load group, parameters A, B, C, and D are read to establish the load variation curve with respect to voltage magnitude at the respective bus. Loads of this type are modeled by ZIP load characteristics:

**Active Power Load:**

$$P_{load} = \begin{cases}
\left(100-A-B + A \cdot \frac{V}{V_{def}} + B \cdot \frac{V^2}{V_{def}^2}\right) \cdot \frac{P}{100} & \text{if } V \geq V_{fld} \\
\left((100-A-B) \cdot \frac{V^2}{V_{fld}^2} + A \cdot \frac{V^2}{V_{def} \cdot V_{fld}} + B \cdot \frac{V^2}{V_{def}^2}\right) \cdot \frac{P}{100} & \text{if } V < V_{fld}
\end{cases}$$

**Reactive Power Load:**

$$Q_{load} = \begin{cases}
\left(100-C-D + C \cdot \frac{V}{V_{def}} + D \cdot \frac{V^2}{V_{def}^2}\right) \cdot \frac{Q}{100} & \text{if } V \geq V_{fld} \\
\left((100-C-D) \cdot \frac{V^2}{V_{fld}^2} + C \cdot \frac{V^2}{V_{def} \cdot V_{fld}} + D \cdot \frac{V^2}{V_{def}^2}\right) \cdot \frac{Q}{100} & \text{if } V < V_{fld}
\end{cases}$$

**Where:**
- **A, C**: Parameters defining load portions represented by constant current (% of total load)
- **B, D**: Parameters defining load portions represented by constant impedance (% of total load)
- **$(100-A-B)$, $(100-C-D)$**: Constant power portions (% of total load)
- **P, Q**: Active and reactive loads at reference voltage $V_{def}$ (MW, MVAr)
- **$V_{fld}$**: Voltage threshold below which constant power and constant current portions are modeled as constant impedance (p.u.)
- **$V_{def}$**: Reference voltage for which load values P and Q were measured (p.u.)
- **V**: Actual bus voltage (p.u.)

**Note**: The ZIP load modeling with voltage-dependent parameters A, B, C, D is parsed but not yet implemented in the power flow calculations. Currently, only the base load values (P, Q) and units in operation are integrated into the bus load data.

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

## CLI Usage

Parse ANAREDE files from the command line:

```bash
pyxparser -i <input_path>/input.pwf -o <output_path>/output.dat -f dat
```

For output verbosity use:

```bash
pyxparser -i <input_path>/input.pwf -o <output_path>/output.dat -f dat -v
```

or

```bash
pyxparser -i <input_path>/input.pwf -o <output_path>/output.dat -f dat -vv
```

### Options

- `-i, --input` - Input ANAREDE file path
- `-o, --output` - Output file path
- `-f, --format` - Output format (dat)
- `-v, --verbose` - Enable verbose logging

### Example

```bash
# Parse ANAREDE file and convert to DAT format
pyxparser -i input.pwf -o output.dat -f dat -v
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

## References

[1] ANAREDE (2015). *Análise de Redes Elétricas - User Manual and Technical Documentation*. CEPEL (Centro de Pesquisas de Energia Elétrica).
