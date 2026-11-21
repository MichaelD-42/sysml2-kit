package SeatSwitchRfqContext {
    doc /* The seat switches in their operating environment: the people and things they interact with. */

    part seatSwitchContext {
        doc /* The seat switches in use, with everything outside them that they exchange with. */
        part seatSwitches :> SeatSwitchRfqLogical::seatSwitches { doc /* The seat switches under development, one per seat position. */ }
        part seat { doc /* Carries the switch in its side trim; the seat control unit moves it. */ }
        part seatControlUnit { doc /* Seat ECU: LIN commander that reads the key states and drives the seat motors, heating, cooling and massage. */ }
        part occupant { doc /* Adjusts the seat and the comfort functions. */ }
        part workshopTester { doc /* Diagnostic tester on the vehicle bus: reads faults and updates firmware. */ }
        part endOfLineTester { doc /* Supplier's end-of-line station: flashes, codes and tests each switch. */ }

        connect seatSwitches to seat;
        connect seatSwitches to seatControlUnit;
        connect occupant to seatSwitches;
        connect workshopTester to seatControlUnit;
        connect endOfLineTester to seatSwitches;
    }
}
