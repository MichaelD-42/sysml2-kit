package WindowSwitchRfqLogical {
    doc /* L layer: the platform window switch as this vehicle needs it. OEM_WindowSwitch subsets the platform
     * switch and inherits its logical components, which satisfy the system requirements they meet. This RFQ's
     * limits are constraints on the switch as built (WindowSwitchRfqPhysical), and the door positions are
     * physical too. */

    private import WindowSwitchRfqRequirements::*;
    private import WindowSwitchLogical::ACME_WindowSwitch;

    part <'LC-100'> OEM_WindowSwitch :> ACME_WindowSwitch {
        doc /* The vehicle's window switch: the platform window switch with its logical components, as this RFQ needs it. */
    }

    // the platform components this switch inherits meet these as they are
    satisfy windowKeyStages by OEM_WindowSwitch.keySensing;
    satisfy childLockTelltale by OEM_WindowSwitch.switchController;
    satisfy nightDesignDimming by OEM_WindowSwitch.illumination;
    satisfy keyStateReporting by OEM_WindowSwitch.linCommunication;
    satisfy messagePlausibility by OEM_WindowSwitch.linCommunication;
    // what this program adds on top of the platform
    satisfy partNumberLabel by OEM_WindowSwitch;
}
