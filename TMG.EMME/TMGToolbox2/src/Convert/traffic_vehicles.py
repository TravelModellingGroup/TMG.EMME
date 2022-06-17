# ---LICENSE----------------------
"""
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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

import inro.modeller as _m
import csv
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class TransitVehicle():
    """
    The base class that stores the transit vehicle data 
    """
    def __init__(self, desc, code, mode, seat_cap, total_cap, auto_equi, network):
        self.description = desc  
        self.code = code
        self.mode = mode
        self.seated_capacity = seat_cap
        self.total_capacity = total_cap
        self.auto_equivalent = auto_equi
        self.network = network

    def copy_data(self, id):
        """
        function to change the value and convert the ncs16 standard to ncs22.
        """
        # first extract the transit vehicle object using the id
        vehicle_object = self.network.transit_vehicle(int(id))
        # change the values of the vehicle object
        vehicle_object.description = self.code
        vehicle_object.seated_capacity = int(self.seated_capacity)
        vehicle_object.total_capacity = int(self.total_capacity)
        vehicle_object.auto_equivalent = float(self.auto_equivalent)
    
    def __get__(self):
        # used for outputting a print statement of the class if need be
        return self.description, self.code, self.mode, self.seated_capacity, self.total_capacity, self.auto_equi



# code for transit vehicle changes
def filter_mode(self, value, network):
    """
    extract the id of the vehicles from the transit vehicles list
    this is used to filter the transit vehicle to change the data
    """
    for i in network.transit_vehicles():
        if value == i.description:
            return i.id
    return None
 
def update_transit_vehicle_definitions(self, scenario, parameters, network):
    """
    function to read the csv file 
    it also runs the change_data() method to change the data
    """
    with open(parameters["transit_vehicle_definitions"], mode="r") as trans_veh:
        transit_op_file = csv.reader(trans_veh)
        next(transit_op_file)
        for item in transit_op_file:
            #get the vehicle id using the ncs16 standard code
            id = self.filter_mode(item[1].strip(), network)
            #save the data as a vehicle dictionary
            nc22_data = TransitVehicle(item[0], item[6].strip(), item[7].strip(), item[8].strip(),
                                        item[9].strip(), item[10].strip(), network)
            #change the value
            nc22_data.copy_data(id)

