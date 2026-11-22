package WindowSwitchRfqRequirements {
    doc /* R layer: what the window switches shall do, derived from the customer requirements. Values the
     * model can state are constraints on OEM_WindowSwitch and on the door parts (WindowSwitchRfqPhysical);
     * these are the rest: behaviour. */

    private import Trace::*;

    requirement <'SR-101'> windowKeyStages {
        @Satisfies { need = "CRS-201"; }
        @Satisfies { need = "CRS-202"; }
        doc /* The switch shall report each window key as released, manual or express, as three distinct states, while the key is held at that stage. */
    }
    // states what is met of CRS-203: toggle and telltale, no fault blinking
    requirement <'SR-102'> childLockTelltale {
        @Satisfies { need = "CRS-203"; }
        doc /* The driver switch shall report each press of the child-lock key as one toggle request and light the telltale while the received child-lock state is active. */
    }
    requirement <'SR-103'> nightDesignDimming {
        @Satisfies { need = "CRS-204"; }
        doc /* The switch shall light every key symbol at the dimming level received on LIN within 100 ms of receiving it. */
    }
    requirement <'SR-104'> keyStateReporting {
        @Satisfies { need = "CRS-401"; }
        doc /* The switch shall send a changed key state in its LIN frame to the door control unit at most 30 ms after the change. */
    }
    // what this program adds on top of the platform: satisfied by the switch as a whole
    requirement <'SR-106'> partNumberLabel {
        @Satisfies { need = "CRS-506"; }
        doc /* The label of each switch shall carry the OEM part number of its door in plain text and in its Data Matrix code. */
    }
    requirement <'SR-105'> messagePlausibility {
        @Satisfies { need = "CRS-403"; }
        doc /* The switch shall discard every received LIN frame with a wrong checksum, a repeated alive counter or a signal out of its range. */
    }
}
