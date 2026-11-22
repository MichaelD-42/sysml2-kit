package WindowSwitchFeatures {
    doc /* F layer: what the window-switch product line sells (features, noun names) and the functions
     * each feature owns, independent of how they are built. */

    private import Trace::*;
    private import WindowSwitchItems::*;

    #Feature action <'WSW-FEAT-001'> windowControl {
        doc /* Two-stage window keys: first stage moves the window while held, second stage starts express travel. */
        action <'WSW-F-001'> senseKeyStage {
            doc /* Detect which stage a window key is pulled or pushed to. */
            out keyState : KeyState;
        }
        action <'WSW-F-002'> debounceKey {
            doc /* Accept a key stage only after it is stable for the debounce time. */
            in keyState : KeyState;
        }
        action <'WSW-F-003'> mapToWindowRequest { doc /* Map the accepted stage to its window's manual or express request on LIN. */ }
        action <'WSW-F-004'> provideTactileFeedback { doc /* Guide key travel and give a distinct click at each stage. */ }

        first senseKeyStage then debounceKey;
        first debounceKey then mapToWindowRequest;
        flow of KeyState from senseKeyStage.keyState to debounceKey.keyState;
    }

    #Feature action <'WSW-FEAT-002'> childLock {
        doc /* A child-lock key for the rear windows with a telltale showing the lock. */
        action <'WSW-F-005'> detectChildLockKey {
            doc /* Detect a press of the child-lock key. */
            out keyState : KeyState;
        }
        action <'WSW-F-006'> requestChildLockToggle {
            doc /* Send the accepted press as a child-lock toggle request on LIN. */
            in keyState : KeyState;
        }
        action <'WSW-F-007'> showChildLockState { doc /* Light the telltale while the door control unit reports the lock active. */ }

        first detectChildLockKey then requestChildLockToggle;
        flow of KeyState from detectChildLockKey.keyState to requestChildLockToggle.keyState;
    }

    #Feature action <'WSW-FEAT-003'> nightIllumination {
        doc /* Key symbols lit at night at the vehicle's dimming level. */
        action <'WSW-F-008'> receiveDimmingLevel { doc /* Read the dimming level the vehicle sends. */ }
        action <'WSW-F-009'> lightKeySymbols { doc /* Light every key symbol at the dimming level. */ }

        first receiveDimmingLevel then lightKeySymbols;
    }

    #Feature action <'WSW-FEAT-004'> vehicleCommunication {
        doc /* Key states to, commands from the door control unit over LIN. */
        action <'WSW-F-010'> sendKeyStates { doc /* Send the current key states in the switch's LIN frame. */ }
        action <'WSW-F-011'> receiveDoorCommands { doc /* Read the dimming level and the child-lock state sent by the door control unit. */ }
        action <'WSW-F-012'> checkMessagePlausibility { doc /* Discard received frames with a wrong checksum, counter or value range. */ }
        action <'WSW-F-013'> supplyProtectedPower { doc /* Supply the electronics from the vehicle supply across 9 V to 16 V and survive reverse polarity and transients. */ }

        first receiveDoorCommands then checkMessagePlausibility;
    }
}
