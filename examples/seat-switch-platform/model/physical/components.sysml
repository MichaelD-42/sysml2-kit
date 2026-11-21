package SeatSwitchPhysical {
    doc /* P layer: the parts that are built and shipped, one engineering domain each, with the
     * logical components and interfaces allocated to them. Each doc names the BOM part number. */

    private import Trace::*;
    private import SeatSwitchLogical::*;
    private import SeatSwitchItems::*;
    private import ISQ::*;
    private import SI::*;
    private import ScalarValues::String;
    private import ScalarValues::Integer;

    // what every assembled switch states, and the platform's limits on it as constraints (plain values included)
    part def SwitchAssembly {
        doc /* Characteristics of an assembled seat switch, whatever its housing side and button set. */
        attribute actuationForce : ForceValue;
        attribute keyTravel : LengthValue;
        attribute minOperatingVoltage : ElectricPotentialDifferenceValue;
        attribute maxOperatingVoltage : ElectricPotentialDifferenceValue;
        attribute minOperatingTemperature : ThermodynamicTemperatureValue;
        attribute maxOperatingTemperature : ThermodynamicTemperatureValue;
        attribute ipRating : String;
        attribute esdContactLevel : ElectricPotentialDifferenceValue;
        attribute esdAirLevel : ElectricPotentialDifferenceValue;
        attribute durabilityCycles : Integer;
        attribute symbolLuminance : LuminanceValue;
        attribute linVersion : String;
        // set by our own production and workshop requirements, not by a customer
        attribute endOfLineTestTime : DurationValue;
        attribute partMarking : String;
        attribute reflashTime : DurationValue;

        constraint <'SSW-CON-001'> actuationForceWindow {
            @Satisfies { need = "SSW-PRQ-009"; }
            doc /* The actuation force of every key and knob direction shall be 3.5 N to 6.0 N. */
            actuationForce >= 3.5 [N] and actuationForce <= 6.0 [N]
        }
        constraint <'SSW-CON-002'> keyTravelWindow {
            @Satisfies { need = "SSW-PRQ-009"; }
            doc /* The travel to the actuation point shall be 0.3 mm to 1.2 mm. */
            keyTravel >= 0.3 [mm] and keyTravel <= 1.2 [mm]
        }
        constraint <'SSW-CON-003'> symbolLuminanceWindow {
            @Satisfies { need = "SSW-PRQ-010"; }
            doc /* A lit key symbol shall have a luminance of 10 cd/m² to 30 cd/m² at full dimming level. */
            symbolLuminance >= 10 [cd/m^2] and symbolLuminance <= 30 [cd/m^2]
        }
        constraint <'SSW-CON-004'> keyDurability {
            @Satisfies { need = "SSW-PRQ-011"; }
            doc /* Every key and knob direction shall withstand at least 200 000 actuations. */
            durabilityCycles >= 200000
        }
        constraint <'SSW-CON-005'> operatingVoltageRange {
            @Satisfies { need = "SSW-PRQ-012"; }
            doc /* The switch shall operate from 9 V to 16 V. */
            minOperatingVoltage <= 9 [V] and maxOperatingVoltage >= 16 [V]
        }
        constraint <'SSW-CON-006'> operatingTemperatureRange {
            @Satisfies { need = "SSW-PRQ-013"; }
            doc /* The switch shall operate from -40 °C to +85 °C. */
            minOperatingTemperature <= -40 ['°C'] and maxOperatingTemperature >= 85 ['°C']
        }
        constraint <'SSW-CON-007'> ingressProtection {
            @Satisfies { need = "SSW-PRQ-014"; }
            doc /* The switch shall be rated IP5K4. */
            ipRating == "IP5K4"
        }
        constraint <'SSW-CON-008'> esdImmunity {
            @Satisfies { need = "SSW-PRQ-015"; }
            doc /* The switch shall withstand electrostatic discharge of ±8 kV contact and ±15 kV air on every touchable surface. */
            esdContactLevel >= 8000 [V] and esdAirLevel >= 15000 [V]
        }
        constraint <'SSW-CON-009'> linProtocolVersion {
            @Satisfies { need = "SSW-PRQ-016"; }
            doc /* The switch shall implement LIN protocol version 2.2A. */
            linVersion == "2.2A"
        }
        constraint <'SSW-CON-010'> endOfLineCycleTime {
            @Satisfies { need = "SSW-PRQ-018"; }
            doc /* The end-of-line test of one switch shall take at most 12 s. */
            endOfLineTestTime <= 12 [s]
        }
        constraint <'SSW-CON-011'> traceabilityMarking {
            @Satisfies { need = "SSW-PRQ-019"; }
            doc /* Every switch shall carry a laser-marked Data Matrix code. */
            partMarking == "laser Data Matrix"
        }
        constraint <'SSW-CON-012'> workshopReflashTime {
            @Satisfies { need = "SSW-PRQ-020"; }
            doc /* A full reflash over LIN, with fault memory readout before and after, shall take at most 120 s. */
            reflashTime <= 120 [s]
        }
    }

    // a variation owns only its variants, so the housing's characteristics live in its definition
    part def Housing {
        doc /* Characteristics every housing variant states. */
        attribute side : String;
        attribute clipPattern : String;
        attribute codingRib : String;
    }
    part def ButtonSet {
        doc /* Characteristics every button set states. */
        attribute heatingKeys : Integer;
        attribute coolingKeys : Integer;
        attribute massageKeys : Integer;
    }

    // the housing is mirrored by seat side; an RFQ selects one variant per seat position
    #Mechanical variation part <'SSW-PC-001'> housing : Housing {
        doc /* PBT-GF30 housing family: one forward-offset snap-fit clip pattern and a coding rib, mirrored left to right, so a housing fits only its own side's trim opening, BOM SSW-HSG-100. */
        variant #Mechanical part <'SSW-PC-002'> housingLH {
            doc /* Left-hand housing; its coding rib keys into the slot of the left-hand trim opening only, BOM SSW-HSG-110. */
            attribute :>> side = "left";
            attribute :>> clipPattern = "forward-offset";
            attribute :>> codingRib = "left-hand";
            #Mechanical port <'SSW-PI-001'> clipsLH : ClipPort;
        }
        variant #Mechanical part <'SSW-PC-003'> housingRH {
            doc /* Right-hand housing, mirror image of the left-hand one, clip pattern and coding rib included, BOM SSW-HSG-120. */
            attribute :>> side = "right";
            attribute :>> clipPattern = "forward-offset";
            attribute :>> codingRib = "right-hand";
            #Mechanical port <'SSW-PI-002'> clipsRH : ClipPort;
        }
    }
    #Mechanical part <'SSW-PC-004'> knob {
        doc /* Seat-shaped two-part adjustment knob (cushion and backrest) and a 4-way lumbar pad, BOM SSW-KNB-200. */
    }
    #Mechanical part <'SSW-PC-005'> buttonCaps {
        doc /* Laser-etched comfort key caps with night-design symbol windows, BOM SSW-CAP-300.
         * The caps and the housing's key openings follow the button set. */
    }
    #Mechanical part <'SSW-PC-006'> seal {
        doc /* Silicone keymat seal between caps and PCB, BOM SSW-SEL-400. */
    }

    #Electrical part <'SSW-PC-007'> pcb {
        doc /* Main PCB with microcontroller and supply filter, BOM SSW-PCB-500. */
        port supply : ~PowerPort;
    }
    #Electrical part <'SSW-PC-008'> hallSensors {
        doc /* 3D hall sensors under the knob parts and the lumbar pad, BOM SSW-HAL-510. */
        port directions : KeyPort;
    }
    #Electrical part <'SSW-PC-009'> linTransceiver {
        doc /* LIN transceiver with bus protection, BOM SSW-LIN-520. */
        #Electrical port <'SSW-PI-003'> linPin : LinPort;
    }
    #Electrical part <'SSW-PC-010'> leds {
        doc /* White symbol LEDs and amber level LEDs, BOM SSW-LED-530. */
        port symbols : LightPort;
    }
    // keys (tact switches) and level LEDs are placed on the PCB; the button set decides which are fitted
    #Electrical variation part <'SSW-PC-011'> buttonSet : ButtonSet {
        doc /* Comfort key population of the PCB, BOM SSW-BTN-600. */
        variant #Electrical part <'SSW-PC-012'> base {
            doc /* Adjustment knob only, no comfort keys, BOM SSW-BTN-610. */
            attribute :>> heatingKeys = 0;
            attribute :>> coolingKeys = 0;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-013'> heating {
            doc /* One seat heating key with three level LEDs, BOM SSW-BTN-620. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 0;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-014'> heatingCooling {
            doc /* Seat heating and seat cooling keys with three level LEDs each, BOM SSW-BTN-630. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 1;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-015'> massageHeatingCooling {
            doc /* Massage, heating and cooling keys with three level LEDs each, BOM SSW-BTN-640. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 1;
            attribute :>> massageKeys = 1;
        }
    }

    #Software part <'SSW-PC-016'> switchFirmware {
        doc /* Switch firmware: secure boot, tester authentication, LIN stack, diagnostics; module SSW-SW-700. */
        #Software port <'SSW-PI-004'> linStack : ~LinPort;
    }

    part seatSwitchAssembly : SwitchAssembly {
        doc /* The switch as delivered, with the platform's rated values: one housing, one button set, behind two ports. */
        attribute :>> actuationForce = 4.5 [N];
        attribute :>> keyTravel = 0.6 [mm];
        attribute :>> minOperatingVoltage = 9 [V];
        attribute :>> maxOperatingVoltage = 16 [V];
        attribute :>> minOperatingTemperature = -40 ['°C'];
        attribute :>> maxOperatingTemperature = 85 ['°C'];
        attribute :>> ipRating = "IP5K4";
        attribute :>> esdContactLevel = 8000 [V];
        attribute :>> esdAirLevel = 15000 [V];
        attribute :>> durabilityCycles = 200000;
        attribute :>> symbolLuminance = 20 [cd/m^2];
        attribute :>> linVersion = "2.2A";
        attribute :>> endOfLineTestTime = 9 [s];
        attribute :>> partMarking = "laser Data Matrix";
        attribute :>> reflashTime = 95 [s];

        ref part housing :> SeatSwitchPhysical::housing;
        ref part knob :> SeatSwitchPhysical::knob;
        ref part buttonCaps :> SeatSwitchPhysical::buttonCaps;
        ref part seal :> SeatSwitchPhysical::seal;
        ref part pcb :> SeatSwitchPhysical::pcb;
        ref part hallSensors :> SeatSwitchPhysical::hallSensors;
        ref part linTransceiver :> SeatSwitchPhysical::linTransceiver;
        ref part leds :> SeatSwitchPhysical::leds;
        ref part buttonSet :> SeatSwitchPhysical::buttonSet;
        ref part switchFirmware :> SeatSwitchPhysical::switchFirmware;

        port lin : LinPort;
        port supply : ~PowerPort;

        interface : LinInterface connect linTransceiver.linPin to switchFirmware.linStack;

        bind lin = linTransceiver.linPin;
        bind supply = pcb.supply;
    }

    allocate seatSwitch.enclosure to housing.housingLH;
    allocate seatSwitch.enclosure to housing.housingRH;
    allocate seatSwitch.enclosure to knob;
    allocate seatSwitch.enclosure to buttonCaps;
    allocate seatSwitch.enclosure to seal;
    allocate seatSwitch.keypad to buttonSet.base;
    allocate seatSwitch.keypad to buttonSet.heating;
    allocate seatSwitch.keypad to buttonSet.heatingCooling;
    allocate seatSwitch.keypad to buttonSet.massageHeatingCooling;
    allocate seatSwitch.positionSensing to hallSensors;
    allocate seatSwitch.switchController to pcb;
    allocate seatSwitch.switchController to switchFirmware;
    allocate seatSwitch.linCommunication to linTransceiver;
    allocate seatSwitch.linCommunication to switchFirmware;
    allocate seatSwitch.illumination to leds;

    allocate seatSwitch.enclosure.trimMount to housing.housingLH.clipsLH;
    allocate seatSwitch.enclosure.trimMount to housing.housingRH.clipsRH;
    allocate seatSwitch.linCommunication.vehicleBus to linTransceiver.linPin;
    allocate seatSwitch.linCommunication.controllerLink to switchFirmware.linStack;
}
