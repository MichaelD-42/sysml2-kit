package SeatSwitchSystemTests {
    doc /* V: system test cases, each verifying system requirements or platform constraints.
     * Environmental tests follow the supplier's qualification plan QP-SSW-01. */

    private import Trace::*;
    private import SeatSwitchRequirements::*;

    verification <'SSW-STC-001'> adjustmentDirectionTest {
        doc /* Push the cushion and backrest knob parts and the lumbar pad in each of the ten directions on the HIL bench; pass if each yields its own request on LIN while held and none after release. */
        objective { verify adjustmentDirections; }
    }
    verification <'SSW-STC-002'> comfortKeyTest {
        doc /* Press each comfort key of each button set repeatedly; pass if the level steps up once per press and wraps to off. */
        objective { verify comfortKeySteps; }
    }
    verification <'SSW-STC-003'> nightDesignTest {
        doc /* Send dimming levels 0 to 100 % on LIN; pass if symbol brightness follows within 100 ms. */
        objective { verify nightDesign; }
    }
    verification <'SSW-STC-004'> keyStateLatencyTest {
        doc /* Actuate keys with a robot finger and log LIN; pass if every changed state is sent within 20 ms. */
        objective { verify keyStateLatency; }
    }
    verification <'SSW-STC-005'> faultMemoryTest {
        doc /* Hold a key for 35 s, then read the fault memory with the diagnostic tester; pass if the stuck-key code is reported. */
        objective { verify faultMemory; }
    }
    verification <'SSW-STC-006'> secureBootTest {
        doc /* Flash an unsigned and a wrongly signed image; pass if the switch keeps running the previous image both times. */
        objective { verify signedFirmware; }
    }
    verification <'SSW-STC-007'> securityAccessTest {
        doc /* Send write and flash requests without authentication, with an expired, a foreign and a valid tester certificate; pass if only the last is accepted. */
        objective { verify protectedWrite; }
    }
    verification <'SSW-STC-008'> endOfLineTest {
        doc /* Run the end-of-line sequence on each button set; pass if every key and LED is reported and the coded set's keys alone are active. */
        objective { verify endOfLineTestMode; verify variantCoding; }
    }
    verification <'SSW-STC-009'> mirroredMountingCheck {
        doc /* Try to fit each housing into both trim openings; pass if each fits its own side only. */
        objective { verify mirroredMounting; }
    }
    verification <'SSW-STC-010'> hapticMeasurement {
        @Verifies { need = "SSW-CON-001"; }
        @Verifies { need = "SSW-CON-002"; }
        doc /* Record force-travel curves of every key and direction on 10 samples; pass if force is 3.5 N to 6.0 N and travel 0.3 mm to 1.2 mm. */
    }
    verification <'SSW-STC-011'> luminanceMeasurement {
        @Verifies { need = "SSW-CON-003"; }
        doc /* Measure each lit symbol at full dimming level in a dark room; pass at 10 cd/m² to 30 cd/m². */
    }
    verification <'SSW-STC-012'> keyDurabilityTest {
        @Verifies { need = "SSW-CON-004"; }
        doc /* Actuate every key and direction 200 000 times at room temperature and at the temperature limits; pass if force and function stay in limits. */
    }
    verification <'SSW-STC-013'> supplyVoltageTest {
        @Verifies { need = "SSW-CON-005"; }
        doc /* Run all functions at 9 V, 13.5 V and 16 V supply; pass if every function works at each. */
    }
    verification <'SSW-STC-014'> temperatureTest {
        @Verifies { need = "SSW-CON-006"; }
        doc /* Operate the switch in a climate chamber at -40 °C and +85 °C; pass if every function works at both. */
    }
    verification <'SSW-STC-015'> ingressTest {
        @Verifies { need = "SSW-CON-007"; }
        doc /* Expose the mounted switch to dust and to splash water per IP5K4; pass if no dust or water reaches the PCB and every function works. */
    }
    verification <'SSW-STC-016'> esdTest {
        @Verifies { need = "SSW-CON-008"; }
        doc /* Discharge ±8 kV contact and ±15 kV air on every touchable surface, powered and unpowered; pass without reset or damage. */
    }
    verification <'SSW-STC-017'> linConformanceTest {
        @Verifies { need = "SSW-CON-009"; }
        doc /* Run the LIN 2.2A protocol conformance test suite; pass if every case passes. */
    }
    verification <'SSW-STC-018'> endOfLineCycleTimeTest {
        @Verifies { need = "SSW-CON-010"; }
        doc /* Run 50 switches of each button set through the end-of-line station; pass if no test cycle exceeds 12 s. */
    }
    verification <'SSW-STC-019'> markingInspection {
        @Verifies { need = "SSW-CON-011"; }
        doc /* Read the Data Matrix of 50 switches with the line scanner after the temperature test; pass if every code reads at grade B or better per SSW-PRD-04. */
    }
    verification <'SSW-STC-020'> workshopReflashTest {
        @Verifies { need = "SSW-CON-012"; }
        doc /* With the workshop tester on the vehicle LIN, read the fault memory, reflash, and read it again; pass if the sequence takes at most 120 s. */
    }
    verification <'SSW-STC-021'> sideKeyedAssemblyCheck {
        doc /* Try to assemble each housing with the knob carrier and keymat of the other side; pass if no combination can be assembled. */
        objective { verify sideKeyedAssembly; }
    }
}
