"""CLI helper functions."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict
from loguru import logger

from .__version__ import __version__
from .enums import INFINITY_VALUE, BASE_POWER_MVA, DEFAULT_VMAX, DEFAULT_VMIN


def base_cli() -> argparse.ArgumentParser:
    """Create parser object for CLI."""
    parser = argparse.ArgumentParser(
        description="Parse ANAREDE electrical power system files",
        add_help=True,
        prog="pyxparser",
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to the PWF/ANAREDE input file to parse",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path (optional, defaults to stdout)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "yaml", "dat"],
        default="json",
        help="Output format (default: json). 'dat' format is for modeling.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Run with additional verbosity (can be used multiple times: -v, -vv, -vvv)",
    )

    parser.add_argument("--log-file", type=str, help="Path to log file (optional)")

    parser.add_argument(
        "--version", "-V", action="version", version=f"pyxparser version: {__version__}"
    )

    return parser


def handle_output(result: Dict[str, Any], args: argparse.Namespace) -> None:
    """Handle output formatting and saving.

    Args:
        result: Parsed data dictionary
        args: CLI arguments namespace
    """

    if args.output:
        output_path = Path(args.output)

        # Save to file based on format
        if args.format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        elif args.format == "csv":
            # TODO: Implement CSV export
            raise NotImplementedError("CSV format not yet implemented")
        elif args.format == "yaml":
            # TODO: Implement YAML export
            raise NotImplementedError("YAML format not yet implemented")
        elif args.format == "dat":
            _write_dat_file(result, output_path)

    else:
        # Print to stdout
        if args.format == "json":
            print(json.dumps(result, indent=2))
        elif args.format == "dat":
            _print_dat_format(result)
        else:
            # For other formats, default to JSON when printing to stdout
            print(json.dumps(result, indent=2))


def _print_dat_format(result: Dict[str, Any]) -> None:
    """Print data in .dat format to stdout.

    Args:
        result: Parsed data dictionary
    """
    print(_format_dat_file(result))


def _write_dat_file(result: Dict[str, Any], output_path: Path) -> None:
    """Write data in .dat format to file.

    Args:
        result: Parsed data dictionary
        output_path: Path to output file
    """
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(_format_dat_file(result))

    except Exception as e:
        logger.error(f"Error writing .dat file {output_path}: {e}")
        raise


def _format_dat_file(result: Dict[str, Any]) -> str:
    """Format data as .dat file content.

    Args:
        result: Parsed data dictionary

    Returns:
        String in .dat format
    """
    dat_content = []

    # System base power
    dat_content.append("# System base power")
    dat_content.append(f"param BASE := {BASE_POWER_MVA};\n")

    # Process DBAR data (buses)
    if "DBAR" in result and result["DBAR"]:
        buses = result["DBAR"]

        # Create a lookup for DGER data by bus number
        dger_lookup = {}
        if "DGER" in result and result["DGER"]:
            for dger in result["DGER"]:
                bus_num = dger.get("number")
                if bus_num:
                    dger_lookup[bus_num] = dger

        dat_content.append("# Bus data")
        dat_content.append(
            "param: DBAR:       Name Tb   Are    V0      A0        Pg0      Qg0       Pgm        Pgn        Qgm        Qgn         Pl         Ql        Bsh       Vmx       Vmn    :="
        )
        dat_content.append(
            "#                                 [pu]  [grau]       [MW]   [MVAr]      [MW]       [MW]     [MVAr]     [MVAr]       [MW]     [MVAr]       [pu]      [pu]      [pu]      "
        )

        for bus in buses:
            if bus.get("state", "L") == "L":  # Only connected buses
                # Convert all values to proper types with safe defaults
                num = int(bus.get("number", 0)) if bus.get("number") else 0
                name = str(bus.get("name", "")).strip()[:12]
                tb = int(bus.get("type", 0)) if bus.get("type") else 0
                area = int(bus.get("area", 1)) if bus.get("area") else 1
                v0_val = bus.get("voltage")
                v0 = (float(v0_val) / 1000.0) if v0_val not in [None, ""] else 1.0
                a0 = float(bus.get("angle", 0.0)) if bus.get("angle") else 0.0
                pg0 = (
                    float(bus.get("active_generation", 0.0))
                    if bus.get("active_generation")
                    else 0.0
                )
                qg0 = (
                    float(bus.get("reactive_generation", 0.0))
                    if bus.get("reactive_generation")
                    else 0.0
                )

                # Get active power limits from DGER data
                dger_data = dger_lookup.get(num, dger_lookup.get(str(num), {}))
                pgm_val = dger_data.get("max_active_generation")
                pgn_val = dger_data.get("min_active_generation")
                pgm = float(pgm_val) if pgm_val is not None else INFINITY_VALUE
                pgn = float(pgn_val) if pgn_val is not None else -INFINITY_VALUE

                # Get reactive power limits from DBAR data
                # Get reactive power limits from DBAR data
                qgm_val = bus.get("max_reactive_generation")
                qgn_val = bus.get("min_reactive_generation")
                qgm = float(qgm_val) if qgm_val not in [None, ""] else INFINITY_VALUE
                qgn = float(qgn_val) if qgn_val not in [None, ""] else -INFINITY_VALUE

                bus_pl = bus.get("active_load")
                bus_ql = bus.get("reactive_load")
                pl = float(bus_pl) if bus_pl not in [None, ""] else 0.0
                ql = float(bus_ql) if bus_ql not in [None, ""] else 0.0

                bsh = (
                    float(bus.get("capacitor_reactor", 0.0)) / 100.0
                    if bus.get("capacitor_reactor")
                    else 0.0
                )
                vmx = DEFAULT_VMAX
                vmn = DEFAULT_VMIN

                line = f'{num:8} "{name:12}" {tb:2} {area:3} {v0:7.3f} {a0:8.2f} {pg0:10.3f} {qg0:8.3f} {pgm:8.2f} {pgn:10.2f} {qgm:10.2f} {qgn:10.2f} {pl:10.3f} {ql:10.3f} {bsh:10.4f} {vmx:9.3f} {vmn:9.3f}'
                dat_content.append(line)

        dat_content.append(";\n")

    # Process DLIN data (lines)
    if "DLIN" in result and result["DLIN"]:
        lines = result["DLIN"]

        # Create a set of connected bus numbers for quick lookup
        connected_buses = set()
        if "DBAR" in result and result["DBAR"]:
            for bus in result["DBAR"]:
                if bus.get("state", "L") == "L":  # Only connected buses
                    bus_num = bus.get("number")
                    if bus_num:
                        connected_buses.add(int(bus_num))

        dat_content.append("# AC circuits data (LTs and Transfos)")
        dat_content.append(
            "param: DLIN:       Tr         R          X       Bshl     Tap     Tmx     Tmn      Psh        Cn     :="
        )
        dat_content.append(
            "#    k     i     j          [pu]       [pu]       [pu]                           [grau]    [MVA]                     "
        )

        dlin_idx = 1  # Counter for valid DLIN entries
        for idx, line_data in enumerate(lines, 1):
            if line_data.get("state", "L") == "L":  # Only connected lines
                from_bus = (
                    int(line_data.get("from_bus", 0))
                    if line_data.get("from_bus")
                    else 0
                )
                to_bus = (
                    int(line_data.get("to_bus", 0)) if line_data.get("to_bus") else 0
                )
                # Check if both FROM and TO buses are connected
            if from_bus in connected_buses and to_bus in connected_buses:
                r = (
                    float(line_data.get("resistance", 0)) / 100.0
                    if line_data.get("resistance")
                    else 0
                )
                x = (
                    float(line_data.get("reactance", 0.0)) / 100.0
                    if line_data.get("reactance")
                    else 0.0
                )
                bshl = (
                    float(line_data.get("susceptance", 0.0)) / 100.0
                    if line_data.get("susceptance")
                    else 0.0
                )
                # Handle tap field according to your logic
                tap_val = line_data.get("tap")
                if tap_val is None or str(tap_val).isspace() or str(tap_val) == "":
                    tap = 0.0
                    tr = 0
                else:
                    tap = float(tap_val)
                    tr = 1
                tmx = (
                    float(line_data.get("tap_maximum", 0.0))
                    if line_data.get("tap_maximum")
                    else 0.0
                )
                tmn = (
                    float(line_data.get("tap_minimum", 0.0))
                    if line_data.get("tap_minimum")
                    else 0.0
                )
                psh = (
                    float(line_data.get("phase_shift", 0.0))
                    if line_data.get("phase_shift")
                    else 0.0
                )
                cn = (
                    float(line_data.get("normal_capacity", INFINITY_VALUE))
                    if line_data.get("normal_capacity")
                    else 99999.0
                )

                line_str = f"{dlin_idx:6d} {from_bus:5d} {to_bus:5d} {tr:2d} {r:10.7f} {x:10.7f} {bshl:10.7f} {tap:7.4f} {tmx:7.4f} {tmn:7.4f} {psh:8.3f} {cn:8.2f}"
                dat_content.append(line_str)
                dlin_idx += 1  # Only increment for valid entrie

        dat_content.append(";\n")

    # Process DCER data (Static Reactive Compensators)
    if "DCER" in result and result["DCER"]:
        dcer_data = result["DCER"]

        # Create a set of connected bus numbers for quick lookup
        connected_buses = set()
        if "DBAR" in result and result["DBAR"]:
            for bus in result["DBAR"]:
                if bus.get("state", "L") == "L":  # Only connected buses
                    bus_num = bus.get("number")
                    if bus_num:
                        connected_buses.add(int(bus_num))

        dat_content.append("# Static reactive compensator (SVC) data")
        dat_content.append(
            "param: DCER:   Nbc    Kb       Incl      Qcn       Qcm  Ccer :="
        )
        dat_content.append(
            "#                                      [MVAr]    [MVAr]        "
        )

        dcer_idx = 1  # Counter for valid DCER entries
        for dcer in dcer_data:
            if dcer.get("state", "L") == "L":
                bus = int(dcer.get("bus", 0)) if dcer.get("bus") else 0
                if bus in connected_buses:
                    controlled_bus = (
                        int(dcer.get("controlled_bus", 0))
                        if dcer.get("controlled_bus")
                        else 0
                    )
                    # Given in %
                    slope = (
                        float(dcer.get("slope", 0.0)) / 100.0
                        if dcer.get("slope")
                        else 0.0
                    )
                    qmin = (
                        float(dcer.get("min_reactive_generation", -INFINITY_VALUE))
                        if dcer.get("min_reactive_generation")
                        else -INFINITY_VALUE
                    )
                    qmax = (
                        float(dcer.get("max_reactive_generation", INFINITY_VALUE))
                        if dcer.get("max_reactive_generation")
                        else INFINITY_VALUE
                    )
                    control_mode = dcer.get("control_mode", "").strip()
                    if control_mode == "" or control_mode == "I":
                        ccer = 0
                    else:
                        ccer = 1

                    line_str = f"{dcer_idx:8d} {bus:9d} {controlled_bus:5d} {slope:10.7f} {qmin:9.2f} {qmax:9.2f} {ccer:4d}"
                    dat_content.append(line_str)
                    dcer_idx += 1

        dat_content.append(";\n")

    # Process DCSC data (Controllable Series Compensators)
    if "DCSC" in result and result["DCSC"]:
        dcsc_data = result["DCSC"]

        dat_content.append("# Controlable series compensator (CSC) data")
        dat_content.append(
            "param: DCSC:            Xmin       Xmax  Ccsc      Xesp      Cnc :="
        )
        dat_content.append(
            "#    k     i     j       [pu]       [pu]            [pu]    [MVA]"
        )

        for idx, dcsc in enumerate(dcsc_data, 1):
            if dcsc.get("state", "L") == "L":  # Only connected devices
                from_bus = int(dcsc.get("from_bus", 0)) if dcsc.get("from_bus") else 0
                to_bus = int(dcsc.get("to_bus", 0)) if dcsc.get("to_bus") else 0
                # Convert reactance from % to pu (divide by 100)
                min_x = (
                    float(dcsc.get("min_reactance", 0.0)) / 100.0
                    if dcsc.get("min_reactance")
                    else -0.0
                )
                max_x = (
                    float(dcsc.get("max_reactance", 0.0)) / 100.0
                    if dcsc.get("max_reactance")
                    else 0.0
                )
                init_x = (
                    float(dcsc.get("initial_reactance", 0.0)) / 100.0
                    if dcsc.get("initial_reactance")
                    else 0.0
                )

                # if string == ' ': Ctrlcsc.append(3)
                # elif string == 'X': Ctrlcsc.append(3)
                # elif string == 'I': Ctrlcsc.append(2)
                # elif string == 'P': Ctrlcsc.append(1)
                control_mode = dcsc.get("control_mode", "").strip()
                if control_mode == "" or control_mode == "X":
                    ccsc = 3
                elif control_mode == "I":
                    ccsc = 2
                elif control_mode == "P":
                    ccsc = 1
                else:
                    ccsc = 3  # Default to 3 for unknown values

                # Cnc appears to be capacity - using 99999 as default
                cnc = (
                    float(dcsc.get("dcsc_capacity", 0.0))
                    if dcsc.get("dcsc_capacity")
                    else 99999.0
                )

                line_str = f"{idx:5d} {from_bus:5d} {to_bus:5d} {min_x:10.7f} {max_x:10.7f} {ccsc:4d} {init_x:10.7f} {cnc:8.2f}"
                dat_content.append(line_str)

        dat_content.append(";\n")

    return "\n".join(dat_content)


def validate_input_file(file_path: str) -> Path:
    """Validate that input file exists.

    Args:
        file_path: Path to the input file

    Returns:
        Path object for the validated file

    Raises:
        SystemExit: If file doesn't exist
    """
    pwf_path = Path(file_path)
    if not pwf_path.exists():
        print(f"Error: File '{pwf_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    return pwf_path
