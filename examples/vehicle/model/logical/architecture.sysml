package VehicleLogical {
    doc /* L layer: technology-independent components, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import VehicleFunctions::*;
    private import VehicleRequirements::*;

    part <'LC-001'> vehicle {
        doc /* The vehicle as a whole. */
        part <'LC-002'> powertrain {
            doc /* Produces traction from electrical power. */
            port <'LI-001'> powerIn;
        }
        part <'LC-003'> energyStore {
            doc /* Stores electrical energy. */
            port <'LI-002'> powerOut;
        }
        part <'LC-004'> cabin { doc /* Occupant compartment. */ }
        part <'LC-005'> chassis { doc /* Load-bearing structure. */ }

        connect energyStore.powerOut to powertrain.powerIn;
    }

    allocate operateVehicle.propel to vehicle.powertrain;
    allocate operateVehicle.storeEnergy to vehicle.energyStore;
    allocate operateVehicle.carryOccupants to vehicle.cabin;
    allocate operateVehicle.secureForTransport to vehicle.chassis;

    satisfy range by vehicle.energyStore;
    satisfy seating by vehicle.cabin;
    satisfy curbMass by vehicle;
    satisfy tieDownPoints by vehicle.chassis;
}
