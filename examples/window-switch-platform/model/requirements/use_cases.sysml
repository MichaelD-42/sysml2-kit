package WindowSwitchUseCases {
    doc /* R layer: how occupants and the door control unit use the window switch. Each use case realizes
     * platform requirements and is realized by the features it performs. */

    private import Trace::*;
    private import WindowSwitchFeatures::*;

    use case <'WSW-UC-001'> moveWindow {
        @Realizes { need = "WSW-PRQ-001"; }
        @Realizes { need = "WSW-PRQ-004"; }
        objective { doc /* The occupant wants to open or close a window */ }
        doc /* The occupant pulls or pushes a window key to the first stage to move the window while held, or to the second stage for express travel; the door control unit drives the motor. */
        subject ACME_WindowSwitch :> WindowSwitchLogical::ACME_WindowSwitch;
        actor occupant;
        actor doorControlUnit;
        perform windowControl;
        perform vehicleCommunication;
    }

    use case <'WSW-UC-002'> lockRearWindows {
        @Realizes { need = "WSW-PRQ-002"; }
        objective { doc /* The driver wants to lock the rear windows against the children */ }
        doc /* The driver presses the child-lock key; the door control unit blocks the rear window keys and the telltale shows the lock. */
        subject ACME_WindowSwitch :> WindowSwitchLogical::ACME_WindowSwitch;
        actor driver;
        actor doorControlUnit;
        perform childLock;
        perform vehicleCommunication;
    }

    use case <'WSW-UC-003'> findSwitchAtNight {
        @Realizes { need = "WSW-PRQ-003"; }
        objective { doc /* The occupant wants to find the window keys in the dark */ }
        doc /* At night the key symbols are lit at the vehicle's dimming level. */
        subject ACME_WindowSwitch :> WindowSwitchLogical::ACME_WindowSwitch;
        actor occupant;
        actor doorControlUnit;
        perform nightIllumination;
    }
}
