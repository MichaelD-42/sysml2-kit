package SeatSwitchUseCases {
    doc /* R layer: how occupants, the vehicle, the workshop and the production line use the seat
     * switch. Each use case realizes platform requirements and is realized by the features it performs. */

    private import Trace::*;
    private import SeatSwitchFeatures::*;

    use case <'SSW-UC-001'> adjustSeat {
        @Realizes { need = "SSW-PRQ-001"; }
        @Realizes { need = "SSW-PRQ-004"; }
        doc /* The occupant pushes the knob; the seat control unit moves the seat while the knob is held. */
        subject seatSwitch;
        actor occupant;
        actor seatControlUnit;
        perform seatAdjustmentInput;
        perform vehicleCommunication;
    }

    use case <'SSW-UC-002'> operateComfortFunctions {
        @Realizes { need = "SSW-PRQ-002"; }
        @Realizes { need = "SSW-PRQ-003"; }
        doc /* The occupant presses a heating, cooling or massage key and sees its level; at night the keys are lit. */
        subject seatSwitch;
        actor occupant;
        actor seatControlUnit;
        perform comfortFunctionInput;
        perform nightDesignIllumination;
    }

    use case <'SSW-UC-003'> diagnoseAndUpdateInWorkshop {
        @Realizes { need = "SSW-PRQ-005"; }
        @Realizes { need = "SSW-PRQ-006"; }
        @Realizes { need = "SSW-PRQ-007"; }
        doc /* A technician reads the fault memory and updates the firmware over the vehicle bus with a diagnostic tester. */
        subject seatSwitch;
        actor technician;
        actor diagnosticTester;
        perform diagnostics;
        perform secureUpdate;
    }

    use case <'SSW-UC-004'> produceAndTestAtEndOfLine {
        @Realizes { need = "SSW-PRQ-008"; }
        doc /* The end-of-line station flashes and codes the button set, then tests every key and LED. */
        subject seatSwitch;
        actor endOfLineTester;
        perform diagnostics;
        perform secureUpdate;
    }
}
