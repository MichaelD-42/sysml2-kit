package SeatSwitchRfqLogical {
    doc /* L layer: the platform seat switch as this vehicle needs it. OEM_SeatSwitch subsets the platform
     * switch and inherits its logical components, which satisfy the system requirements they meet; the
     * switch as a whole satisfies what this program adds. This RFQ's limits are constraints on the switch
     * as built (SeatSwitchRfqPhysical), and the seat positions are physical too. */

    private import SeatSwitchRfqRequirements::*;
    private import SeatSwitchLogical::ACME_SeatSwitch;

    part <'LC-100'> OEM_SeatSwitch :> ACME_SeatSwitch {
        doc /* The vehicle's seat switch: the platform seat switch with its logical components, as this RFQ needs it. */
    }

    // the platform components this switch inherits meet these as they are
    satisfy adjustmentRequests by OEM_SeatSwitch.positionSensing;
    satisfy comfortLevelSteps by OEM_SeatSwitch.keypad;
    satisfy nightDesignDimming by OEM_SeatSwitch.illumination;
    satisfy keyStateReporting by OEM_SeatSwitch.linCommunication;
    satisfy messagePlausibility by OEM_SeatSwitch.linCommunication;
    satisfy diagnosticIdentification by OEM_SeatSwitch.switchController;
    satisfy faultCodes by OEM_SeatSwitch.switchController;
    satisfy authenticatedWrite by OEM_SeatSwitch.switchController;
    satisfy signedImagesOnly by OEM_SeatSwitch.switchController;
    satisfy workshopUpdate by OEM_SeatSwitch.linCommunication;
    satisfy endOfLineTest by OEM_SeatSwitch.switchController;
    satisfy endOfLineCoding by OEM_SeatSwitch.switchController;
    satisfy traceabilityContent by OEM_SeatSwitch.switchController;
    satisfy debugInterfaceClosed by OEM_SeatSwitch.switchController;
    satisfy installationSpace by OEM_SeatSwitch.enclosure;
    satisfy seatInPlaceReplacement by OEM_SeatSwitch.enclosure;
    // what this program adds on top of the platform
    satisfy materialDeclaration by OEM_SeatSwitch;
    satisfy sparePartNumbers by OEM_SeatSwitch;
}
