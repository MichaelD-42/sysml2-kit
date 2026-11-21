package VehiclePhysical {
    doc /* P layer: the parts that are built or bought, one engineering domain each, with the
     * logical components allocated to them. Drive parts come from the e-drive platform. */

    private import Trace::*;
    private import VehicleLogical::*;
    private import EDrivePhysical::*;

    // selects the platform's 80 kW motor variant for this vehicle
    #Electrical part <'PC-001'> driveMotor :> motor::motor80kW { doc /* Platform motor, 80 kW variant. */ }
    #Electrical part <'PC-002'> tractionBattery { doc /* 60 kWh lithium-ion battery pack. */ }
    #Mechanical part <'PC-003'> body { doc /* Steel body-in-white with five seats. */ }
    #Mechanical part <'PC-004'> ladderFrame { doc /* Steel ladder frame with four welded tie-down eyes. */ }

    allocate vehicle.powertrain.inverter to inverter;
    allocate vehicle.powertrain.motor to driveMotor;
    allocate vehicle.energyStore to tractionBattery;
    allocate vehicle.cabin to body;
    allocate vehicle.chassis to ladderFrame;
}
