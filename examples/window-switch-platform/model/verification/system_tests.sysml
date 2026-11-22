package WindowSwitchSystemTests {
    doc /* V: system test cases, each verifying system requirements or platform constraints.
     * Environmental tests follow the supplier's qualification plan QP-WSW-01. */

    private import Trace::*;
    private import WindowSwitchRequirements::*;

    verification <'WSW-STC-001'> keyStageTest {
        doc /* Move every window key of each key module to both stages on the HIL bench; pass if each stage yields its own state on LIN while held and released after. */
        objective { verify windowKeyStages; }
    }
    verification <'WSW-STC-002'> childLockTest {
        doc /* Press the child-lock key and toggle the received child-lock state; pass if each press yields one toggle request and the telltale follows the state. */
        objective { verify childLockToggle; }
    }
    verification <'WSW-STC-003'> nightDesignTest {
        doc /* Send dimming levels 0 to 100 % on LIN; pass if symbol brightness follows within 100 ms. */
        objective { verify nightDesign; }
    }
    verification <'WSW-STC-004'> keyStateLatencyTest {
        doc /* Actuate keys with a robot finger and log LIN; pass if every changed stage is sent within 20 ms. */
        objective { verify keyStateLatency; }
    }
    verification <'WSW-STC-005'> linConformanceTest {
        @Verifies { need = "WSW-CON-006"; }
        doc /* Run the LIN 2.2A conformance test suite, with requests to the switch's and to foreign node addresses; pass if every case passes. */
        objective { verify nodeAddressing; }
    }
    verification <'WSW-STC-006'> framePlausibilityTest {
        doc /* On the HIL bench, send frames with a wrong checksum, and command frames with a repeated alive counter or a signal out of range; pass if the switch discards each and acts on the next valid frame. */
        objective { verify framePlausibility; }
    }
    verification <'WSW-STC-007'> hapticMeasurement {
        @Verifies { need = "WSW-CON-001"; }
        doc /* Record force-travel curves of every key on 10 samples; pass if the first-stage force is 3.5 N to 7.0 N. */
    }
    verification <'WSW-STC-008'> keyDurabilityTest {
        @Verifies { need = "WSW-CON-002"; }
        doc /* Actuate every key 100 000 times per stage at room temperature and at the temperature limits; pass if force and function stay in limits. */
    }
    verification <'WSW-STC-009'> supplyVoltageTest {
        @Verifies { need = "WSW-CON-003"; }
        doc /* Run all functions at 9 V, 13.5 V and 16 V supply; pass if every function works at each. */
    }
    verification <'WSW-STC-010'> temperatureTest {
        @Verifies { need = "WSW-CON-004"; }
        doc /* Operate the switch in a climate chamber at -40 °C and +85 °C; pass if every function works at both. */
    }
    verification <'WSW-STC-011'> ingressTest {
        @Verifies { need = "WSW-CON-005"; }
        doc /* Expose the mounted switch to dust and to dripping water per IP5K3; pass if none reaches the PCB and every function works. */
    }
}
