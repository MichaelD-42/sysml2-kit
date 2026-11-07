package VehicleRequirements {
    doc /* R layer: what the vehicle shall do, derived from customer requirements. */

    private import Trace::*;

    requirement <'SR-001'> range {
        @Satisfies { need = "CRS-001"; }
        doc /* The vehicle shall drive at least 120 km on one battery charge. */
    }
    requirement <'SR-002'> seating {
        @Satisfies { need = "CRS-001"; }
        doc /* The vehicle shall seat five occupants including the driver. */
    }
    requirement <'SR-003'> curbMass {
        @Satisfies { need = "CRS-002"; }
        doc /* The vehicle curb mass shall not exceed 1800 kg. */
    }
    requirement <'SR-004'> tieDownPoints {
        @Satisfies { need = "CRS-002"; }
        doc /* The vehicle shall provide four tie-down points rated for 1000 kg each. */
    }
}
