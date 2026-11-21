package VehicleRequirements {
    doc /* R layer: what the vehicle shall do, derived from customer requirements. */

    private import Trace::*;
    private import ISQ::*;
    private import SI::*;

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
    // states the gap of the partial match: the 80 kW platform motor does not reach the customer's 8 s
    requirement <'SR-005'> acceleration {
        @Satisfies { need = "CRS-003"; }
        doc /* The vehicle shall accelerate from 0 to 100 km/h in at most 10 s. */
        subject vehicle;
        attribute accelerationTime : TimeValue;
        require constraint { accelerationTime <= 10 [s] }
    }
}
