package WindowSwitchLogical {
    doc /* L layer: technology-neutral components and interfaces, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import WindowSwitchFeatures::*;
    private import WindowSwitchRequirements::*;

    // solution-free: its rated values and limits belong to the switch as built (WindowSwitchPhysical::windowSwitchAssembly)
    part <'WSW-LC-001'> ACME_WindowSwitch {
        doc /* The door window switch as a whole. */
        part <'WSW-LC-002'> keySensing {
            doc /* Turns key movement into key stages. */
            port <'WSW-LI-001'> keyStates;
        }
        part <'WSW-LC-003'> switchController {
            doc /* Debounces and maps key stages to requests and drives the lights. */
            port <'WSW-LI-002'> keyInput;
            port <'WSW-LI-003'> busData;
            port <'WSW-LI-004'> lightControl;
        }
        part <'WSW-LC-004'> linCommunication {
            doc /* Exchanges frames with the door control unit and checks received frames. */
            port <'WSW-LI-005'> controllerLink;
            port <'WSW-LI-006'> vehicleBus;
        }
        part <'WSW-LC-005'> illumination {
            doc /* Lights key symbols and the child-lock telltale. */
            port <'WSW-LI-007'> lightDrive;
        }
        part <'WSW-LC-006'> powerSupply {
            doc /* Supplies the switch's electronics from the vehicle supply. */
            port <'WSW-LI-008'> vehicleSupply;
        }
        part <'WSW-LC-007'> enclosure {
            doc /* Holds and seals the switch, guides the keys, mounts it in the door trim. */
            port <'WSW-LI-009'> trimMount;
        }

        connect keySensing.keyStates to switchController.keyInput;
        connect switchController.busData to linCommunication.controllerLink;
        connect switchController.lightControl to illumination.lightDrive;
    }

    allocate windowControl.senseKeyStage to ACME_WindowSwitch.keySensing;
    allocate windowControl.debounceKey to ACME_WindowSwitch.switchController;
    allocate windowControl.mapToWindowRequest to ACME_WindowSwitch.switchController;
    allocate windowControl.provideTactileFeedback to ACME_WindowSwitch.enclosure;
    allocate childLock.detectChildLockKey to ACME_WindowSwitch.keySensing;
    allocate childLock.requestChildLockToggle to ACME_WindowSwitch.switchController;
    allocate childLock.showChildLockState to ACME_WindowSwitch.illumination;
    allocate nightIllumination.receiveDimmingLevel to ACME_WindowSwitch.linCommunication;
    allocate nightIllumination.lightKeySymbols to ACME_WindowSwitch.illumination;
    allocate vehicleCommunication.sendKeyStates to ACME_WindowSwitch.linCommunication;
    allocate vehicleCommunication.receiveDoorCommands to ACME_WindowSwitch.linCommunication;
    allocate vehicleCommunication.checkMessagePlausibility to ACME_WindowSwitch.linCommunication;
    allocate vehicleCommunication.supplyProtectedPower to ACME_WindowSwitch.powerSupply;

    satisfy windowKeyStages by ACME_WindowSwitch.keySensing;
    satisfy childLockToggle by ACME_WindowSwitch.switchController;
    satisfy nightDesign by ACME_WindowSwitch.illumination;
    satisfy keyStateLatency by ACME_WindowSwitch.linCommunication;
    satisfy nodeAddressing by ACME_WindowSwitch.linCommunication;
    satisfy framePlausibility by ACME_WindowSwitch.linCommunication;
}
