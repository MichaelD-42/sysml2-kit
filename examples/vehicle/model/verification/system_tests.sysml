package VehicleSystemTests {
    doc /* V: system test cases, each verifying system requirements. */

    private import VehicleRequirements::*;

    verification <'STC-001'> rangeTest {
        doc /* Drive the WLTP cycle from full charge until shutdown; record distance. */
        objective { verify range; }
    }
    verification <'STC-002'> seatCount {
        doc /* Inspect seating positions and belts. */
        objective { verify seating; }
    }
    verification <'STC-003'> weighing {
        doc /* Weigh the vehicle in curb condition on a calibrated scale. */
        objective { verify curbMass; }
    }
    verification <'STC-004'> tieDownPullTest {
        doc /* Pull-test each tie-down point to 1000 kg. */
        objective { verify tieDownPoints; }
    }
}
