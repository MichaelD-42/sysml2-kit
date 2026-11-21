package SeatSwitchRfqSystemTests {
    doc /* V: system test cases. Each verifies system requirements or constraints, and where the customer
     * prescribes the test (a CTR), implements it as written. */

    private import Trace::*;
    private import SeatSwitchRfqRequirements::*;

    verification <'STC-101'> hapticMeasurement {
        @Implements { need = "CTR-003"; }
        @Verifies { need = "CON-101"; }
        @Verifies { need = "CON-102"; }
        doc /* Record force-travel curves of every key and knob direction on 10 samples per button set as CTR-003 prescribes; pass if force is 3.0 N to 6.5 N and travel 0.2 mm to 1.5 mm. */
    }
    verification <'STC-102'> luminanceMeasurement {
        @Verifies { need = "CON-103"; }
        doc /* Measure each lit symbol at full dimming level in a dark room; pass at 8 cd/m² to 40 cd/m². */
    }
    verification <'STC-103'> keyDurabilityTest {
        @Implements { need = "CTR-002"; }
        @Verifies { need = "CON-104"; }
        doc /* Actuate every key and knob direction per CTR-002's profile at -40 °C, 23 °C and +85 °C, to 300 000 cycles; pass at 200 000 cycles if force stays in limits and no key fails, and record the cycle count at which the first key fails. */
        objective { verify durabilityGap; }
    }
    verification <'STC-104'> environmentalTest {
        @Implements { need = "CTR-001"; }
        @Verifies { need = "CON-105"; }
        @Verifies { need = "CON-106"; }
        doc /* Run the OEM-ENV-100 programme of CTR-001 on 6 samples, with function checks at 9 V, 13.5 V and 16 V and at -40 °C and +85 °C; pass if every function works at every check. */
    }
    verification <'STC-105'> ingressTest {
        @Implements { need = "CTR-006"; }
        @Verifies { need = "CON-107"; }
        doc /* Expose the switch mounted in a trim panel to dust and to splash water per IP5K4; pass if no dust or water reaches the PCB and every function works. */
    }
    verification <'STC-106'> esdTest {
        @Implements { need = "CTR-005"; }
        @Verifies { need = "CON-108"; }
        doc /* Discharge ±8 kV contact and ±15 kV air on every touchable surface, powered and unpowered; pass without reset, fault code or damage. */
    }
    verification <'STC-107'> emcTest {
        @Implements { need = "CTR-004"; }
        doc /* Run the OEM-EMC-200 class 3 emission and immunity tests of CTR-004 in an accredited laboratory; pass if every limit is met. */
        objective { verify emcLimits; }
    }
    verification <'STC-108'> linConformanceTest {
        @Implements { need = "CTR-008"; }
        @Verifies { need = "CON-109"; }
        doc /* Run the LIN 2.2A conformance suite and the OEM-LIN-300 frame tests, including frames with wrong checksum, repeated alive counter and out-of-range signals; pass if every case passes, every changed key state is sent within 50 ms and every bad frame is discarded. */
        objective { verify keyStateReporting; verify messagePlausibility; }
    }
    verification <'STC-109'> markingInspection {
        @Verifies { need = "CON-110"; }
        doc /* Read the Data Matrix of 50 switches with the customer's scanner type after the environmental test; pass if every code reads. */
    }
    verification <'STC-110'> workshopUpdateTest {
        @Verifies { need = "CON-111"; }
        doc /* With the workshop tester on the vehicle LIN, update the firmware of a fitted switch; pass if the update completes within 180 s and the new version is reported. */
        objective { verify workshopUpdate; }
    }
    verification <'STC-111'> dimensionalInspection {
        @Verifies { need = "CON-112"; }
        doc /* Weigh 10 switches of each variant and measure them against the seat trim drawing; pass at 60 g or less and inside the installation space. */
        objective { verify installationSpace; }
    }
    verification <'STC-112'> positionVariantCheck {
        @Verifies { need = "CON-113"; }
        @Verifies { need = "CON-114"; }
        @Verifies { need = "CON-115"; }
        @Verifies { need = "CON-116"; }
        @Verifies { need = "CON-117"; }
        @Verifies { need = "CON-118"; }
        @Verifies { need = "CON-119"; }
        @Verifies { need = "CON-120"; }
        doc /* For each seat position, check the switch's housing side, coding rib and comfort keys against the position table, and its label against the spare-part list; pass if all four positions match. */
        objective { verify sparePartNumbers; }
    }
    verification <'STC-113'> adjustmentDirectionTest {
        doc /* Push the knob parts and the lumbar pad in each of the ten directions on the HIL bench; pass if each yields its own request on LIN while held and none after release. */
        objective { verify adjustmentRequests; }
    }
    verification <'STC-114'> comfortKeyTest {
        doc /* Press each comfort key of each button set repeatedly; pass if the level steps up once per press, wraps to off, and the level LEDs follow. */
        objective { verify comfortLevelSteps; }
    }
    verification <'STC-115'> nightDesignTest {
        doc /* Send dimming levels 0 % to 100 % on LIN; pass if symbol brightness follows within 100 ms. */
        objective { verify nightDesignDimming; }
    }
    verification <'STC-116'> diagnosticsTest {
        doc /* Read identification data, then provoke a stuck key, an open LED and 8 V supply and read the fault memory; pass if the data are correct and each fault is reported. */
        objective { verify diagnosticIdentification; verify faultCodes; }
    }
    verification <'STC-117'> penetrationTest {
        @Implements { need = "CTR-007"; }
        doc /* Independent penetration test per CTR-007: unsigned and wrongly signed images, write and flash requests without and with forged certificates, debug pin probing on series parts, fuzzed LIN frames; pass if no attack succeeds. */
        objective { verify authenticatedWrite; verify signedImagesOnly; verify debugInterfaceClosed; }
    }
    verification <'STC-118'> endOfLineSequenceTest {
        doc /* Run the end-of-line sequence for each position's button set; pass if every key and LED is reported and only the coded set's keys are active. */
        objective { verify endOfLineTest; verify endOfLineCoding; }
    }
    verification <'STC-119'> materialDataReview {
        doc /* Check the material data system entry of every part against the bill of materials and the OEM-MAT-500 restricted list; pass if every part is declared and none contains a restricted substance. */
        objective { verify materialDeclaration; }
    }
    verification <'STC-120'> seatInPlaceReplacementTest {
        doc /* With a seat fitted in a vehicle body, remove and refit each switch with the trim tool; pass if each takes at most 5 minutes and the switch works afterwards. */
        objective { verify seatInPlaceReplacement; }
    }
}
