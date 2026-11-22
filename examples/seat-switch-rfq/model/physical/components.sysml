package SeatSwitchRfqPhysical {
    doc /* P layer: per seat position, the platform housing and button-set variants it selects. Everything
     * else is the platform switch as it is (SeatSwitchPhysical). A constraint on each selection states the
     * customer's position table: which side's housing and which comfort keys that seat gets. */

    private import Trace::*;
    private import SeatSwitchRfqLogical::*;
    private import SeatSwitchPhysical::housing;
    private import SeatSwitchPhysical::buttonSet;

    // driver seat, left-hand drive
    #Mechanical part <'PC-101'> driverHousing :> housing::housingLH {
        doc /* Platform left-hand housing for the driver seat, BOM SSW-HSG-110. */
        constraint <'CON-113'> driverHousingSide {
            @Satisfies { need = "CRS-704"; }
            doc /* The driver switch housing shall be keyed to the left-hand trim opening. */
            codingRib == "left-hand"
        }
    }
    #Electrical part <'PC-102'> driverButtonSet :> buttonSet::massageHeatingCooling {
        doc /* Platform massage, heating and cooling button set for the driver seat, BOM SSW-BTN-640. */
        constraint <'CON-114'> driverComfortKeys {
            @Satisfies { need = "CRS-203"; }
            doc /* The driver switch shall have one massage, one heating and one cooling key. */
            massageKeys == 1 and heatingKeys == 1 and coolingKeys == 1
        }
    }

    #Mechanical part <'PC-103'> coDriverHousing :> housing::housingRH {
        doc /* Platform right-hand housing for the co-driver seat, BOM SSW-HSG-120. */
        constraint <'CON-115'> coDriverHousingSide {
            @Satisfies { need = "CRS-704"; }
            doc /* The co-driver switch housing shall be keyed to the right-hand trim opening. */
            codingRib == "right-hand"
        }
    }
    #Electrical part <'PC-104'> coDriverButtonSet :> buttonSet::heatingCooling {
        doc /* Platform heating and cooling button set for the co-driver seat, BOM SSW-BTN-630. */
        constraint <'CON-116'> coDriverComfortKeys {
            @Satisfies { need = "CRS-203"; }
            doc /* The co-driver switch shall have one heating and one cooling key and no massage key. */
            massageKeys == 0 and heatingKeys == 1 and coolingKeys == 1
        }
    }

    #Mechanical part <'PC-105'> rearLeftHousing :> housing::housingLH {
        doc /* Platform left-hand housing for the rear left seat, BOM SSW-HSG-110. */
        constraint <'CON-117'> rearLeftHousingSide {
            @Satisfies { need = "CRS-704"; }
            doc /* The rear left switch housing shall be keyed to the left-hand trim opening. */
            codingRib == "left-hand"
        }
    }
    #Electrical part <'PC-106'> rearLeftButtonSet :> buttonSet::heating {
        doc /* Platform heating button set for the rear left seat, BOM SSW-BTN-620. */
        constraint <'CON-118'> rearLeftComfortKeys {
            @Satisfies { need = "CRS-203"; }
            doc /* The rear left switch shall have one heating key and no cooling or massage key. */
            massageKeys == 0 and heatingKeys == 1 and coolingKeys == 0
        }
    }

    #Mechanical part <'PC-107'> rearRightHousing :> housing::housingRH {
        doc /* Platform right-hand housing for the rear right seat, BOM SSW-HSG-120. */
        constraint <'CON-119'> rearRightHousingSide {
            @Satisfies { need = "CRS-704"; }
            doc /* The rear right switch housing shall be keyed to the right-hand trim opening. */
            codingRib == "right-hand"
        }
    }
    #Electrical part <'PC-108'> rearRightButtonSet :> buttonSet::heating {
        doc /* Platform heating button set for the rear right seat, BOM SSW-BTN-620. */
        constraint <'CON-120'> rearRightComfortKeys {
            @Satisfies { need = "CRS-203"; }
            doc /* The rear right switch shall have one heating key and no cooling or massage key. */
            massageKeys == 0 and heatingKeys == 1 and coolingKeys == 0
        }
    }

    allocate OEM_SeatSwitch.driverSwitch to driverHousing;
    allocate OEM_SeatSwitch.driverSwitch to driverButtonSet;
    allocate OEM_SeatSwitch.coDriverSwitch to coDriverHousing;
    allocate OEM_SeatSwitch.coDriverSwitch to coDriverButtonSet;
    allocate OEM_SeatSwitch.rearLeftSwitch to rearLeftHousing;
    allocate OEM_SeatSwitch.rearLeftSwitch to rearLeftButtonSet;
    allocate OEM_SeatSwitch.rearRightSwitch to rearRightHousing;
    allocate OEM_SeatSwitch.rearRightSwitch to rearRightButtonSet;
}
