package WindowSwitchPhysical {
    doc /* P layer: the parts that are built and shipped, one engineering domain each, with the
     * logical components and interfaces allocated to them. Each doc names the BOM part number. */

    private import Trace::*;
    private import WindowSwitchLogical::*;
    private import WindowSwitchItems::*;
    private import ISQ::*;
    private import SI::*;
    private import ScalarValues::String;
    private import ScalarValues::Integer;
    private import ScalarValues::Boolean;

    // what every assembled switch states, and the platform's limits on it as constraints (plain values included)
    part def SwitchAssembly {
        doc /* An assembled window switch, whatever its key module and backlight: the platform's rated values
         * and its three ports. */
        attribute actuationForce : ForceValue = 5 [N];
        attribute minOperatingVoltage : ElectricPotentialDifferenceValue = 9 [V];
        attribute maxOperatingVoltage : ElectricPotentialDifferenceValue = 16 [V];
        attribute minOperatingTemperature : ThermodynamicTemperatureValue = -40 ['°C'];
        attribute maxOperatingTemperature : ThermodynamicTemperatureValue = 85 ['°C'];
        attribute ipRating : String = "IP5K3";
        attribute durabilityCycles : Integer = 100000;
        attribute linVersion : String = "2.2A";
        attribute mass : MassValue = 42 [g];
        // 40 µA with the bus asleep: the transceiver in sleep mode and the regulator's leakage
        attribute quiescentCurrent : ElectricCurrentValue = 0.00004 [A];
        // LIN node address, set per door position; the platform sets no value
        attribute nad : Integer;

        port lin : LinPort;
        port supply : ~PowerPort;
        port ground : GroundPort;

        constraint <'WSW-CON-001'> actuationForceWindow {
            @Satisfies { need = "WSW-PRQ-005"; }
            doc /* The first-stage actuation force of every key shall be 3.5 N to 7.0 N. */
            actuationForce >= 3.5 [N] and actuationForce <= 7.0 [N]
        }
        constraint <'WSW-CON-002'> keyDurability {
            @Satisfies { need = "WSW-PRQ-006"; }
            doc /* Every key shall withstand at least 100 000 actuations of each stage. */
            durabilityCycles >= 100000
        }
        constraint <'WSW-CON-003'> operatingVoltageRange {
            @Satisfies { need = "WSW-PRQ-007"; }
            doc /* The switch shall operate from 9 V to 16 V. */
            minOperatingVoltage <= 9 [V] and maxOperatingVoltage >= 16 [V]
        }
        constraint <'WSW-CON-004'> operatingTemperatureRange {
            @Satisfies { need = "WSW-PRQ-008"; }
            doc /* The switch shall operate from -40 °C to +85 °C. */
            minOperatingTemperature <= -40 ['°C'] and maxOperatingTemperature >= 85 ['°C']
        }
        constraint <'WSW-CON-005'> ingressProtection {
            @Satisfies { need = "WSW-PRQ-009"; }
            doc /* The switch shall be rated IP5K3. */
            ipRating == "IP5K3"
        }
        constraint <'WSW-CON-006'> linProtocolVersion {
            @Satisfies { need = "WSW-PRQ-010"; }
            doc /* The switch shall implement LIN protocol version 2.2A. */
            linVersion == "2.2A"
        }
    }

    // a variation owns only its variants, so their characteristics live in the definitions
    part def KeyModule {
        doc /* Characteristics every key module states. */
        attribute windowKeys : Integer;
        attribute childLockKey : Boolean;
        port contacts : KeyPort;
    }
    part def Backlight {
        doc /* Characteristics every backlight states. */
        attribute colour : String;
        port drive : ~LedDrivePort;
    }

    #Mechanical part <'WSW-PC-001'> housing {
        doc /* PBT-GF30 housing with snap-fit clips into the door trim, BOM WSW-HSG-100. */
        #Mechanical port <'WSW-PI-001'> clips : ClipPort;
    }
    #Mechanical part <'WSW-PC-002'> keyCaps {
        doc /* Two-stage rocker key caps with laser-etched symbol windows, BOM WSW-CAP-200; the caps follow the key module. */
    }
    #Mechanical part <'WSW-PC-003'> seal {
        doc /* Silicone keymat seal between caps and PCB, BOM WSW-SEL-300. */
    }

    // the key contacts sit on the PCB; the key module decides which are fitted, an RFQ selects one per door
    variation #Electrical part <'WSW-PC-004'> keyModule : KeyModule {
        doc /* Key contact population of the PCB, two-stage tact switches per window key, BOM WSW-KEY-400. */
        variant #Electrical part <'WSW-PC-005'> fourKey {
            doc /* Driver door: four window keys and the child-lock key, BOM WSW-KEY-410. */
            attribute :>> windowKeys = 4;
            attribute :>> childLockKey = true;
        }
        variant #Electrical part <'WSW-PC-006'> oneKey {
            doc /* Passenger or rear door: one window key, BOM WSW-KEY-420. */
            attribute :>> windowKeys = 1;
            attribute :>> childLockKey = false;
        }
    }
    variation #Electrical part <'WSW-PC-007'> backlight : Backlight {
        doc /* Symbol backlight LEDs, BOM WSW-LED-500. */
        variant #Electrical part <'WSW-PC-008'> whiteLeds {
            doc /* White symbol LEDs, BOM WSW-LED-510. */
            attribute :>> colour = "white";
        }
        variant #Electrical part <'WSW-PC-009'> amberLeds {
            doc /* Amber symbol LEDs, BOM WSW-LED-520. */
            attribute :>> colour = "amber";
        }
    }

    #Electrical part <'WSW-PC-010'> pcb {
        doc /* Main PCB assembly, BOM WSW-PCB-600. Every part returns to KL31 on the ground plane. */
        #Electrical port kl30 : ~PowerPort;
        #Electrical port linBus : LinPort;
        #Electrical port keyContacts : ~KeyPort;
        #Electrical port backlightDrive : LedDrivePort;

        #Electrical part <'WSW-PC-011'> voltageRegulator {
            doc /* Reverse-polarity diode and 5 V low-dropout regulator for the microcontroller, BOM WSW-REG-610. */
            #Electrical port input : ~PowerPort;
            #Electrical port output : PowerPort;
        }
        #Electrical part <'WSW-PC-012'> microcontroller {
            doc /* 16-bit automotive microcontroller with UART and PWM timers; runs the firmware WSW-PC-016, BOM WSW-MCU-620. */
            #Electrical port supply : ~PowerPort;
            #Electrical port uart : UartPort;
            #Electrical port keyInputs : ~KeyPort;
            #Electrical port pwm : PwmPort;
        }
        #Electrical part <'WSW-PC-013'> linTransceiver {
            doc /* LIN 2.2A transceiver with bus wake-up detection, BOM WSW-LIN-630. */
            #Electrical port <'WSW-PI-002'> linPin : LinPort;
            #Electrical port uart : ~UartPort;
        }
        #Electrical part <'WSW-PC-014'> ledDriver {
            doc /* Constant-current LED driver, one PWM-dimmed channel for the symbols and one for the telltale, BOM WSW-LDR-640. */
            #Electrical port pwm : ~PwmPort;
            #Electrical port drive : LedDrivePort;
        }

        bind kl30 = voltageRegulator.input;
        connect voltageRegulator.output to microcontroller.supply;
        bind linBus = linTransceiver.linPin;
        connect linTransceiver.uart to microcontroller.uart;
        bind keyContacts = microcontroller.keyInputs;
        connect microcontroller.pwm to ledDriver.pwm;
        bind backlightDrive = ledDriver.drive;
    }
    #Electrical part <'WSW-PC-015'> vehicleConnector {
        doc /* 4-pin connector header to the door harness, BOM WSW-CON-700. Pin 1 KL30, pin 2 KL31 (also the LIN reference), pin 3 LIN, pin 4 not used. */
        #Electrical port <'WSW-PI-003'> pin1Kl30 : ~PowerPort { doc /* KL30, permanent 12 V supply. */ }
        #Electrical port <'WSW-PI-004'> pin2Kl31 : GroundPort { doc /* KL31, ground and LIN reference. */ }
        #Electrical port <'WSW-PI-005'> pin3Lin : LinPort { doc /* LIN bus. */ }
        #Electrical port pin4 { doc /* Not used. */ }
    }

    // top-level, so its SW components and units are classified by ownership
    #Software part <'WSW-PC-016'> switchFirmware {
        doc /* Switch firmware on the microcontroller WSW-PC-012, module WSW-SW-800, in three SW components. */
        #Software part <'WSW-PC-017'> inputProcessing {
            doc /* SW component: scans and debounces the keys and maps them to signals, module WSW-SW-810. */
            #Software port keyStates : SignalPort;
            #Software part <'WSW-PC-018'> keyScan {
                doc /* SW unit: samples both stages of every key contact every 2 ms. */
                #Software port raw;
            }
            #Software part <'WSW-PC-019'> debouncer {
                doc /* SW unit: accepts a stage after 10 ms stable and maps it to its window signal. */
                #Software port raw;
                #Software port accepted;
            }
            connect keyScan.raw to debouncer.raw;
            bind keyStates = debouncer.accepted;
        }
        #Software part <'WSW-PC-020'> linStack {
            doc /* SW component: LIN 2.2A slave stack, module WSW-SW-820. */
            #Software port <'WSW-PI-006'> signals : SignalPort;
            #Software part <'WSW-PC-021'> linDriver {
                doc /* SW unit: UART bytes, break and sync detection, checksum, node address. */
                #Software port bytes;
            }
            #Software part <'WSW-PC-022'> signalInterface {
                doc /* SW unit: packs and unpacks signals per the LDF and checks alive counters and ranges. */
                #Software port bytes;
                #Software port signals;
            }
            connect linDriver.bytes to signalInterface.bytes;
            bind signals = signalInterface.signals;
        }
        #Software part <'WSW-PC-023'> illuminationControl {
            doc /* SW component: symbol dimming and telltale, module WSW-SW-830. */
            #Software port commands : SignalPort;
            #Software part <'WSW-PC-024'> ledControl {
                doc /* SW unit: sets the PWM duty from the dimming level and switches the telltale. */
                #Software port commands;
            }
            bind commands = ledControl.commands;
        }

        connect inputProcessing.keyStates to linStack.signals;
        connect linStack.signals to illuminationControl.commands;
    }

    #Assembly part <'WSW-PC-025'> windowSwitchAssembly : SwitchAssembly {
        doc /* The switch as delivered: housing, key module, backlight and PCB assembly behind the vehicle connector, and the firmware. */
        ref part housing :> WindowSwitchPhysical::housing;
        ref part keyCaps :> WindowSwitchPhysical::keyCaps;
        ref part seal :> WindowSwitchPhysical::seal;
        ref part keyModule :> WindowSwitchPhysical::keyModule;
        ref part backlight :> WindowSwitchPhysical::backlight;
        ref part pcb :> WindowSwitchPhysical::pcb;
        ref part vehicleConnector :> WindowSwitchPhysical::vehicleConnector;
        ref part switchFirmware :> WindowSwitchPhysical::switchFirmware;

        // the boundary ports reach the vehicle through the connector pins
        bind supply = vehicleConnector.pin1Kl30;
        bind ground = vehicleConnector.pin2Kl31;
        bind lin = vehicleConnector.pin3Lin;
        connect vehicleConnector.pin1Kl30 to pcb.kl30;
        connect vehicleConnector.pin3Lin to pcb.linBus;
        connect keyModule.contacts to pcb.keyContacts;
        connect pcb.backlightDrive to backlight.drive;
    }

    allocate ACME_WindowSwitch to windowSwitchAssembly;
    allocate ACME_WindowSwitch.enclosure to housing;
    allocate ACME_WindowSwitch.enclosure to keyCaps;
    allocate ACME_WindowSwitch.enclosure to seal;
    // allocation to each variant offers it; an RFQ selects one by subsetting it
    allocate ACME_WindowSwitch.keySensing to keyModule.fourKey;
    allocate ACME_WindowSwitch.keySensing to keyModule.oneKey;
    allocate ACME_WindowSwitch.illumination to backlight.whiteLeds;
    allocate ACME_WindowSwitch.illumination to backlight.amberLeds;
    allocate ACME_WindowSwitch.switchController to pcb.microcontroller;
    allocate ACME_WindowSwitch.powerSupply to pcb.voltageRegulator;
    allocate ACME_WindowSwitch.powerSupply to vehicleConnector;
    allocate ACME_WindowSwitch.linCommunication to pcb.linTransceiver;
    allocate ACME_WindowSwitch.linCommunication to vehicleConnector;
    allocate ACME_WindowSwitch.illumination to pcb.ledDriver;
    // logical components go to SW components, never to SW units
    allocate ACME_WindowSwitch.switchController to switchFirmware.inputProcessing;
    allocate ACME_WindowSwitch.linCommunication to switchFirmware.linStack;
    allocate ACME_WindowSwitch.illumination to switchFirmware.illuminationControl;

    allocate ACME_WindowSwitch.enclosure.trimMount to housing.clips;
    allocate ACME_WindowSwitch.linCommunication.vehicleBus to vehicleConnector.pin3Lin;
    allocate ACME_WindowSwitch.powerSupply.vehicleSupply to vehicleConnector.pin1Kl30;
    allocate ACME_WindowSwitch.linCommunication.controllerLink to switchFirmware.linStack.signals;
}
