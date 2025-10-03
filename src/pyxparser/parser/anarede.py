"""ANAREDE parser implementation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Type, Union

from loguru import logger


class AnaredeParser:
    """ANAREDE file parser for electrical power system data."""

    def __init__(self) -> None:
        """Initialize the ANAREDE parser."""
        logger.info("ANAREDE parser initialized")
        self.field_mappings = self._load_field_mappings()

    def _load_field_mappings(self) -> Dict[str, Any]:
        """Load field mappings from JSON configuration."""
        mapping_file = (
            Path(__file__).parent.parent / "defaults" / "anarede_mapping.json"
        )
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                mappings: Dict[str, Any] = json.load(f)
                return mappings
        except FileNotFoundError:
            logger.warning(f"Mapping file not found: {mapping_file}")
            return {"DBAR": {"fields": {}}, "DLIN": {"fields": {}}}

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse an ANAREDE file.

        Args:
            file_path: Path to the ANAREDE file to parse

        Returns:
            Dictionary containing parsed data
        """
        logger.info(f"Starting to parse ANAREDE file: {file_path}")

        try:
            result: Dict[str, Any] = {
                "TITU": [],
                "DBAR": [],
                "DLIN": [],
                "DGER": [],
                "DCSC": [],
                "DCER": [],
                "DBSH": [],
                "metadata": {"file_path": str(file_path), "status": "parsed"},
            }

            with open(file_path, "r", encoding="utf-8") as f:
                current_section = None

                for line_num, line in enumerate(f, 1):
                    line = line.rstrip("\n\r")

                    # Check for end of file marker
                    if line.strip() == "FIM":
                        break

                    # Check for end of section marker
                    if line.strip() == "99999":
                        current_section = None
                        continue

                    # Check for section headers
                    if line.strip() == "TITU":
                        current_section = "TITU"
                        logger.debug("Starting TITU section")
                        continue
                    if line.strip() == "DBAR":
                        current_section = "DBAR"
                        logger.debug("Starting DBAR section")
                        continue
                    elif line.strip() == "DLIN":
                        current_section = "DLIN"
                        logger.debug("Starting DLIN section")
                        continue
                    elif line.strip() == "DGER":
                        current_section = "DGER"
                        logger.debug("Starting DGER section")
                        continue
                    elif line.strip() == "DCSC":
                        current_section = "DCSC"
                        logger.debug("Starting DCSC section")
                        continue
                    elif line.strip() == "DCER":
                        current_section = "DCER"
                        logger.debug("Starting DCER section")
                        continue
                    elif line.strip() == "DBSH":
                        current_section = "DBSH"
                        logger.debug("Starting DBSH section")
                        continue

                    # Skip empty lines and comment lines (lines starting with parentheses)
                    if not line.strip() or line.strip().startswith("("):
                        continue

                    # Check for unsupported section headers
                    unsupported_sections = [
                        "DOPC",
                        "QLIM",
                        "DGLT",
                        "DARE",
                        "DGBT",
                        "DGGB",
                        "DTPF",
                        "DCAR",
                        "DMFL",
                        "DCTR",
                        "DSHL",
                        "DMFL",
                        "DELO",
                        "DCBA",
                        "DCLI",
                        "DCNV",
                        "DCCV",
                    ]
                    if line.strip() in unsupported_sections:
                        current_section = line.strip()  # Use actual section name
                        logger.warning(
                            f"Skipping section '{current_section}' (not supported)"
                        )
                        continue

                    try:
                        if current_section == "TITU":
                            # TITU section: only take the first non-empty line after "TITU"
                            if (
                                line.strip()
                                and line.strip()
                                not in unsupported_sections
                                + ["DBAR", "DLIN", "DGER", "DCSC", "DCER", "DBSH"]
                            ):
                                result["TITU"].append(line.strip())
                                logger.debug(f"Case Title: {line.strip()}")
                                current_section = None
                            else:
                                current_section = None
                                continue
                        elif current_section == "DBAR":
                            record = self.parse_dbar_record(line)
                            result["DBAR"].append(record)
                        elif current_section == "DLIN":
                            record = self.parse_dlin_record(line)
                            result["DLIN"].append(record)
                        elif current_section == "DGER":
                            record = self.parse_dger_record(line)
                            result["DGER"].append(record)
                        elif current_section == "DCSC":
                            record = self.parse_dcsc_record(line)
                            result["DCSC"].append(record)
                        elif current_section == "DCER":
                            record = self.parse_dcer_record(line)
                            result["DCER"].append(record)
                        elif current_section == "DBSH":
                            # DBSH needs special handling - parse until FBAN, then continue
                            dbsh_data = self.parse_dbsh_section(f, line)
                            result["DBSH"].extend(dbsh_data)
                        elif current_section in unsupported_sections:
                            continue
                        elif current_section is None:
                            continue
                    except Exception as e:
                        logger.warning(
                            f"Error parsing line {line_num} in section {current_section}: {e}"
                        )
                        logger.debug(f"Problematic line: {line}")
                        continue

            if result["DBSH"]:
                logger.debug("Integrating DBSH shunt values into DBAR data")
                self._integrate_dbsh_into_dbar(result)

            if result["TITU"]:
                result["metadata"]["title"] = " ".join(result["TITU"])

            logger.success(f"Successfully parsed ANAREDE file: {file_path}")
            logger.info(
                f"Parsed {len(result['DBAR'])} DBAR, {len(result['DLIN'])} DLIN , "
                f"{len(result['DGER'])} DGER, {len(result['DCSC'])} DCSC, "
                f"{len(result['DCER'])} DCER, and {len(result['DBSH'])} DBSH records"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to parse ANAREDE file {file_path}: {e}")
            raise

    def parse_dbar_record(self, line: str) -> Dict[str, Any]:
        """Parse a DBAR (bus) record.

        Args:
            line: Line containing DBAR data

        Returns:
            Dictionary with parsed bus data
        """
        if len(line) < 20:
            raise ValueError(f"DBAR line too short: {line}")

        fields = self.field_mappings.get("DBAR", {}).get("fields", {})
        record: Dict[str, Any] = {}

        for field_name, field_config in fields.items():
            try:
                column_config = field_config.get("column", {})
                start = column_config.get("start", 1)
                end = column_config.get("end", 1)
                default = field_config.get("default", "")

                # Determine data type based on default value
                data_type: Type[Union[str, int, float]]
                if isinstance(default, int):
                    data_type = int
                elif isinstance(default, float):
                    data_type = float
                else:
                    data_type = str

                value = self._extract_field_value(line, start, end, data_type)
                record[field_name] = value if value != "" else default

            except Exception as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = field_config.get("default", "")

        return record

    def parse_dlin_record(self, line: str) -> Dict[str, Any]:
        """Parse a DLIN (line) record.

        Args:
            line: Line containing DLIN data

        Returns:
            Dictionary with parsed line data
        """
        if len(line) < 20:
            raise ValueError(f"DLIN line too short: {line}")

        fields = self.field_mappings.get("DLIN", {}).get("fields", {})
        record: Dict[str, Any] = {}

        for field_name, field_config in fields.items():
            try:
                column_config = field_config.get("column", {})
                start = column_config.get("start", 1)
                end = column_config.get("end", 1)
                default = field_config.get("default", "")

                # Determine data type based on default value
                data_type: Type[Union[str, int, float]]
                if isinstance(default, int):
                    data_type = int
                elif isinstance(default, float):
                    data_type = float
                else:
                    data_type = str

                value = self._extract_field_value(line, start, end, data_type)
                record[field_name] = value if value != "" else default

            except Exception as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = field_config.get("default", "")

        return record

    def parse_dger_record(self, line: str) -> Dict[str, Any]:
        """Parse a DGER (generator) record.

        Args:
            line: Line containing DGER data

        Returns:
            Dictionary with parsed generator data
        """
        if len(line) < 10:
            raise ValueError(f"DGER line too short: {line}")

        fields = self.field_mappings.get("DGER", {}).get("fields", {})
        record: Dict[str, Any] = {}

        for field_name, field_config in fields.items():
            try:
                column_config = field_config.get("column", {})
                start = column_config.get("start", 1)
                end = column_config.get("end", 1)
                default = field_config.get("default", "")

                # Determine data type based on default value
                data_type: Type[Union[str, int, float]]
                if isinstance(default, int):
                    data_type = int
                elif isinstance(default, float):
                    data_type = float
                else:
                    data_type = str

                value = self._extract_field_value(line, start, end, data_type)
                record[field_name] = value if value != "" else default

            except Exception as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = field_config.get("default", "")

        return record

    def parse_dcsc_record(self, line: str) -> Dict[str, Any]:
        """Parse a DCSC (Controllable Series Compensator) record.

        Args:
            line: Line containing DCSC data

        Returns:
            Dictionary with parsed DCSC data
        """
        if len(line) < 10:
            raise ValueError(f"DCSC line too short: {line}")

        fields = self.field_mappings.get("DCSC", {}).get("fields", {})
        record: Dict[str, Any] = {}

        for field_name, field_config in fields.items():
            try:
                column_config = field_config.get("column", {})
                start = column_config.get("start", 1)
                end = column_config.get("end", 1)
                default = field_config.get("default", "")

                # Determine data type based on default value
                data_type: Type[Union[str, int, float]]
                if isinstance(default, int):
                    data_type = int
                elif isinstance(default, float):
                    data_type = float
                else:
                    data_type = str

                value = self._extract_field_value(line, start, end, data_type)
                record[field_name] = value if value != "" else default

            except Exception as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = field_config.get("default", "")

        return record

    def parse_dcer_record(self, line: str) -> Dict[str, Any]:
        """Parse a DCER (Static Reactive Compensator) record.

        Args:
            line: Line containing DCER data

        Returns:
            Dictionary with parsed DCER data
        """
        if len(line) < 10:
            raise ValueError(f"DCER line too short: {line}")

        fields = self.field_mappings.get("DCER", {}).get("fields", {})
        record: Dict[str, Any] = {}

        for field_name, field_config in fields.items():
            try:
                column_config = field_config.get("column", {})
                start = column_config.get("start", 1)
                end = column_config.get("end", 1)
                default = field_config.get("default", "")

                # Determine data type based on default value
                data_type: Type[Union[str, int, float]]
                if isinstance(default, int):
                    data_type = int
                elif isinstance(default, float):
                    data_type = float
                else:
                    data_type = str

                value = self._extract_field_value(line, start, end, data_type)
                record[field_name] = value if value != "" else default

            except Exception as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = field_config.get("default", "")

        return record

    def parse_dbsh_section(self, file_handle, first_line: str) -> List[Dict[str, Any]]:
        """Parse DBSH (Shunt Banks) section with special multi-line format.

        Args:
            file_handle: File handle for reading additional lines
            first_line: First data line of DBSH section

        Returns:
            List of parsed DBSH records
        """
        dbsh_records: List[Dict[str, Any]] = []
        line = first_line

        while True:
            # Skip comment lines
            while line.startswith("("):
                line = file_handle.readline().rstrip("\n\r")

            # Check for section end
            if line.strip() == "99999" or line.strip() == "FIM":
                break

            # Check if line starts with a bus number (first 5 characters should be a number)
            try:
                cont = int(line[:5])
                if cont == 99999:
                    break
            except (ValueError, IndexError):
                line = file_handle.readline().rstrip("\n\r")
                continue

            # Parse main DBSH data line
            dbsh_record: Dict[str, Any] = {
                "from_bus": int(line[:5]),  # Bus number FROM
                "to_bus": None,  # Bus number TO
                "control_mode": "C",  # Default control mode
                "initial_reactive_injection": 0.0,
                "terminal_bus": None,
                "total_shunt": 0.0,  # Will accumulate from bank data
                "banks": [],  # Individual bank data
            }

            # Parse TO bus (columns 9-13)
            to_bus_str = line[8:13].strip()
            if to_bus_str and not to_bus_str.isspace():
                dbsh_record["to_bus"] = int(to_bus_str)

            # Parse control mode (column 18)
            control_mode_str = line[17:18].strip()
            if control_mode_str and not control_mode_str.isspace():
                dbsh_record["control_mode"] = control_mode_str

            # Parse initial reactive injection (columns 36-41)
            qini_str = line[35:41].strip()
            if qini_str and not qini_str.isspace():
                dbsh_record["initial_reactive_injection"] = float(qini_str)

            # Parse terminal bus (column 47 onwards)
            terminal_str = line[46:].strip()
            if terminal_str and not terminal_str.isspace():
                dbsh_record["terminal_bus"] = int(terminal_str)
            else:
                dbsh_record["terminal_bus"] = dbsh_record["from_bus"]

            # Read bank data until FBAN is found
            total_shunt = 0.0

            line = file_handle.readline().rstrip("\n\r")

            # Skip comment lines
            while line.startswith("("):
                line = file_handle.readline().rstrip("\n\r")

            # Process bank data lines until FBAN
            while not line.startswith("FBAN"):
                if line.strip() and not line.startswith("("):
                    try:
                        # Parse bank data
                        bank_data = {
                            "group_id": int(line[:2]) if line[:2].strip() else 1,
                            "state": line[6:7].strip() if line[6:7].strip() else "L",
                            "units_in_operation": int(line[12:15])
                            if line[12:15].strip()
                            else 1,
                            "unit_reactive_power": 0.0,
                        }

                        # Parse unit reactive power (column 17 onwards)
                        power_str = line[16:].split()[0] if line[16:].strip() else "0"
                        if power_str and not power_str.isspace():
                            bank_data["unit_reactive_power"] = float(power_str)

                        # Calculate contribution to total shunt
                        if bank_data["state"] == "L":  # Only if bank is connected
                            units_in_operation = int(bank_data["units_in_operation"])
                            unit_reactive_power = float(
                                bank_data["unit_reactive_power"]
                            )
                            bank_contribution = units_in_operation * unit_reactive_power
                            total_shunt += bank_contribution

                        dbsh_record["banks"].append(bank_data)

                    except (ValueError, IndexError) as e:
                        logger.debug(f"Error parsing DBSH bank line: {e}")

                line = file_handle.readline().rstrip("\n\r")

            dbsh_record["total_shunt"] = total_shunt
            dbsh_records.append(dbsh_record)

            line = file_handle.readline().rstrip("\n\r")
            if not line:
                break

            while line.startswith("("):
                line = file_handle.readline().rstrip("\n\r")
                if not line:
                    return dbsh_records

        return dbsh_records

    def _integrate_dbsh_into_dbar(self, result: Dict[str, Any]) -> None:
        """Integrate DBSH shunt values into DBAR bus data."""
        nbsh = len(result["DBSH"])  # Number of DBSH records
        nb = len(result["DBAR"])  # Number of DBAR records

        # Process each DBSH record (s loop: for s in range(1, nbsh + 1))
        for s in range(1, nbsh + 1):
            dbsh_record = result["DBSH"][s - 1]  # Convert to 0-based index

            # Extract values from DBSH record
            Debsh_s = dbsh_record.get("from_bus")  # Debsh[s-1]
            Extr_s = dbsh_record.get("terminal_bus")  # Extr[s-1]
            Sht_s = dbsh_record.get("total_shunt", 0.0)  # Sht[s-1]

            # Find matching bus in DBAR (k loop: for k in range(1, nb + 1))
            flag = 0
            k_found = None

            for k in range(1, nb + 1):
                dbar_record = result["DBAR"][k - 1]  # Convert to 0-based index
                Num_k = dbar_record.get("number")  # Num[k-1]

                # Check if bus numbers match: if Num[k - 1] == Extr[s - 1]
                if Num_k and int(Num_k) == Extr_s:
                    flag = 1
                    k_found = k
                    break

            # Handle error case: if flag == 0
            if flag == 0 or k_found is None:
                logger.warning(f"* Error in bus {Debsh_s} of BSH {s}.")
                continue  # Skip this DBSH record

            # Add shunt to capacitor_reactor field: Sh[k - 1] = Sh[k - 1] + Sht[s - 1]
            dbar_index = k_found - 1  # Convert back to 0-based index
            current_capacitor_reactor = result["DBAR"][dbar_index].get(
                "capacitor_reactor", 0.0
            )

            # Handle string values and convert to float
            if isinstance(current_capacitor_reactor, str):
                try:
                    current_capacitor_reactor = float(current_capacitor_reactor)
                except ValueError:
                    current_capacitor_reactor = 0.0

            # Update the capacitor_reactor field (this is Sh[k-1] in the original code)
            new_capacitor_reactor = current_capacitor_reactor + Sht_s
            result["DBAR"][dbar_index]["capacitor_reactor"] = new_capacitor_reactor

            logger.debug(
                f"BSH {s}: Added shunt {Sht_s} to bus {Extr_s} "
                f"(DBAR {k_found}), total shunt val: {new_capacitor_reactor}"
            )

        logger.info(f"Integrated {nbsh} DBSH records into {nb} DBAR records")

    def _extract_field_value(
        self, line: str, start: int, end: int, data_type: Type[Union[str, int, float]]
    ) -> Union[str, int, float]:
        """Extract and convert field value from line.

        Args:
            line: Source line
            start: Start position (1-based)
            end: End position (1-based)
            data_type: Target data type

        Returns:
            Converted value
        """
        # Convert to 0-based indexing
        start_idx = start - 1
        end_idx = end

        # Extract raw value
        if end_idx <= len(line):
            raw_value = line[start_idx:end_idx].strip()
        else:
            raw_value = line[start_idx:].strip()

        if not raw_value:
            return ""

        try:
            if data_type is str:
                return raw_value
            elif data_type is int:
                return int(raw_value)
            elif data_type is float:
                return float(raw_value)
        except ValueError:
            return ""

        return ""
