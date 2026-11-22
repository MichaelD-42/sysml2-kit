package WindowSwitchRfqPhysical {
    doc /* P layer: the vehicle's window switch as built, the platform switch assembly within this RFQ's limits,
     * and the two switches of one vehicle, each selecting the platform key-module and backlight variants of
     * its door. Everything else is the platform switch as it is (WindowSwitchPhysical). A constraint on each
     * selection states the customer's door table: which keys and which symbol colour that door gets. */

    private import Trace::*;
    private import WindowSwitchRfqLogical::*;
    private import WindowSwitchPhysical::windowSwitchAssembly;
    private import ISQ::*;
    private import SI::*;

    // one switch: every limit here holds for each switch, in every door
    #Assembly part <'PC-100'> oemWindowSwitch :> windowSwitchAssembly {
        doc /* The vehicle's window switch as delivered: the platform switch assembly within this RFQ's limits. */

        constraint <'CON-101'> actuationForceLimits {
            @Satisfies { need = "CRS-301"; }
            doc /* The first-stage actuation force of every key shall be 3.0 N to 7.5 N. */
            actuationForce >= 3.0 [N] and actuationForce <= 7.5 [N]
        }
        // the platform is rated for 100 000 actuations (WSW-CON-002); the OEM asks for 150 000
        constraint <'CON-102'> keyDurabilityLimit {
            @Satisfies { need = "CRS-302"; partial = true; }
            doc /* Every key shall withstand at least 100 000 actuations of each stage. */
            durabilityCycles >= 100000
        }
        constraint <'CON-103'> linProtocol {
            @Satisfies { need = "CRS-402"; }
            doc /* The switch shall implement LIN 2.2A. */
            linVersion == "2.2A"
        }
        constraint <'CON-104'> supplyVoltageRange {
            @Satisfies { need = "CRS-501"; }
            doc /* The switch shall operate from 9 V to 16 V. */
            minOperatingVoltage <= 9 [V] and maxOperatingVoltage >= 16 [V]
        }
        constraint <'CON-105'> operatingTemperatureLimits {
            @Satisfies { need = "CRS-502"; }
            doc /* The switch shall operate from -40 °C to +85 °C. */
            minOperatingTemperature <= -40 ['°C'] and maxOperatingTemperature >= 85 ['°C']
        }
        constraint <'CON-106'> ingressRating {
            @Satisfies { need = "CRS-503"; }
            doc /* The switch shall be rated IP5K3. */
            ipRating == "IP5K3"
        }
        constraint <'CON-107'> quiescentCurrentLimit {
            @Satisfies { need = "CRS-504"; }
            doc /* With the LIN bus asleep, the switch shall draw at most 100 µA. */
            quiescentCurrent <= 0.0001 [A]
        }
        constraint <'CON-108'> switchMass {
            @Satisfies { need = "CRS-505"; }
            doc /* A switch shall weigh at most 50 g. */
            mass <= 50 [g]
        }
    }

    // the two switches of one vehicle; what holds between them is stated here
    #Assembly part <'PC-109'> vehicleDoorSwitches {
        doc /* The window switches fitted to one vehicle, one per front door. */

        // both switches share the door LIN, so each gets its own node address (CRS-404)
        constraint <'CON-109'> distinctNodeAddresses {
            @Satisfies { need = "CRS-404"; }
            doc /* The two door switches shall have different LIN node addresses. */
            driverDoorSwitch.nad != passengerDoorSwitch.nad
        }

        #Assembly part <'PC-110'> driverDoorSwitch :> oemWindowSwitch {
            doc /* Driver door (left-hand drive): the switch with its key module and backlight; LIN node address 0x2A. */
            attribute :>> nad = 42;
            #Electrical part <'PC-101'> driverKeyModule :>> keyModule :> WindowSwitchPhysical::keyModule::fourKey {
                doc /* Platform four-key module with the child-lock key for the driver door, BOM WSW-KEY-410. */
                constraint <'CON-110'> driverKeys {
                    @Satisfies { need = "CRS-201"; }
                    doc /* The driver switch shall have four window keys and the child-lock key. */
                    windowKeys == 4 and childLockKey == true
                }
            }
            #Electrical part <'PC-102'> driverBacklight :>> backlight :> WindowSwitchPhysical::backlight::whiteLeds {
                doc /* Platform white symbol LEDs for the driver door, BOM WSW-LED-510. */
                constraint <'CON-112'> driverSymbolColour {
                    @Satisfies { need = "CRS-303"; }
                    doc /* The driver switch's symbols shall be lit white. */
                    colour == "white"
                }
            }
        }
        #Assembly part <'PC-111'> passengerDoorSwitch :> oemWindowSwitch {
            doc /* Passenger door: the switch with its key module and backlight; LIN node address 0x2B. */
            attribute :>> nad = 43;
            #Electrical part <'PC-103'> passengerKeyModule :>> keyModule :> WindowSwitchPhysical::keyModule::oneKey {
                doc /* Platform one-key module for the passenger door, BOM WSW-KEY-420. */
                constraint <'CON-111'> passengerKeys {
                    @Satisfies { need = "CRS-201"; }
                    doc /* The passenger switch shall have one window key. */
                    windowKeys == 1
                }
            }
            #Electrical part <'PC-104'> passengerBacklight :>> backlight :> WindowSwitchPhysical::backlight::whiteLeds {
                doc /* Platform white symbol LEDs for the passenger door, BOM WSW-LED-510. */
                constraint <'CON-113'> passengerSymbolColour {
                    @Satisfies { need = "CRS-303"; }
                    doc /* The passenger switch's symbols shall be lit white. */
                    colour == "white"
                }
            }
        }
    }

    allocate OEM_WindowSwitch to oemWindowSwitch;
    allocate OEM_WindowSwitch.keySensing to vehicleDoorSwitches.driverDoorSwitch.driverKeyModule;
    allocate OEM_WindowSwitch.illumination to vehicleDoorSwitches.driverDoorSwitch.driverBacklight;
    allocate OEM_WindowSwitch.keySensing to vehicleDoorSwitches.passengerDoorSwitch.passengerKeyModule;
    allocate OEM_WindowSwitch.illumination to vehicleDoorSwitches.passengerDoorSwitch.passengerBacklight;
}
