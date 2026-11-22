package SeatSwitchRfqUseCases {
    doc /* R layer: how occupants, the workshop and the production line use the vehicle's seat switches.
     * Each use case realizes customer requirements and is realized by the features it performs. */

    private import Trace::*;
    private import SeatSwitchRfqFeatures::*;

    use case <'UC-101'> adjustSeat {
        @Realizes { need = "CRS-201"; }
        @Realizes { need = "CRS-202"; }
        @Realizes { need = "CRS-401"; }
        objective { doc /* The occupant wants to adjust the seat position */ }
        doc /* The occupant pushes the knob or the lumbar pad; the seat control unit moves the seat while it is held. */
        subject OEM_SeatSwitch :> SeatSwitchRfqContext::seatSwitchContext::OEM_SeatSwitch;
        actor occupant :> SeatSwitchRfqContext::seatSwitchContext::occupant;
        actor seatControlUnit :> SeatSwitchRfqContext::seatSwitchContext::seatControlUnit;
        perform seatAdjustment;
        perform linCommunication;
    }

    use case <'UC-102'> useComfortFunctions {
        @Realizes { need = "CRS-203"; }
        @Realizes { need = "CRS-204"; }
        @Realizes { need = "CRS-206"; }
        objective { doc /* The occupant wants to set seat heating, cooling and massage */ }
        doc /* The occupant steps seat heating, cooling or massage through its levels; at night the keys are lit. */
        subject OEM_SeatSwitch :> SeatSwitchRfqContext::seatSwitchContext::OEM_SeatSwitch;
        actor occupant :> SeatSwitchRfqContext::seatSwitchContext::occupant;
        actor seatControlUnit :> SeatSwitchRfqContext::seatSwitchContext::seatControlUnit;
        perform comfortKeys;
        perform nightDesign;
    }

    use case <'UC-103'> serviceInWorkshop {
        @Realizes { need = "CRS-404"; }
        @Realizes { need = "CRS-801"; }
        @Realizes { need = "CRS-802"; }
        objective { doc /* The technician wants to diagnose and update the switch without removing it */ }
        doc /* A technician reads identification and fault memory and updates the firmware over LIN with the workshop tester. */
        subject OEM_SeatSwitch :> SeatSwitchRfqContext::seatSwitchContext::OEM_SeatSwitch;
        actor technician :> SeatSwitchRfqContext::seatSwitchContext::technician;
        actor workshopTester :> SeatSwitchRfqContext::seatSwitchContext::workshopTester;
        perform diagnosticServices;
        perform softwareUpdate;
    }

    use case <'UC-104'> produceAtEndOfLine {
        @Realizes { need = "CRS-701"; }
        @Realizes { need = "CRS-702"; }
        objective { doc /* The end-of-line tester wants to flash, code and test each switch for its seat position */ }
        doc /* The end-of-line tester flashes and codes each switch for its seat position, then tests every key and LED. */
        subject OEM_SeatSwitch :> SeatSwitchRfqContext::seatSwitchContext::OEM_SeatSwitch;
        actor endOfLineTester :> SeatSwitchRfqContext::seatSwitchContext::endOfLineTester;
        perform diagnosticServices;
        perform softwareUpdate;
    }
}
