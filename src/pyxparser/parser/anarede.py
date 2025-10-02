"""ANAREDE parser implementation."""

import json
from pathlib import Path
from typing import Any, Dict, Type, Union

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
                "DBAR": [],
                "DLIN": [],
                "DGER": [],
                "DCSC": [],
                "DCER": [],
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

                    # Skip empty lines and comment lines (lines starting with parentheses)
                    if not line.strip() or line.strip().startswith("("):
                        continue

                    # Check for unsupported section headers
                    unsupported_sections = [
                        "TITU",
                        "DOPC",
                        "QLIM",
                        "DGLT",
                        "DARE",
                        "DGBT",
                        "DGGB",
                        "DTPF",
                        "DCAR",
                        "DMFL",
                        "DBSH",
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

                    # Parse data lines based on current section
                    try:
                        if current_section == "DBAR":
                            record = self.parse_dbar_record(line)
                            result["DBAR"].append(record)
                        elif current_section == "DLIN":
                            record = self.parse_dlin_record(line)
                            result["DLIN"].append(record)
                        elif current_section == "DGER":
                            record = self.parse_dger_record(line)
                            result["DGER"].append(record)
                        elif current_section == "DCSC":  # Add DCSC parsing
                            record = self.parse_dcsc_record(line)
                            result["DCSC"].append(record)
                        elif current_section == "DCER":  # Add DCER parsing
                            record = self.parse_dcer_record(line)
                            result["DCER"].append(record)
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

            logger.success(f"Successfully parsed ANAREDE file: {file_path}")
            logger.info(
                f"Parsed {len(result['DBAR'])} DBAR records, {len(result['DLIN'])} DLIN records, {len(result['DGER'])} DGER records, {len(result['DCSC'])} DCSC records, and {len(result['DCER'])} DCER records"
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
