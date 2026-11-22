package WindowSwitchRequirements {
    doc /* R layer: what the window switch shall do, derived from the platform requirements. Values the
     * model can state are constraints on SwitchAssembly (WindowSwitchPhysical); these are the rest. */

    private import Trace::*;

    requirement <'WSW-SR-001'> windowKeyStages {
        @Satisfies { need = "WSW-PRQ-001"; }
        doc /* The switch shall report each window key as released, first stage or second stage, as three distinct states, while the key is held at that stage. */
    }
    requirement <'WSW-SR-002'> childLockToggle {
        @Satisfies { need = "WSW-PRQ-002"; }
        doc /* The switch shall report each press of the child-lock key as one toggle request and light the telltale while the received child-lock state is active. */
    }
    requirement <'WSW-SR-003'> nightDesign {
        @Satisfies { need = "WSW-PRQ-003"; }
        doc /* The switch shall light every key symbol at the dimming level received from the vehicle within 100 ms of receiving it. */
    }
    requirement <'WSW-SR-004'> keyStateLatency {
        @Satisfies { need = "WSW-PRQ-004"; }
        doc /* The switch shall send a changed key state on the vehicle bus at most 20 ms after the key reaches the new stage. */
    }
    requirement <'WSW-SR-005'> nodeAddressing {
        @Satisfies { need = "WSW-PRQ-004"; }
        doc /* The switch shall answer configuration requests addressed to its node address or to the broadcast address, and no others. */
    }
    requirement <'WSW-SR-006'> framePlausibility {
        @Satisfies { need = "WSW-PRQ-004"; }
        doc /* The switch shall discard every received LIN frame with a wrong checksum, and every received command frame with a repeated alive counter or a signal out of its range. */
    }
}
