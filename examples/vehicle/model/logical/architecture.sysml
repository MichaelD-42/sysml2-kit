package VehicleLogical {
    doc /* L layer: technology-independent components, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import VehicleFeatures::*;
    private import VehicleRequirements::*;

    part <'LC-001'> vehicle {
        doc /* The vehicle as a whole. */
        part <'LC-002'> powertrain {
            doc /* Produces traction from electrical power. */
            port <'LI-001'> powerIn;
            part <'LC-006'> inverter { doc /* Supplies the motor from the energy store. */ }
            part <'LC-007'> motor { doc /* Drives the wheels. */ }
        }
        part <'LC-003'> energyStore {
            doc /* Stores electrical energy. */
            port <'LI-002'> powerOut;
        }
        part <'LC-004'> cabin { doc /* Occupant compartment. */ }
        part <'LC-005'> chassis { doc /* Load-bearing structure. */ }

        connect energyStore.powerOut to powertrain.powerIn;
    }

    allocate propulsion.propel.convertPower to vehicle.powertrain.inverter;
    allocate propulsion.propel.produceTorque to vehicle.powertrain.motor;
    allocate travelRange.storeEnergy to vehicle.energyStore;
    allocate occupantSeating.carryOccupants to vehicle.cabin;
    allocate trailerTransport.secureForTransport to vehicle.chassis;

    satisfy range by vehicle.energyStore;
    satisfy seating by vehicle.cabin;
    satisfy curbMass by vehicle;
    satisfy tieDownPoints by vehicle.chassis;
    satisfy acceleration by vehicle.powertrain.motor;
}
