package WindowSwitchRfqUseCases {
    doc /* R layer: how occupants and the driver use the vehicle's door window switches.
     * Each use case realizes customer requirements and is realized by the features it performs. */

    private import Trace::*;
    private import WindowSwitchRfqFeatures::*;

    use case <'UC-101'> moveWindow {
        @Realizes { need = "CRS-201"; }
        @Realizes { need = "CRS-202"; }
        @Realizes { need = "CRS-401"; }
        objective { doc /* The occupant wants to open or close a window */ }
        doc /* The occupant moves a window key to the first stage to move the window while held, or to the second stage for express travel. */
        subject OEM_WindowSwitch :> WindowSwitchRfqContext::doorSwitchContext.OEM_WindowSwitch;
        actor occupant :> WindowSwitchRfqContext::doorSwitchContext.occupant;
        actor doorControlUnit :> WindowSwitchRfqContext::doorSwitchContext.doorControlUnit;
        perform windowKeys;
        perform linCommunication;
    }

    use case <'UC-102'> lockRearWindows {
        @Realizes { need = "CRS-203"; }
        objective { doc /* The driver wants to lock the rear windows against the children */ }
        doc /* The driver presses the child-lock key; the door control unit blocks the rear window keys and the telltale shows the lock. */
        subject OEM_WindowSwitch :> WindowSwitchRfqContext::doorSwitchContext.OEM_WindowSwitch;
        actor driver :> WindowSwitchRfqContext::doorSwitchContext.driver;
        actor doorControlUnit :> WindowSwitchRfqContext::doorSwitchContext.doorControlUnit;
        perform childLock;
        perform linCommunication;
    }

    use case <'UC-103'> findSwitchAtNight {
        @Realizes { need = "CRS-204"; }
        objective { doc /* The occupant wants to find the window keys in the dark */ }
        doc /* At night the key symbols are lit white at the vehicle's dimming level. */
        subject OEM_WindowSwitch :> WindowSwitchRfqContext::doorSwitchContext.OEM_WindowSwitch;
        actor occupant :> WindowSwitchRfqContext::doorSwitchContext.occupant;
        actor doorControlUnit :> WindowSwitchRfqContext::doorSwitchContext.doorControlUnit;
        perform nightDesign;
    }
}
