package WindowSwitchRfqSystemTests {
    doc /* V: system test cases. Each verifies system requirements or constraints, and where the customer
     * prescribes the test (a CTR), implements it as written. */

    private import Trace::*;
    private import WindowSwitchRfqRequirements::*;

    verification <'STC-101'> hapticMeasurement {
        @Implements { need = "CTR-002"; }
        @Verifies { need = "CON-101"; }
        doc /* Record force-travel curves of every key on 10 samples per key module as CTR-002 prescribes; pass if the first-stage force is 3.0 N to 7.5 N. */
    }
    verification <'STC-102'> keyDurabilityTest {
        @Implements { need = "CTR-001"; }
        @Verifies { need = "CON-102"; }
        doc /* Actuate every key per CTR-001's profile to 150 000 cycles per stage; pass at 100 000 cycles if force stays in limits and no key fails, and record the cycle count at which the first key fails. */
    }
    verification <'STC-103'> environmentalTest {
        @Implements { need = "CTR-005"; }
        @Verifies { need = "CON-104"; }
        @Verifies { need = "CON-105"; }
        @Verifies { need = "CON-107"; }
        doc /* Run the OEM-ENV-100 programme of CTR-005 on 6 samples, with function checks at 9 V, 13.5 V and 16 V and at -40 °C and +85 °C, and the quiescent current measured with the bus asleep; pass if every function works at every check and the current is at most 100 µA. */
    }
    verification <'STC-104'> ingressTest {
        @Implements { need = "CTR-003"; }
        @Verifies { need = "CON-106"; }
        doc /* Expose the switch mounted in a door trim to dust and to dripping water per IP5K3; pass if none reaches the PCB and every function works. */
    }
    verification <'STC-105'> linConformanceTest {
        @Verifies { need = "CON-103"; }
        @Verifies { need = "CON-109"; }
        doc /* Run the LIN 2.2A conformance suite on both door switches on one bus; pass if every case passes and each switch answers only its own node address. */
    }
    verification <'STC-106'> keyLayoutInspection {
        @Verifies { need = "CON-108"; }
        @Verifies { need = "CON-110"; }
        @Verifies { need = "CON-111"; }
        @Verifies { need = "CON-112"; }
        @Verifies { need = "CON-113"; }
        doc /* Inspect and weigh 10 switches of each door; pass if each has its door's keys and white symbols and weighs at most 50 g. */
    }
    verification <'STC-107'> windowKeyTest {
        doc /* Move every window key of both doors to both stages on the HIL bench with the LIN log; pass if each stage is reported while held and within 30 ms of the change. */
        objective { verify windowKeyStages; verify keyStateReporting; }
    }
    verification <'STC-108'> childLockTest {
        doc /* Press the child-lock key and toggle the received child-lock state; pass if each press yields one toggle request and the telltale follows the state. */
        objective { verify childLockTelltale; }
    }
    verification <'STC-109'> nightDesignTest {
        doc /* Send dimming levels 0 to 100 % on LIN; pass if symbol brightness follows within 100 ms. */
        objective { verify nightDesignDimming; }
    }
    verification <'STC-110'> plausibilityTest {
        doc /* Send frames with a wrong checksum, a repeated alive counter and a signal out of range; pass if the switch discards each. */
        objective { verify messagePlausibility; }
    }
    verification <'STC-111'> labelInspection {
        doc /* Read the label of 10 switches of each door by eye and with the line scanner; pass if each shows its door's OEM part number in both forms. */
        objective { verify partNumberLabel; }
    }
}
