# ---LICENSE---------------------
"""
    Copyright 2016-2026 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of the TMG Toolbox.

    The TMG Toolbox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The TMG Toolbox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the TMG Toolbox.  If not, see <http://www.gnu.org/licenses/>.
"""

# ---METADATA------------------
"""
Create Extra Attributes

    Creates or initializes a set of extra attributes in an EMME scenario.
"""

import math as _math
import traceback as _traceback
import inro.modeller as _m

_MODELLER = _m.Modeller()
_DOMAINS = {
    0: "LINK",
    1: "NODE",
    2: "TRANSIT_LINE",
    3: "TRANSIT_SEGMENT",
}


class CreateExtraAttributes(_m.Tool()):
    version = "1.0.0"

    def __call__(self, parameters: dict) -> None:
        self.run_xtmf(parameters)

    def run_xtmf(self, parameters: dict) -> None:
        try:
            self._execute(parameters)
        except Exception:
            raise Exception(_traceback.format_exc())

    def _execute(self, parameters: dict) -> None:
        scenario_number = parameters["scenario_number"]
        definitions = self._validate_definitions(parameters.get("attributes"))
        scenario = _MODELLER.emmebank.scenario(str(scenario_number))
        if scenario is None:
            raise ValueError("Scenario %s was not found." % scenario_number)

        for definition in definitions:
            attribute_id = definition["id"]
            domain = definition["domain"]
            default_value = definition["default_value"]
            reset_to_default = definition["reset_to_default"]
            existing = scenario.extra_attribute(attribute_id)

            if existing is None:
                scenario.create_extra_attribute(domain, attribute_id, default_value)
            elif existing.type != domain:
                scenario.delete_extra_attribute(attribute_id)
                scenario.create_extra_attribute(domain, attribute_id, default_value)
            elif reset_to_default:
                existing.initialize(default_value)

    def _validate_definitions(self, definitions: object) -> list:
        if not isinstance(definitions, list) or not definitions:
            raise ValueError("At least one extra attribute definition is required.")

        validated = []
        seen_ids = set()
        for index, definition in enumerate(definitions):
            if not isinstance(definition, dict):
                raise ValueError("Extra attribute definition %s must be an object." % index)

            attribute_id = definition.get("id")
            if not isinstance(attribute_id, str) or not attribute_id.strip():
                raise ValueError("Extra attribute definition %s must have a non-empty ID." % index)
            if attribute_id in seen_ids:
                raise ValueError("Extra attribute ID '%s' was specified more than once." % attribute_id)
            seen_ids.add(attribute_id)

            domain_value = definition.get("domain")
            if isinstance(domain_value, bool) or not isinstance(domain_value, int) or domain_value not in _DOMAINS:
                raise ValueError("Extra attribute '%s' has an invalid domain value." % attribute_id)
            domain = _DOMAINS[domain_value]

            default_value = definition.get("default_value")
            if isinstance(default_value, bool) or not isinstance(default_value, (int, float)):
                raise ValueError("Extra attribute '%s' must have a numeric default value." % attribute_id)
            default_value = float(default_value)
            if not _math.isfinite(default_value):
                raise ValueError("Extra attribute '%s' must have a finite default value." % attribute_id)

            reset_to_default = definition.get("reset_to_default")
            if not isinstance(reset_to_default, bool):
                raise ValueError("Extra attribute '%s' must specify reset_to_default as a boolean." % attribute_id)

            validated.append({
                "id": attribute_id,
                "domain": domain,
                "default_value": default_value,
                "reset_to_default": reset_to_default,
            })

        return validated
