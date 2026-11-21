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
        doc /* An assembled seat switch, whatever its housing side and button set: the platform's rated values
         * and its three ports. */
        attribute actuationForce : ForceValue = 4.5 [N];
        attribute keyTravel : LengthValue = 0.6 [mm];
        attribute minOperatingVoltage : ElectricPotentialDifferenceValue = 9 [V];
        attribute maxOperatingVoltage : ElectricPotentialDifferenceValue = 16 [V];
        attribute minOperatingTemperature : ThermodynamicTemperatureValue = -40 ['°C'];
        attribute maxOperatingTemperature : ThermodynamicTemperatureValue = 85 ['°C'];
        attribute ipRating : String = "IP5K4";
        attribute esdContactLevel : ElectricPotentialDifferenceValue = 8000 [V];
        attribute esdAirLevel : ElectricPotentialDifferenceValue = 15000 [V];
        attribute durabilityCycles : Integer = 200000;
        attribute symbolLuminance : LuminanceValue = 20 [cd/m^2];
        attribute linVersion : String = "2.2A";
        attribute emcSeverityClass : Integer = 3;
        attribute mass : MassValue = 48 [g];
        attribute symbolColour : String = "white";
        attribute levelIndicatorColour : String = "amber";
        // 50 µA with the bus asleep: only the transceiver (sleep mode, at most 20 µA) and the reverse-polarity TVS leakage draw;
        // the transceiver's INH switches the regulator off, so microcontroller, hall sensors and LED drivers are unpowered
        attribute quiescentCurrent : ElectricCurrentValue = 0.00005 [A];
        // set by our own production and workshop requirements, not by a customer
        attribute endOfLineTestTime : DurationValue = 9 [s];
        attribute partMarking : String = "laser Data Matrix";
        attribute reflashTime : DurationValue = 95 [s];
        // LIN node address, written per seat position by end-of-line variant coding; the platform sets no value
        attribute nad : Integer;

        port lin : LinPort;
        port supply : ~PowerPort;
        port ground : GroundPort;

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
        port contacts : KeyPort;
        port levelLeds : ~LedDrivePort;
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

    // the PCB assembly carries every electrical part except the button-set population, a variation an RFQ selects
    #Electrical part <'SSW-PC-007'> pcb {
        doc /* Main PCB assembly, BOM SSW-PCB-500. Every part returns to KL31 on the ground plane. */
        #Electrical port kl30 : ~PowerPort;
        #Electrical port kl31 : GroundPort;
        #Electrical port linBus : LinPort;
        #Electrical port keyContacts : ~KeyPort;
        #Electrical port levelLedDrive : LedDrivePort;

        #Electrical part <'SSW-PC-019'> reversePolarityProtection {
            doc /* Series Schottky diode and TVS diode on KL30 against reverse polarity and transients, BOM SSW-RPP-501. */
            #Electrical port kl30In : ~PowerPort;
            #Electrical port kl30Protected : PowerPort;
        }
        #Electrical part <'SSW-PC-018'> voltageRegulator {
            doc /* 5 V low-dropout regulator for the microcontroller and the hall sensors, enabled by the transceiver's INH so it is off with the bus asleep, BOM SSW-REG-502. */
            #Electrical port input : ~PowerPort;
            #Electrical port enable : ~InhibitPort;
            #Electrical port output : PowerPort;
        }
        #Electrical part <'SSW-PC-017'> microcontroller {
            doc /* 32-bit automotive microcontroller with UART, PWM timers, crypto accelerator and write-protectable flash; runs the firmware SSW-PC-016, BOM SSW-MCU-503. */
            #Electrical port supply : ~PowerPort;
            #Electrical port uart : UartPort;
            #Electrical port transceiverMode : TransceiverModePort;
            #Electrical port keyInputs : ~KeyPort;
            #Electrical port sensorBus : SensorBusPort;
            #Electrical port pwm : PwmPort;
        }
        #Electrical part <'SSW-PC-020'> linEsdProtection {
            doc /* ESD protection diode and 220 pF filter capacitor at the LIN pin, BOM SSW-ESD-504. */
            #Electrical port connectorSide : LinPort;
            #Electrical port transceiverSide : LinPort;
        }
        #Electrical part <'SSW-PC-009'> linTransceiver {
            doc /* LIN 2.2A transceiver with bus wake-up detection, supplied from protected KL30, BOM SSW-LIN-520. */
            #Electrical port <'SSW-PI-003'> linPin : LinPort;
            #Electrical port vbat : ~PowerPort;
            #Electrical port uart : ~UartPort;
            #Electrical port mode : ~TransceiverModePort;
            #Electrical port inh : InhibitPort;
        }
        #Electrical part <'SSW-PC-008'> hallSensors {
            doc /* 3D hall sensors under the knob parts and the lumbar pad, read over SPI, BOM SSW-HAL-510. */
            #Electrical port supply : ~PowerPort;
            #Electrical port sensorBus : ~SensorBusPort;
        }
        #Electrical part <'SSW-PC-021'> ledDrivers {
            doc /* Constant-current LED driver, one PWM-dimmed channel per LED group (symbols, level LEDs), with open-LED detection, BOM SSW-LDR-505. */
            #Electrical port pwm : ~PwmPort;
            #Electrical port symbolDrive : LedDrivePort;
            #Electrical port levelDrive : LedDrivePort;
        }
        #Electrical part <'SSW-PC-010'> leds {
            doc /* White symbol backlight LEDs, BOM SSW-LED-530; the amber level LEDs come with the button set. */
            #Electrical port drive : ~LedDrivePort;
            #Electrical port symbols : LightPort;
        }

        bind kl30 = reversePolarityProtection.kl30In;
        connect reversePolarityProtection.kl30Protected to linTransceiver.vbat;
        connect reversePolarityProtection.kl30Protected to voltageRegulator.input;
        connect linTransceiver.inh to voltageRegulator.enable;
        connect voltageRegulator.output to microcontroller.supply;
        connect voltageRegulator.output to hallSensors.supply;
        bind linBus = linEsdProtection.connectorSide;
        connect linEsdProtection.transceiverSide to linTransceiver.linPin;
        connect linTransceiver.uart to microcontroller.uart;
        connect microcontroller.transceiverMode to linTransceiver.mode;
        connect hallSensors.sensorBus to microcontroller.sensorBus;
        bind keyContacts = microcontroller.keyInputs;
        connect microcontroller.pwm to ledDrivers.pwm;
        connect ledDrivers.symbolDrive to leds.drive;
        bind levelLedDrive = ledDrivers.levelDrive;
    }
    #Electrical part <'SSW-PC-022'> vehicleConnector {
        doc /* 6-pin connector header to the seat harness, BOM SSW-CON-540. Pin 1 KL30 supply, pin 2 KL31 ground (also the LIN reference),
         * pin 3 LIN bus, pins 4 to 6 not used. LIN wakes up on the bus, so there is no wake line. */
        #Electrical port <'SSW-PI-005'> pin1Kl30 : ~PowerPort { doc /* KL30, permanent 12 V supply. */ }
        #Electrical port <'SSW-PI-006'> pin2Kl31 : GroundPort { doc /* KL31, ground and LIN reference. */ }
        #Electrical port <'SSW-PI-007'> pin3Lin : LinPort { doc /* LIN bus. */ }
        #Electrical port pin4 { doc /* Not used. */ }
        #Electrical port pin5 { doc /* Not used. */ }
        #Electrical port pin6 { doc /* Not used. */ }
    }
    // switch contacts (tact switches) and level LEDs are placed on the PCB; the button set decides which are fitted
    #Electrical variation part <'SSW-PC-011'> buttonSet : ButtonSet {
        doc /* Comfort key population of the PCB, BOM SSW-BTN-600. */
        variant #Electrical part <'SSW-PC-012'> base {
            doc /* Adjustment knob only, no comfort keys, BOM SSW-BTN-610. */
            attribute :>> heatingKeys = 0;
            attribute :>> coolingKeys = 0;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-013'> heating {
            doc /* Switch contact of one seat heating key with three level LEDs, BOM SSW-BTN-620. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 0;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-014'> heatingCooling {
            doc /* Switch contacts of the seat heating and seat cooling keys with three level LEDs each, BOM SSW-BTN-630. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 1;
            attribute :>> massageKeys = 0;
        }
        variant #Electrical part <'SSW-PC-015'> massageHeatingCooling {
            doc /* Switch contacts of the massage, heating and cooling keys with three level LEDs each, BOM SSW-BTN-640. */
            attribute :>> heatingKeys = 1;
            attribute :>> coolingKeys = 1;
            attribute :>> massageKeys = 1;
        }
    }

    // top-level, so its SW components and units are classified by ownership
    #Software part <'SSW-PC-016'> switchFirmware {
        doc /* Switch firmware on the microcontroller SSW-PC-017, module SSW-SW-700, in six SW components. */

        #Software part <'SSW-PC-023'> bootManager {
            doc /* SW component: secure boot, module SSW-SW-710. */
            #Software port imageStatus : ~ImageStatusPort;
            #Software part <'SSW-PC-024'> signatureCheck {
                doc /* SW unit: verifies the application image's ECDSA signature against the public key in write-protected flash. */
                #Software port verdict;
            }
            #Software part <'SSW-PC-025'> bootSelector {
                doc /* SW unit: starts the application if its signature verifies, otherwise stays in boot mode and accepts a reflash. */
                #Software port verdict;
                #Software port imageStatus;
            }
            connect signatureCheck.verdict to bootSelector.verdict;
            bind imageStatus = bootSelector.imageStatus;
        }

        #Software part <'SSW-PC-026'> inputProcessing {
            doc /* SW component: turns switch contacts and hall sensor readings into key states, module SSW-SW-720. */
            #Software port keyStates : SignalPort;
            #Software port faults : FaultPort;
            #Software part <'SSW-PC-027'> keyScan {
                doc /* SW unit: reads the switch contacts of the coded button set. */
                #Software port raw;
            }
            #Software part <'SSW-PC-028'> hallEvaluation {
                doc /* SW unit: reads the 3D hall sensors over SPI and turns field vectors into knob and lumbar pad directions. */
                #Software port raw;
            }
            #Software part <'SSW-PC-029'> debouncer {
                doc /* SW unit: accepts an input after 10 ms stable, reports a key held for more than 30 s as stuck. */
                #Software port raw;
                #Software port accepted;
                #Software port stuck;
            }
            #Software part <'SSW-PC-030'> signalMapping {
                doc /* SW unit: maps accepted directions and key presses to the status frame signals. */
                #Software port accepted;
                #Software port keyStates;
            }
            connect keyScan.raw to debouncer.raw;
            connect hallEvaluation.raw to debouncer.raw;
            connect debouncer.accepted to signalMapping.accepted;
            bind keyStates = signalMapping.keyStates;
            bind faults = debouncer.stuck;
        }

        #Software part <'SSW-PC-031'> illuminationControl {
            doc /* SW component: night design and comfort level indication, module SSW-SW-730. */
            #Software port commands : SignalPort;
            #Software port faults : FaultPort;
            #Software part <'SSW-PC-032'> ledControl {
                doc /* SW unit: sets the PWM duty of the symbol LEDs from the dimming level and lights the level LEDs from the comfort levels. */
                #Software port commands;
            }
            #Software part <'SSW-PC-033'> ledMonitor {
                doc /* SW unit: reads the LED driver's open-LED flags and reports a defective LED. */
                #Software port faults;
            }
            bind commands = ledControl.commands;
            bind faults = ledMonitor.faults;
        }

        #Software part <'SSW-PC-034'> linStack {
            doc /* SW component: LIN 2.2A slave at 19.2 kbit/s with enhanced checksum, module SSW-SW-740. */
            #Software port <'SSW-PI-004'> signals : SignalPort;
            #Software port diagnostics : DiagnosticPort;
            #Software port coding : ~CodingPort;
            #Software part <'SSW-PC-035'> linDriver {
                doc /* SW unit: UART driver, break and sync field detection, transceiver mode control. */
                #Software port bytes;
                #Software port mode;
            }
            #Software part <'SSW-PC-036'> linProtocol {
                doc /* SW unit: protected identifier parity, enhanced checksum and frame handling per the LDF schedule. */
                #Software port bytes;
                #Software port frames;
            }
            #Software part <'SSW-PC-037'> signalInterface {
                doc /* SW unit: packs the status frame and unpacks the command frame per the LDF, checks alive counter and signal ranges. */
                #Software port frames;
                #Software port signals;
            }
            #Software part <'SSW-PC-038'> nodeConfiguration {
                doc /* SW unit: node address (NAD) from end-of-line coding, LIN 2.2A node configuration services (AssignFrameIdRange, ReadByIdentifier). */
                #Software port frames;
                #Software port coding;
            }
            #Software part <'SSW-PC-039'> transportLayer {
                doc /* SW unit: LIN transport layer, segments UDS messages into master request (0x3C) and slave response (0x3D) frames. */
                #Software port frames;
                #Software port diagnostics;
            }
            #Software part <'SSW-PC-040'> networkManagement {
                doc /* SW unit: go-to-sleep command, bus idle timeout and wake-up, transceiver sleep mode. */
                #Software port frames;
                #Software port mode;
            }
            connect linDriver.bytes to linProtocol.bytes;
            connect linProtocol.frames to signalInterface.frames;
            connect linProtocol.frames to nodeConfiguration.frames;
            connect linProtocol.frames to transportLayer.frames;
            connect linProtocol.frames to networkManagement.frames;
            connect networkManagement.mode to linDriver.mode;
            bind signals = signalInterface.signals;
            bind diagnostics = transportLayer.diagnostics;
            bind coding = nodeConfiguration.coding;
        }

        #Software part <'SSW-PC-041'> diagnosticsManager {
            doc /* SW component: UDS diagnostics with security access, fault memory and end-of-line services, module SSW-SW-750. */
            #Software port requests : DiagnosticPort;
            #Software port faults : ~FaultPort;
            #Software port coding : CodingPort;
            #Software port download : DownloadPort;
            #Software part <'SSW-PC-042'> udsServer {
                doc /* SW unit: dispatches UDS services (identification, fault memory, routines, download) and checks session and security level. */
                #Software port requests;
                #Software port services;
                #Software port download;
            }
            #Software part <'SSW-PC-043'> securityAccess {
                doc /* SW unit: certificate-based tester authentication, unlocks write and flash services, locks out after failed attempts. */
                #Software port services;
            }
            #Software part <'SSW-PC-044'> faultMemory {
                doc /* SW unit: stores diagnostic trouble codes in non-volatile memory, reads and clears them. */
                #Software port services;
                #Software port faults;
            }
            #Software part <'SSW-PC-045'> endOfLineServices {
                doc /* SW unit: end-of-line test mode and variant coding: button set and node address (NAD) per seat position. */
                #Software port services;
                #Software port coding;
            }
            bind requests = udsServer.requests;
            bind download = udsServer.download;
            connect udsServer.services to securityAccess.services;
            connect udsServer.services to faultMemory.services;
            connect udsServer.services to endOfLineServices.services;
            bind faults = faultMemory.faults;
            bind coding = endOfLineServices.coding;
        }

        #Software part <'SSW-PC-046'> updateManager {
            doc /* SW component: firmware download over UDS and activation of verified images, module SSW-SW-760. */
            #Software port download : ~DownloadPort;
            #Software port imageStatus : ImageStatusPort;
            #Software part <'SSW-PC-047'> flashDownload {
                doc /* SW unit: erases and programs the application flash from UDS RequestDownload and TransferData. */
                #Software port download;
                #Software port image;
            }
            #Software part <'SSW-PC-048'> imageActivation {
                doc /* SW unit: verifies the downloaded image's signature and marks it valid for the boot manager. */
                #Software port image;
                #Software port imageStatus;
            }
            bind download = flashDownload.download;
            connect flashDownload.image to imageActivation.image;
            bind imageStatus = imageActivation.imageStatus;
        }

        connect inputProcessing.keyStates to linStack.signals;
        connect linStack.signals to illuminationControl.commands;
        connect linStack.diagnostics to diagnosticsManager.requests;
        connect inputProcessing.faults to diagnosticsManager.faults;
        connect illuminationControl.faults to diagnosticsManager.faults;
        connect diagnosticsManager.coding to linStack.coding;
        connect diagnosticsManager.download to updateManager.download;
        connect updateManager.imageStatus to bootManager.imageStatus;
    }

    part seatSwitchAssembly : SwitchAssembly {
        doc /* The switch as delivered: housing, button set and PCB assembly behind the vehicle connector, and the firmware. */
        ref part housing :> SeatSwitchPhysical::housing;
        ref part knob :> SeatSwitchPhysical::knob;
        ref part buttonCaps :> SeatSwitchPhysical::buttonCaps;
        ref part seal :> SeatSwitchPhysical::seal;
        ref part pcb :> SeatSwitchPhysical::pcb;
        ref part buttonSet :> SeatSwitchPhysical::buttonSet;
        ref part vehicleConnector :> SeatSwitchPhysical::vehicleConnector;
        ref part switchFirmware :> SeatSwitchPhysical::switchFirmware;

        // the boundary ports reach the vehicle through the connector pins
        bind supply = vehicleConnector.pin1Kl30;
        bind ground = vehicleConnector.pin2Kl31;
        bind lin = vehicleConnector.pin3Lin;
        connect vehicleConnector.pin1Kl30 to pcb.kl30;
        connect vehicleConnector.pin2Kl31 to pcb.kl31;
        connect vehicleConnector.pin3Lin to pcb.linBus;
        connect buttonSet.contacts to pcb.keyContacts;
        connect pcb.levelLedDrive to buttonSet.levelLeds;
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
    allocate seatSwitch.positionSensing to pcb.hallSensors;
    allocate seatSwitch.switchController to pcb.microcontroller;
    allocate seatSwitch.powerSupply to pcb.voltageRegulator;
    allocate seatSwitch.powerSupply to pcb.reversePolarityProtection;
    allocate seatSwitch.powerSupply to vehicleConnector;
    allocate seatSwitch.linCommunication to pcb.linTransceiver;
    allocate seatSwitch.linCommunication to pcb.linEsdProtection;
    allocate seatSwitch.linCommunication to vehicleConnector;
    allocate seatSwitch.illumination to pcb.ledDrivers;
    allocate seatSwitch.illumination to pcb.leds;
    // logical components go to SW components, never to SW units
    allocate seatSwitch.switchController to switchFirmware.bootManager;
    allocate seatSwitch.switchController to switchFirmware.inputProcessing;
    allocate seatSwitch.illumination to switchFirmware.illuminationControl;
    allocate seatSwitch.linCommunication to switchFirmware.linStack;
    allocate seatSwitch.switchController to switchFirmware.diagnosticsManager;
    allocate seatSwitch.switchController to switchFirmware.updateManager;

    allocate seatSwitch.enclosure.trimMount to housing.housingLH.clipsLH;
    allocate seatSwitch.enclosure.trimMount to housing.housingRH.clipsRH;
    allocate seatSwitch.linCommunication.vehicleBus to vehicleConnector.pin3Lin;
    allocate seatSwitch.powerSupply.vehicleSupply to vehicleConnector.pin1Kl30;
    allocate seatSwitch.linCommunication.controllerLink to switchFirmware.linStack.signals;
}
