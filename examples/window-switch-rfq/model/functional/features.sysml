package WindowSwitchRfqFeatures {
    doc /* F layer: the features this vehicle's window switches offer, each matching the customer
     * requirements it covers, and the functions each owns. The RFQ derives them itself; the platform
     * realizes them at P (WindowSwitchRfqPhysical). Which keys each door gets is its key-module selection. */

    private import Trace::*;
    private import WindowSwitchItems::*;

    #Feature action <'FEAT-101'> windowKeys {
        @Matches { need = "CRS-201"; }
        @Matches { need = "CRS-202"; }
        doc /* Two-stage window keys, four in the driver door and one in the passenger door. */
        action <'F-101'> senseKeyStage {
            doc /* Detect which stage a window key is pulled or pushed to. */
            out keyState : KeyState;
        }
        action <'F-102'> debounceKey {
            doc /* Accept a key stage only after it is stable for the debounce time. */
            in keyState : KeyState;
        }
        action <'F-103'> mapToWindowRequest { doc /* Map the accepted stage to its window's manual or express request on LIN. */ }
        action <'F-104'> provideTactileFeedback { doc /* Guide key travel and give a distinct click at each stage. */ }

        first senseKeyStage then debounceKey;
        first debounceKey then mapToWindowRequest;
        flow of KeyState from senseKeyStage.keyState to debounceKey.keyState;
    }

    // the telltale shows the lock; the OEM's fault blinking is not offered (CST-005)
    #Feature action <'FEAT-102'> childLock {
        @Matches { need = "CRS-203"; partial = true; }
        doc /* Child-lock key in the driver door with a telltale showing the lock. */
        action <'F-105'> detectChildLockKey {
            doc /* Detect a press of the child-lock key. */
            out keyState : KeyState;
        }
        action <'F-106'> requestChildLockToggle {
            doc /* Send the accepted press as a child-lock toggle request on LIN. */
            in keyState : KeyState;
        }
        action <'F-107'> showChildLockState { doc /* Light the telltale while the door control unit reports the lock active. */ }

        first detectChildLockKey then requestChildLockToggle;
        flow of KeyState from detectChildLockKey.keyState to requestChildLockToggle.keyState;
    }

    #Feature action <'FEAT-103'> nightDesign {
        @Matches { need = "CRS-204"; }
        doc /* Key symbols lit at night at the vehicle's dimming level. */
        action <'F-108'> receiveDimmingLevel { doc /* Read the dimming level the vehicle sends. */ }
        action <'F-109'> lightKeySymbols { doc /* Light every key symbol at the dimming level. */ }

        first receiveDimmingLevel then lightKeySymbols;
    }

    #Feature action <'FEAT-104'> linCommunication {
        @Matches { need = "CRS-401"; }
        @Matches { need = "CRS-403"; }
        doc /* Key states to, commands from the door control unit over LIN, with plausibility checks. */
        action <'F-110'> sendKeyStates { doc /* Send the current key states in the switch's LIN frame. */ }
        action <'F-111'> receiveDoorCommands { doc /* Read the dimming level and the child-lock state sent by the door control unit. */ }
        action <'F-112'> checkMessagePlausibility { doc /* Discard received frames with a wrong checksum, counter or value range. */ }
        action <'F-113'> supplyProtectedPower { doc /* Supply the electronics from the vehicle supply across 9 V to 16 V and survive reverse polarity and transients. */ }

        first receiveDoorCommands then checkMessagePlausibility;
    }
}
