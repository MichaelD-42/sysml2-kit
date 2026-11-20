package EDriveSystemTests {
    doc /* V: system test cases, each verifying system requirements. */

    private import EDriveRequirements::*;

    verification <'EDU-STC-001'> continuousPowerTest {
        doc /* Run each motor variant on the dynamometer at rated power for 30 min; pass if shaft power stays at 50 kW or 80 kW. */
        objective { verify continuousPower; }
    }
    verification <'EDU-STC-002'> recoveryPowerTest {
        doc /* Drive the dynamometer in generator mode; pass if at least 30 kW reaches the battery emulator. */
        objective { verify recoveryPower; }
    }
    verification <'EDU-STC-003'> torqueStepTest {
        doc /* Send torque request steps on CAN; pass if measured torque settles within 10 ms. */
        objective { verify torqueResponse; }
    }
    verification <'EDU-STC-004'> mountingFitCheck {
        doc /* Bolt each variant to the reference subframe; pass if all four M12 points fit without shims. */
        objective { verify commonMounting; }
    }
}
