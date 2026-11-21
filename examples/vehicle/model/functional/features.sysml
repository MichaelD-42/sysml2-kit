package VehicleFeatures {
    doc /* F layer: what the vehicle offers (features, noun names) and the functions each feature
     * owns, independent of how they are built. */

    private import Trace::*;

    #Feature action <'FEAT-001'> travelRange {
        @Matches { need = "CRS-001"; }
        doc /* Distance on one battery charge. */
        action <'F-003'> storeEnergy { doc /* Store and deliver electrical energy. */ }
    }

    #Feature action <'FEAT-002'> propulsion {
        @Matches { need = "CRS-001"; }
        @Matches { need = "CRS-003"; partial = true; }
        doc /* Traction from stored electrical energy. */
        action <'F-002'> propel {
            doc /* Convert stored energy into traction. */
            action <'F-006'> convertPower { doc /* Turn battery power into motor power. */ }
            action <'F-007'> produceTorque { doc /* Turn motor power into wheel torque. */ }
            first convertPower then produceTorque;
        }
    }

    #Feature action <'FEAT-003'> occupantSeating {
        @Matches { need = "CRS-001"; }
        doc /* Seats for the driver and four passengers. */
        action <'F-004'> carryOccupants { doc /* Seat and protect occupants. */ }
    }

    #Feature action <'FEAT-004'> trailerTransport {
        @Matches { need = "CRS-002"; }
        doc /* Carriage of the vehicle on a car trailer. */
        action <'F-005'> secureForTransport { doc /* Provide attachment for transport restraints. */ }
    }
}
