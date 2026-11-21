package VehiclePhysical {
    doc /* P layer: the parts that are built or bought, one engineering domain each, with the
     * logical components allocated to them. Drive parts come from the e-drive platform. */

    private import Trace::*;
    private import VehicleLogical::*;
    private import EDrivePhysical::*;
    private import EDriveItems::*;

    #Electrical part <'PC-002'> tractionBattery {
        doc /* 60 kWh lithium-ion battery pack. */
        port hvOut : HighVoltagePort;
    }
    #Mechanical part <'PC-003'> body { doc /* Steel body-in-white with five seats. */ }
    #Mechanical part <'PC-004'> ladderFrame {
        doc /* Steel ladder frame with four welded tie-down eyes. */
        port driveMount : ~MountPort;
    }

    part vehicleAssembly {
        doc /* The vehicle as assembled: the platform drive unit wired, cooled and mounted. */
        part driveUnit :> eDriveUnit {
            doc /* The platform drive unit fitted to this vehicle. */
            // selects the platform's 80 kW motor variant for this vehicle
            #Electrical part <'PC-001'> driveMotor :> EDrivePhysical::motor::motor80kW { doc /* Platform motor, 80 kW variant. */ }
        }
        ref part tractionBattery :> VehiclePhysical::tractionBattery;
        ref part ladderFrame :> VehiclePhysical::ladderFrame;
        part vehicleControlUnit {
            doc /* Vehicle control unit that sends the driver's torque request. */
            port canOut : CanPort;
        }
        part coolingCircuit {
            doc /* Low-temperature coolant loop with pump and radiator. */
            port supply : CoolantPort;
            port returnLine : ~CoolantPort;
        }

        interface : HighVoltageInterface connect tractionBattery.hvOut to driveUnit.hvIn;
        interface : CanInterface connect vehicleControlUnit.canOut to driveUnit.canBus;
        interface : CoolantInterface connect coolingCircuit.supply to driveUnit.coolantIn;
        interface : CoolantInterface connect driveUnit.coolantOut to coolingCircuit.returnLine;
        interface : MountInterface connect ladderFrame.driveMount to driveUnit.mount;
    }

    allocate vehicle.powertrain.inverter to inverter;
    allocate vehicle.powertrain.motor to vehicleAssembly.driveUnit.driveMotor;
    allocate vehicle.energyStore to tractionBattery;
    allocate vehicle.cabin to body;
    allocate vehicle.chassis to ladderFrame;
}
