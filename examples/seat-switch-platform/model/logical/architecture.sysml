package SeatSwitchLogical {
    doc /* L layer: technology-neutral components and interfaces, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import SeatSwitchFeatures::*;
    private import SeatSwitchRequirements::*;
    // typed by the assembly definition, so an RFQ component subsetting ACME_SeatSwitch inherits its attributes
    private import SeatSwitchPhysical::SwitchAssembly;

    part <'SSW-LC-001'> ACME_SeatSwitch : SwitchAssembly {
        doc /* The seat adjustment switch as a whole. */
        part <'SSW-LC-002'> keypad {
            doc /* Turns comfort key presses into key states. */
            port <'SSW-LI-001'> keyStates;
        }
        part <'SSW-LC-003'> positionSensing {
            doc /* Turns knob and lumbar pad movement into direction states. */
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
            doc /* Exchanges frames with the seat control unit, checks received frames, sleeps and wakes with the bus. */
            port <'SSW-LI-007'> controllerLink;
            port <'SSW-LI-008'> vehicleBus;
        }
        part <'SSW-LC-006'> illumination {
            doc /* Lights key symbols and level indicators. */
            port <'SSW-LI-009'> lightDrive;
        }
        part <'SSW-LC-008'> powerSupply {
            doc /* Supplies the switch's electronics from the vehicle supply. */
            port <'SSW-LI-011'> vehicleSupply;
        }
        part <'SSW-LC-007'> enclosure {
            doc /* Holds and seals the switch, guides knob, lumbar pad and keys, mounts it in the seat trim. */
            port <'SSW-LI-010'> trimMount;
        }

        connect keypad.keyStates to switchController.keyInput;
        connect positionSensing.directionStates to switchController.directionInput;
        connect switchController.busData to linCommunication.controllerLink;
        connect switchController.lightControl to illumination.lightDrive;
    }

    allocate seatAdjustmentInput.senseKnobDirection to ACME_SeatSwitch.positionSensing;
    allocate seatAdjustmentInput.debounceAdjustmentInput to ACME_SeatSwitch.switchController;
    allocate seatAdjustmentInput.mapToAdjustmentSignal to ACME_SeatSwitch.switchController;
    allocate seatAdjustmentInput.provideTactileFeedback to ACME_SeatSwitch.enclosure;
    allocate comfortFunctionInput.detectKeyPress to ACME_SeatSwitch.keypad;
    allocate comfortFunctionInput.debounceKey to ACME_SeatSwitch.switchController;
    allocate comfortFunctionInput.mapToComfortSignal to ACME_SeatSwitch.switchController;
    allocate comfortFunctionInput.showComfortLevel to ACME_SeatSwitch.illumination;
    allocate nightDesignIllumination.receiveDimmingLevel to ACME_SeatSwitch.linCommunication;
    allocate nightDesignIllumination.lightKeySymbols to ACME_SeatSwitch.illumination;
    allocate vehicleCommunication.sendKeyStates to ACME_SeatSwitch.linCommunication;
    allocate vehicleCommunication.receiveVehicleCommands to ACME_SeatSwitch.linCommunication;
    allocate vehicleCommunication.checkMessagePlausibility to ACME_SeatSwitch.linCommunication;
    allocate vehicleCommunication.supplyProtectedPower to ACME_SeatSwitch.powerSupply;
    allocate diagnostics.storeFaultCodes to ACME_SeatSwitch.switchController;
    allocate diagnostics.answerDiagnosticRequests to ACME_SeatSwitch.switchController;
    allocate diagnostics.grantSecurityAccess to ACME_SeatSwitch.switchController;
    allocate diagnostics.runEndOfLineTest to ACME_SeatSwitch.switchController;
    allocate diagnostics.storeVariantCoding to ACME_SeatSwitch.switchController;
    allocate secureUpdate.receiveFirmwareImage to ACME_SeatSwitch.linCommunication;
    allocate secureUpdate.verifyImageSignature to ACME_SeatSwitch.switchController;
    allocate secureUpdate.bootVerifiedImage to ACME_SeatSwitch.switchController;

    satisfy adjustmentDirections by ACME_SeatSwitch.positionSensing;
    satisfy comfortKeySteps by ACME_SeatSwitch.keypad;
    satisfy nightDesign by ACME_SeatSwitch.illumination;
    satisfy keyStateLatency by ACME_SeatSwitch.linCommunication;
    satisfy faultMemory by ACME_SeatSwitch.switchController;
    satisfy signedFirmware by ACME_SeatSwitch.switchController;
    satisfy protectedWrite by ACME_SeatSwitch.switchController;
    satisfy endOfLineTestMode by ACME_SeatSwitch.switchController;
    satisfy variantCoding by ACME_SeatSwitch.switchController;
    satisfy mirroredMounting by ACME_SeatSwitch.enclosure;
    satisfy sideKeyedAssembly by ACME_SeatSwitch.enclosure;
    satisfy nodeAddressing by ACME_SeatSwitch.linCommunication;
    satisfy busSleepAndWake by ACME_SeatSwitch.linCommunication;
    satisfy framePlausibility by ACME_SeatSwitch.linCommunication;
}
