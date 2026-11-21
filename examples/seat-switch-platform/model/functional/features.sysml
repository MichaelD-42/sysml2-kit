package SeatSwitchFeatures {
    doc /* F layer: what the seat-switch product line sells (features, noun names) and the functions
     * each feature owns, independent of how they are built. */

    private import Trace::*;
    private import SeatSwitchItems::*;

    #Feature action <'SSW-FEAT-001'> seatAdjustmentInput {
        doc /* Seat fore/aft, height, recline and lumbar adjustment from one seat-shaped knob. */
        action <'SSW-F-001'> senseKnobDirection {
            doc /* Detect which of the eight directions the knob is pushed in. */
            out keyState : KeyState;
        }
        action <'SSW-F-002'> debounceAdjustmentInput {
            doc /* Accept a direction only after it is stable for the debounce time. */
            in keyState : KeyState;
        }
        action <'SSW-F-003'> mapToAdjustmentSignal { doc /* Map the accepted direction to its LIN signal. */ }
        action <'SSW-F-004'> provideTactileFeedback { doc /* Guide knob and key travel and give a tactile click at the actuation point. */ }

        first senseKnobDirection then debounceAdjustmentInput;
        first debounceAdjustmentInput then mapToAdjustmentSignal;
        flow of KeyState from senseKnobDirection.keyState to debounceAdjustmentInput.keyState;
    }

    #Feature action <'SSW-FEAT-002'> comfortFunctionInput {
        doc /* Keys for seat heating, cooling and massage, by button set, with a level indicator per key. */
        action <'SSW-F-005'> detectKeyPress {
            doc /* Detect a press of a comfort key. */
            out keyState : KeyState;
        }
        action <'SSW-F-006'> debounceKey {
            doc /* Accept a key press only after it is stable for the debounce time. */
            in keyState : KeyState;
        }
        action <'SSW-F-007'> mapToComfortSignal { doc /* Map the accepted press to the next level of its comfort function on LIN. */ }
        action <'SSW-F-008'> showComfortLevel { doc /* Show the current level of each comfort function. */ }

        first detectKeyPress then debounceKey;
        first debounceKey then mapToComfortSignal;
        flow of KeyState from detectKeyPress.keyState to debounceKey.keyState;
    }

    #Feature action <'SSW-FEAT-003'> nightDesignIllumination {
        doc /* Key symbols lit at night at the vehicle's dimming level. */
        action <'SSW-F-009'> receiveDimmingLevel { doc /* Read the dimming level the vehicle sends. */ }
        action <'SSW-F-010'> lightKeySymbols { doc /* Light every key symbol at the dimming level. */ }

        first receiveDimmingLevel then lightKeySymbols;
    }

    #Feature action <'SSW-FEAT-004'> vehicleCommunication {
        doc /* Key states to, commands from the seat control unit over LIN. */
        action <'SSW-F-011'> sendKeyStates { doc /* Send the current key states in the switch's LIN frame. */ }
        action <'SSW-F-012'> receiveVehicleCommands { doc /* Read commands and status sent by the vehicle. */ }
        action <'SSW-F-013'> checkMessagePlausibility { doc /* Discard received frames with a wrong checksum, counter or value range. */ }

        first receiveVehicleCommands then checkMessagePlausibility;
    }

    #Feature action <'SSW-FEAT-005'> diagnostics {
        doc /* Fault memory, protected diagnostic access, end-of-line test and variant coding. */
        action <'SSW-F-014'> storeFaultCodes { doc /* Record stuck keys, LED faults and supply faults as diagnostic trouble codes. */ }
        action <'SSW-F-015'> answerDiagnosticRequests { doc /* Answer diagnostic read, clear and write requests. */ }
        action <'SSW-F-016'> grantSecurityAccess { doc /* Unlock protected services after a successful seed-key exchange. */ }
        action <'SSW-F-017'> runEndOfLineTest { doc /* Report key states and drive LEDs on command from the end-of-line tester. */ }
        action <'SSW-F-018'> storeVariantCoding { doc /* Store the button-set variant code and enable only its keys. */ }

        first grantSecurityAccess then storeVariantCoding;
    }

    #Feature action <'SSW-FEAT-006'> secureUpdate {
        doc /* Firmware update over the vehicle bus that accepts only signed images. */
        action <'SSW-F-019'> receiveFirmwareImage {
            doc /* Receive a firmware image over the diagnostic channel. */
            in image : FirmwareImage;
        }
        action <'SSW-F-020'> verifyImageSignature { doc /* Verify the image signature before it is activated. */ }
        action <'SSW-F-021'> bootVerifiedImage { doc /* At start-up, run the image only if its signature verifies (secure boot). */ }

        first receiveFirmwareImage then verifyImageSignature;
        first verifyImageSignature then bootVerifiedImage;
    }
}
