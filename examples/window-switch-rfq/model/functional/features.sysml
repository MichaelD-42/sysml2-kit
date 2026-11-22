package WindowSwitchRfqFeatures {
    doc /* F layer: the platform features this vehicle's window switches offer, each matching the customer
     * requirements it covers. A feature subsets the platform feature it reuses and inherits its functions;
     * which keys each door gets is its key-module selection (WindowSwitchRfqPhysical). */

    private import Trace::*;

    #Feature action <'FEAT-101'> windowKeys :> WindowSwitchFeatures::windowControl {
        @Matches { need = "CRS-201"; }
        @Matches { need = "CRS-202"; }
        doc /* Two-stage window keys, four in the driver door and one in the passenger door. */
    }

    // the platform telltale shows the lock; the OEM's fault blinking is not offered (CST-005)
    #Feature action <'FEAT-102'> childLock :> WindowSwitchFeatures::childLock {
        @Matches { need = "CRS-203"; partial = true; }
        doc /* Child-lock key in the driver door with a telltale showing the lock. */
    }

    #Feature action <'FEAT-103'> nightDesign :> WindowSwitchFeatures::nightIllumination {
        @Matches { need = "CRS-204"; }
        doc /* Key symbols lit at night at the vehicle's dimming level. */
    }

    #Feature action <'FEAT-104'> linCommunication :> WindowSwitchFeatures::vehicleCommunication {
        @Matches { need = "CRS-401"; }
        @Matches { need = "CRS-403"; }
        doc /* Key states to, commands from the door control unit over LIN, with plausibility checks. */
    }
}
