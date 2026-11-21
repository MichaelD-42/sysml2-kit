package SeatSwitchRequirements {
    doc /* R layer: what the seat switch shall do, derived from the platform requirements. Values the
     * model can state are constraints on SwitchAssembly (SeatSwitchPhysical); these are the rest. */

    private import Trace::*;

    requirement <'SSW-SR-001'> adjustmentDirections {
        @Satisfies { need = "SSW-PRQ-001"; }
        doc /* The switch shall report fore, aft, up, down, recline forward, recline back, lumbar in and lumbar out as eight distinct requests while the knob is held in that direction. */
    }
    requirement <'SSW-SR-002'> comfortKeySteps {
        @Satisfies { need = "SSW-PRQ-002"; }
        doc /* The switch shall report each press of a comfort key as one step up its function's level, wrapping from the highest level to off. */
    }
    requirement <'SSW-SR-003'> nightDesign {
        @Satisfies { need = "SSW-PRQ-003"; }
        doc /* The switch shall light every key symbol at the dimming level received from the vehicle within 100 ms of receiving it. */
    }
    requirement <'SSW-SR-004'> keyStateLatency {
        @Satisfies { need = "SSW-PRQ-004"; }
        doc /* The switch shall send a changed key state on the vehicle bus at most 20 ms after the key press. */
    }
    requirement <'SSW-SR-005'> faultMemory {
        @Satisfies { need = "SSW-PRQ-005"; }
        doc /* The switch shall store a diagnostic trouble code for a key held for more than 30 s and report it on a diagnostic read request. */
    }
    requirement <'SSW-SR-006'> signedFirmware {
        @Satisfies { need = "SSW-PRQ-006"; }
        doc /* The switch shall start only a firmware image whose signature verifies against the key stored at production. */
    }
    requirement <'SSW-SR-007'> protectedWrite {
        @Satisfies { need = "SSW-PRQ-007"; }
        doc /* The switch shall reject every diagnostic write and flash request until a security access exchange has succeeded. */
    }
    requirement <'SSW-SR-008'> endOfLineTestMode {
        @Satisfies { need = "SSW-PRQ-008"; }
        doc /* In end-of-line test mode the switch shall report every key's state and light every LED on command. */
    }
    requirement <'SSW-SR-009'> variantCoding {
        @Satisfies { need = "SSW-PRQ-008"; }
        doc /* The switch shall report only the keys of the button set coded at end of line. */
    }
    requirement <'SSW-SR-010'> mirroredMounting {
        @Satisfies { need = "SSW-PRQ-017"; }
        doc /* Each switch shall fit only the seat trim opening of its own side, left or right, and no opening of the other side. */
    }
}
