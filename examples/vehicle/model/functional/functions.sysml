package VehicleFunctions {
    doc /* F layer: what the vehicle does, independent of how it is built. */

    action <'F-001'> operateVehicle {
        doc /* Top-level vehicle function. */
        action <'F-002'> propel { doc /* Convert stored energy into traction. */ }
        action <'F-003'> storeEnergy { doc /* Store and deliver electrical energy. */ }
        action <'F-004'> carryOccupants { doc /* Seat and protect occupants. */ }
        action <'F-005'> secureForTransport { doc /* Provide attachment for transport restraints. */ }

        first storeEnergy then propel;
    }
}
