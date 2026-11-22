package WindowSwitchRfqLogical {
    doc /* L layer: the logical breakdown this RFQ quotes, derived in the RFQ analysis: technology-neutral
     * components and interfaces, the functions allocated to them, and the system requirements they satisfy.
     * The platform realizes them at P (WindowSwitchRfqPhysical); this RFQ's limits are constraints on the
     * switch as built, and the door positions are physical too. */

    private import WindowSwitchRfqFeatures::*;
    private import WindowSwitchRfqRequirements::*;

    part <'LC-100'> OEM_WindowSwitch {
        doc /* The vehicle's window switch as a whole. */
        part <'LC-101'> keySensing {
            doc /* Turns key movement into key stages. */
            port <'LI-101'> keyStates;
        }
        part <'LC-102'> switchController {
            doc /* Debounces and maps key stages to requests and drives the lights. */
            port <'LI-102'> keyInput;
            port <'LI-103'> busData;
            port <'LI-104'> lightControl;
        }
        part <'LC-103'> linCommunication {
            doc /* Exchanges frames with the door control unit and checks received frames. */
            port <'LI-105'> controllerLink;
            port <'LI-106'> vehicleBus;
        }
        part <'LC-104'> illumination {
            doc /* Lights key symbols and the child-lock telltale. */
            port <'LI-107'> lightDrive;
        }
        part <'LC-105'> powerSupply {
            doc /* Supplies the switch's electronics from the vehicle supply. */
            port <'LI-108'> vehicleSupply;
        }
        part <'LC-106'> enclosure {
            doc /* Holds and seals the switch, guides the keys, carries its label, mounts it in the door trim. */
            port <'LI-109'> trimMount;
        }

        connect keySensing.keyStates to switchController.keyInput;
        connect switchController.busData to linCommunication.controllerLink;
        connect switchController.lightControl to illumination.lightDrive;
    }

    allocate windowKeys.senseKeyStage to OEM_WindowSwitch.keySensing;
    allocate windowKeys.debounceKey to OEM_WindowSwitch.switchController;
    allocate windowKeys.mapToWindowRequest to OEM_WindowSwitch.switchController;
    allocate windowKeys.provideTactileFeedback to OEM_WindowSwitch.enclosure;
    allocate childLock.detectChildLockKey to OEM_WindowSwitch.keySensing;
    allocate childLock.requestChildLockToggle to OEM_WindowSwitch.switchController;
    allocate childLock.showChildLockState to OEM_WindowSwitch.illumination;
    allocate nightDesign.receiveDimmingLevel to OEM_WindowSwitch.linCommunication;
    allocate nightDesign.lightKeySymbols to OEM_WindowSwitch.illumination;
    allocate linCommunication.sendKeyStates to OEM_WindowSwitch.linCommunication;
    allocate linCommunication.receiveDoorCommands to OEM_WindowSwitch.linCommunication;
    allocate linCommunication.checkMessagePlausibility to OEM_WindowSwitch.linCommunication;
    allocate linCommunication.supplyProtectedPower to OEM_WindowSwitch.powerSupply;

    satisfy windowKeyStages by OEM_WindowSwitch.keySensing;
    satisfy childLockTelltale by OEM_WindowSwitch.switchController;
    satisfy nightDesignDimming by OEM_WindowSwitch.illumination;
    satisfy keyStateReporting by OEM_WindowSwitch.linCommunication;
    satisfy messagePlausibility by OEM_WindowSwitch.linCommunication;
    satisfy partNumberLabel by OEM_WindowSwitch.enclosure;
}
