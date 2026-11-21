package SeatSwitchLogical {
    doc /* L layer: technology-neutral components and interfaces, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import SeatSwitchFeatures::*;
    private import SeatSwitchRequirements::*;

    part <'SSW-LC-001'> seatSwitch {
        doc /* The seat adjustment switch as a whole. */
        part <'SSW-LC-002'> keypad {
            doc /* Turns comfort key presses into key states. */
            port <'SSW-LI-001'> keyStates;
        }
        part <'SSW-LC-003'> positionSensing {
            doc /* Turns knob movement into direction states. */
            port <'SSW-LI-002'> directionStates;
        }
        part <'SSW-LC-004'> switchController {
            doc /* Debounces and maps inputs, keeps the fault memory, guards access and the firmware. */
            port <'SSW-LI-003'> keyInput;
            port <'SSW-LI-004'> directionInput;
            port <'SSW-LI-005'> busData;
            port <'SSW-LI-006'> lightControl;
        }
        part <'SSW-LC-005'> linCommunication {
            doc /* Exchanges frames with the seat control unit. */
            port <'SSW-LI-007'> controllerLink;
            port <'SSW-LI-008'> vehicleBus;
        }
        part <'SSW-LC-006'> illumination {
            doc /* Lights key symbols and level indicators. */
            port <'SSW-LI-009'> lightDrive;
        }
        part <'SSW-LC-007'> enclosure {
            doc /* Holds and seals the switch, guides knob and keys, mounts it in the seat trim. */
            port <'SSW-LI-010'> trimMount;
        }

        connect keypad.keyStates to switchController.keyInput;
        connect positionSensing.directionStates to switchController.directionInput;
        connect switchController.busData to linCommunication.controllerLink;
        connect switchController.lightControl to illumination.lightDrive;
    }

    allocate seatAdjustmentInput.senseKnobDirection to seatSwitch.positionSensing;
    allocate seatAdjustmentInput.debounceAdjustmentInput to seatSwitch.switchController;
    allocate seatAdjustmentInput.mapToAdjustmentSignal to seatSwitch.switchController;
    allocate seatAdjustmentInput.provideTactileFeedback to seatSwitch.enclosure;
    allocate comfortFunctionInput.detectKeyPress to seatSwitch.keypad;
    allocate comfortFunctionInput.debounceKey to seatSwitch.switchController;
    allocate comfortFunctionInput.mapToComfortSignal to seatSwitch.switchController;
    allocate comfortFunctionInput.showComfortLevel to seatSwitch.illumination;
    allocate nightDesignIllumination.receiveDimmingLevel to seatSwitch.linCommunication;
    allocate nightDesignIllumination.lightKeySymbols to seatSwitch.illumination;
    allocate vehicleCommunication.sendKeyStates to seatSwitch.linCommunication;
    allocate vehicleCommunication.receiveVehicleCommands to seatSwitch.linCommunication;
    allocate vehicleCommunication.checkMessagePlausibility to seatSwitch.switchController;
    allocate diagnostics.storeFaultCodes to seatSwitch.switchController;
    allocate diagnostics.answerDiagnosticRequests to seatSwitch.switchController;
    allocate diagnostics.grantSecurityAccess to seatSwitch.switchController;
    allocate diagnostics.runEndOfLineTest to seatSwitch.switchController;
    allocate diagnostics.storeVariantCoding to seatSwitch.switchController;
    allocate secureUpdate.receiveFirmwareImage to seatSwitch.linCommunication;
    allocate secureUpdate.verifyImageSignature to seatSwitch.switchController;
    allocate secureUpdate.bootVerifiedImage to seatSwitch.switchController;

    satisfy adjustmentDirections by seatSwitch.positionSensing;
    satisfy comfortKeySteps by seatSwitch.keypad;
    satisfy nightDesign by seatSwitch.illumination;
    satisfy keyStateLatency by seatSwitch.linCommunication;
    satisfy faultMemory by seatSwitch.switchController;
    satisfy signedFirmware by seatSwitch.switchController;
    satisfy protectedWrite by seatSwitch.switchController;
    satisfy endOfLineTestMode by seatSwitch.switchController;
    satisfy variantCoding by seatSwitch.switchController;
    satisfy mirroredMounting by seatSwitch.enclosure;
}
