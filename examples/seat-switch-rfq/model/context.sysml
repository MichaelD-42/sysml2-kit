package SeatSwitchRfqContext {
    doc /* The seat switches in their operating environment: the people and things they interact with. */

    part seatSwitchContext {
        doc /* The seat switches in use, with everything outside them that they exchange with. */
        part seatSwitches :> SeatSwitchRfqLogical::seatSwitches { doc /* The seat switches under development, one per seat position. */ }
        part seat { doc /* Carries the switch in its side trim; the seat control unit moves it. */ }
        part seatControlUnit { doc /* Seat ECU: LIN commander that reads the key states and drives the seat motors, heating, cooling and massage. */ }
        part seatHarness {
            doc /* Seat wiring harness: KL30, KL31 and the seat LIN from the seat control unit to the 6-pin connector of each switch. */
            port kl30 : SeatSwitchItems::PowerPort;
            port kl31 : SeatSwitchItems::GroundPort;
            port seatLin : SeatSwitchItems::LinPort;
        }
        part occupant { doc /* Adjusts the seat and the comfort functions. */ }
        part workshopTester { doc /* Diagnostic tester on the vehicle bus: reads faults and updates firmware. */ }
        part endOfLineTester { doc /* Supplier's end-of-line station: flashes, codes and tests each switch. */ }

        connect seatSwitches to seat;
        connect seatHarness.kl30 to seatSwitches.supply;
        connect seatHarness.kl31 to seatSwitches.ground;
        connect seatHarness.seatLin to seatSwitches.lin;
        connect seatControlUnit to seatHarness;
        connect occupant to seatSwitches;
        connect workshopTester to seatControlUnit;
        connect endOfLineTester to seatSwitches;
    }
}
