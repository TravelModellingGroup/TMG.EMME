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

import  csv
m = inro.modeller.Modeller()
databank = m.emmebank
scenario_one = databank.scenario(1)
scenario_two = databank.scenario(2)
scenario = databank.scenario(scenario_one)
network = scenario.get_network()

# ToDo: We need to move the traffic vehicle class and functions into here
# since the original code is too cluttered 
# main issue is that this folder the convert folder isn't in the system path folder 
# so importing this module crashes in python

class TransitVehicle():
    """
    The base class that stores the transit vehicle data 
    """
    def __init__(self, desc, code, mode, seat_cap, total_cap, auto_equi):
        self.description = desc  
        self.code = code
        self.mode = mode
        self.seated_capacity = seat_cap
        self.total_capacity = total_cap
        self.auto_equivalent = auto_equi
    
    def __get__(self):
        # used for outputting a print statement of the class if need be
        return self.description, self.code, self.mode, self.seated_capacity, self.total_capacity, self.auto_equi




    # code for transit vehicle changes
    def filtermode(self, value, network):
        """
        extract the id of the vehicles from the transit vehicles list
        this is used to filter the transit vehicle to change the data
        """
        for i in network.transit_vehicles():
            if value == i.description:
                return i.id

    def change_data(self, id, vehicle_property ,value1, value2, network):
        """
        function to change the value and convert the ncs16 standard to ncs22.
        """
        if value1 == value2:
            pass
        else:
            # change the transit vehicle
            vehicle_object = network.transit_vehicle(int(id))
            print('they are different ', repr(id), repr(vehicle_property), repr(value1), repr(value2), vehicle_object)
            print(vehicle_object.id, vehicle_object.mode, vehicle_object.number, vehicle_object.description, vehicle_object.total_capacity)
            if vehicle_property == "code":
                if value1 != value2:
                    vehicle_object.code = value2
                    print('new code: ', vehicle_object.code)
            if vehicle_property == "mode":
                if value1 != value2:
                    vehicle_object.mode = value2
                    print('new mode: ', vehicle_object.mode)
            if vehicle_property == "seated_capacity":
                if value1 != value2:
                    vehicle_object.seated_capacity = int(value2)
                    print('new seated capacity: ', vehicle_object.seated_capacity)
            if vehicle_property == "total_capacity":
                if value1 != value2:
                    vehicle_object.total_capacity = int(value2)
                    print('new total capacity: ', vehicle_object.total_capacity)
            if vehicle_property == "auto_equivalent":
                if value1 != value2:
                    vehicle_object.auto_equivalent = int(value2)
                    print('new auto equi: ', vehicle_object.auto_equivalent)
 
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
                id = self.filtermode(item[1].strip(), network)
                print("id, list and len ", id, item, len(item))
                #save the data as a vehicle dictionary
                nc16_data = TransitVehicle(item[0], item[1].strip(), item[2].strip(), item[3].strip(), item[4].strip(), item[5].strip())
                nc22_data = TransitVehicle(item[0], item[6].strip(), item[7].strip(), item[8].strip(), item[9].strip(), item[10].strip())
            
                #change the value
                self.change_data(id, "code", nc16_data.code, nc22_data.code, network)
                self.change_data(id, "mode", nc16_data.mode, nc22_data.mode, network)
                self.change_data(id, "seated_capacity", nc16_data.seated_capacity, nc22_data.seated_capacity, network)
                self.change_data(id, "total_capacity", nc16_data.total_capacity, nc22_data.total_capacity, network)
                self.change_data(id, "auto_equivalent", nc16_data.auto_equivalent, nc22_data.auto_equivalent, network)
       
def main():
    readFile()
