package SeatSwitchRfqFeatures {
    doc /* F layer: the platform features this vehicle's seat switches offer, each matching the customer
     * requirements it covers. A feature subsets the platform feature it reuses and inherits its functions;
     * only the comfort keys add functions, one per seat position.
     * Known compromise: F-101..104 exist because CRS-203 differs per seat position and each function is
     * allocated to exactly one logical component (rule function-allocated), so each position switch gets
     * its own function; the behaviour itself is the platform's. */

    private import Trace::*;

    #Feature action <'FEAT-101'> seatAdjustment :> SeatSwitchFeatures::seatAdjustmentInput {
        @Matches { need = "CRS-201"; }
        @Matches { need = "CRS-202"; }
        doc /* Seat fore/aft, height, recline and lumbar adjustment from the knob and lumbar pad. */
    }

    #Feature action <'FEAT-102'> comfortKeys :> SeatSwitchFeatures::comfortFunctionInput {
        @Matches { need = "CRS-203"; }
        @Matches { need = "CRS-204"; }
        @Matches { need = "CRS-205"; }
        doc /* Heating, cooling and massage keys with level indicators, by seat position. */
        action <'F-101'> offerDriverComfortKeys { doc /* Offer massage, heating and cooling keys at the driver seat. */ }
        action <'F-102'> offerCoDriverComfortKeys { doc /* Offer heating and cooling keys at the co-driver seat. */ }
        action <'F-103'> offerRearLeftComfortKeys { doc /* Offer a heating key at the rear left seat. */ }
        action <'F-104'> offerRearRightComfortKeys { doc /* Offer a heating key at the rear right seat. */ }
    }

    #Feature action <'FEAT-103'> nightDesign :> SeatSwitchFeatures::nightDesignIllumination {
        @Matches { need = "CRS-206"; }
        doc /* Key symbols lit at night at the vehicle's dimming level. */
    }

    #Feature action <'FEAT-104'> linCommunication :> SeatSwitchFeatures::vehicleCommunication {
        @Matches { need = "CRS-401"; }
        @Matches { need = "CRS-403"; }
        @Matches { need = "CRS-605"; }
        doc /* Key states to, commands from the seat control unit over LIN, with plausibility checks. */
    }

    #Feature action <'FEAT-105'> diagnosticServices :> SeatSwitchFeatures::diagnostics {
        @Matches { need = "CRS-404"; }
        @Matches { need = "CRS-603"; }
        @Matches { need = "CRS-701"; }
        @Matches { need = "CRS-702"; }
        @Matches { need = "CRS-801"; }
        doc /* Identification, fault memory, protected diagnostic access, end-of-line test and coding. */
    }

    #Feature action <'FEAT-106'> softwareUpdate :> SeatSwitchFeatures::secureUpdate {
        @Matches { need = "CRS-601"; }
        @Matches { need = "CRS-602"; }
        @Matches { need = "CRS-702"; }
        @Matches { need = "CRS-802"; }
        doc /* Firmware update over LIN, signed images only, secure boot. */
    }
}
