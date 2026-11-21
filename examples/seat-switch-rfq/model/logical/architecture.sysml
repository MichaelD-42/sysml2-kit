package SeatSwitchRfqLogical {
    doc /* L layer: the platform seat switch as this vehicle needs it. seatSwitches subsets the platform
     * switch, so it carries the platform's rated attributes and limits; its constraints are this RFQ's
     * limits over those attributes. One switch per seat position, each allocated to its housing and
     * button set. The platform's own components satisfy the system requirements they meet. */

    private import Trace::*;
    private import SeatSwitchRfqFeatures::*;
    private import SeatSwitchRfqRequirements::*;
    private import SeatSwitchLogical::seatSwitch;
    private import ISQ::*;
    private import SI::*;

    part <'LC-100'> seatSwitches :> seatSwitch {
        doc /* The vehicle's seat switches: the platform seat switch within this RFQ's limits, fitted at four seat positions. */
        // not rated by the platform; this program states it
        attribute mass : MassValue;

        constraint <'CON-101'> actuationForceLimits {
            @Satisfies { need = "CRS-301"; }
            doc /* The actuation force of every key and knob direction shall be 3.0 N to 6.5 N. */
            actuationForce >= 3.0 [N] and actuationForce <= 6.5 [N]
        }
        constraint <'CON-102'> keyTravelLimits {
            @Satisfies { need = "CRS-302"; }
            doc /* The travel to the actuation point shall be 0.2 mm to 1.5 mm. */
            keyTravel >= 0.2 [mm] and keyTravel <= 1.5 [mm]
        }
        constraint <'CON-103'> symbolLuminanceLimits {
            @Satisfies { need = "CRS-303"; }
            doc /* A lit key symbol shall have a luminance of 8 cd/m² to 40 cd/m² at full dimming level. */
            symbolLuminance >= 8 [cd/m^2] and symbolLuminance <= 40 [cd/m^2]
        }
        // the platform is rated for 200 000 actuations (SSW-CON-004); the OEM asks for 300 000
        constraint <'CON-104'> keyDurability {
            @Satisfies { need = "CRS-304"; partial = true; }
            doc /* Every key and knob direction shall withstand at least 200 000 actuations. */
            durabilityCycles >= 200000
        }
        constraint <'CON-105'> supplyVoltageRange {
            @Satisfies { need = "CRS-501"; }
            doc /* The switch shall operate from 9 V to 16 V. */
            minOperatingVoltage <= 9 [V] and maxOperatingVoltage >= 16 [V]
        }
        constraint <'CON-106'> operatingTemperatureRange {
            @Satisfies { need = "CRS-502"; }
            doc /* The switch shall operate from -40 °C to +85 °C. */
            minOperatingTemperature <= -40 ['°C'] and maxOperatingTemperature >= 85 ['°C']
        }
        constraint <'CON-107'> ingressRating {
            @Satisfies { need = "CRS-503"; }
            doc /* The switch shall be rated IP5K4. */
            ipRating == "IP5K4"
        }
        constraint <'CON-108'> esdLevels {
            @Satisfies { need = "CRS-504"; }
            doc /* The switch shall withstand ±8 kV contact and ±15 kV air discharge. */
            esdContactLevel >= 8000 [V] and esdAirLevel >= 15000 [V]
        }
        constraint <'CON-109'> linProtocol {
            @Satisfies { need = "CRS-402"; }
            doc /* The switch shall implement LIN 2.2A. */
            linVersion == "2.2A"
        }
        constraint <'CON-110'> dataMatrixMarking {
            @Satisfies { need = "CRS-703"; }
            doc /* Every switch shall carry a laser-marked Data Matrix code. */
            partMarking == "laser Data Matrix"
        }
        constraint <'CON-111'> workshopUpdateTime {
            @Satisfies { need = "CRS-803"; }
            doc /* A complete software update in the workshop shall take at most 180 s. */
            reflashTime <= 180 [s]
        }
        constraint <'CON-112'> switchMass {
            @Satisfies { need = "CRS-506"; }
            doc /* A switch shall weigh at most 60 g. */
            mass <= 60 [g]
        }

        part <'LC-101'> driverSwitch :> seatSwitch {
            doc /* Driver seat (left-hand drive): left-hand housing; massage, heating and cooling keys. */
        }
        part <'LC-102'> coDriverSwitch :> seatSwitch {
            doc /* Co-driver seat: right-hand housing; heating and cooling keys. */
        }
        part <'LC-103'> rearLeftSwitch :> seatSwitch {
            doc /* Rear left seat: left-hand housing; heating key. */
        }
        part <'LC-104'> rearRightSwitch :> seatSwitch {
            doc /* Rear right seat: right-hand housing; heating key. */
        }
    }

    allocate comfortKeys.offerDriverComfortKeys to seatSwitches.driverSwitch;
    allocate comfortKeys.offerCoDriverComfortKeys to seatSwitches.coDriverSwitch;
    allocate comfortKeys.offerRearLeftComfortKeys to seatSwitches.rearLeftSwitch;
    allocate comfortKeys.offerRearRightComfortKeys to seatSwitches.rearRightSwitch;

    // the platform components meet these as they are
    satisfy adjustmentRequests by seatSwitch.positionSensing;
    satisfy comfortLevelSteps by seatSwitch.keypad;
    satisfy nightDesignDimming by seatSwitch.illumination;
    satisfy keyStateReporting by seatSwitch.linCommunication;
    satisfy messagePlausibility by seatSwitch.switchController;
    satisfy diagnosticIdentification by seatSwitch.switchController;
    satisfy faultCodes by seatSwitch.switchController;
    satisfy authenticatedWrite by seatSwitch.switchController;
    satisfy signedImagesOnly by seatSwitch.switchController;
    satisfy workshopUpdate by seatSwitch.linCommunication;
    satisfy endOfLineTest by seatSwitch.switchController;
    satisfy endOfLineCoding by seatSwitch.switchController;
    satisfy debugInterfaceClosed by seatSwitch.switchController;
    satisfy installationSpace by seatSwitch.enclosure;
    satisfy seatInPlaceReplacement by seatSwitch.enclosure;
    // what this program adds on top of the platform
    satisfy emcLimits by seatSwitches;
    satisfy materialDeclaration by seatSwitches;
    satisfy sparePartNumbers by seatSwitches;
    satisfy durabilityGap by seatSwitches;
}
