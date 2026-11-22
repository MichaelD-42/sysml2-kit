package WindowSwitchRfqContext {
    doc /* The door window switches in their operating environment: the people and things they interact with. */

    part doorSwitchContext {
        doc /* The window switches in use, with everything outside them that they exchange with. */
        part OEM_WindowSwitch :> WindowSwitchRfqLogical::OEM_WindowSwitch, WindowSwitchRfqPhysical::oemWindowSwitch { doc /* The window switches under development, one per front door. */ }
        part door { doc /* Carries the switch in its armrest trim; the door control unit drives its window. */ }
        part doorControlUnit { doc /* Door ECU: LIN master that reads the key states, drives the window motors with anti-pinch, and blocks the rear windows on child lock. */ }
        part doorHarness {
            doc /* Door wiring harness: KL30, KL31 and the door LIN from the door control unit to the 4-pin connector of the switch. */
            port kl30 : WindowSwitchItems::PowerPort;
            port kl31 : WindowSwitchItems::GroundPort;
            port doorLin : WindowSwitchItems::LinPort;
        }
        part occupant { doc /* Opens and closes a window. */ }
        part driver { doc /* Opens and closes every window and locks the rear windows. */ }

        connect OEM_WindowSwitch to door;
        connect doorHarness.kl30 to OEM_WindowSwitch.supply;
        connect doorHarness.kl31 to OEM_WindowSwitch.ground;
        connect doorHarness.doorLin to OEM_WindowSwitch.lin;
        connect doorControlUnit to doorHarness;
        connect occupant to OEM_WindowSwitch;
        connect driver to OEM_WindowSwitch;
    }
}
