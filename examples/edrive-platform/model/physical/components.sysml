package EDrivePhysical {
    doc /* P layer: the parts that are built and shipped, one engineering domain each, with the
     * logical components and interfaces allocated to them. Each doc names the BOM part number. */

    private import Trace::*;
    private import EDriveLogical::*;

    // the variant is chosen per vehicle program; both members are platform parts
    #Electrical variation part <'EDU-PC-001'> motor {
        doc /* Permanent-magnet synchronous motor family, BOM EDU-MOT-1000. */
        variant #Electrical part <'EDU-PC-002'> motor50kW { doc /* 50 kW continuous, BOM EDU-MOT-1050. */ }
        variant #Electrical part <'EDU-PC-003'> motor80kW { doc /* 80 kW continuous, BOM EDU-MOT-1080. */ }
    }
    #Electrical part <'EDU-PC-004'> inverter {
        doc /* 400 V silicon-carbide traction inverter, BOM EDU-INV-2000. */
        #Electrical port <'EDU-PI-001'> phaseTerminals;
    }
    #Software part <'EDU-PC-005'> controllerFirmware {
        doc /* Drive control firmware on the inverter control board, BOM EDU-SW-3000. */
        #Software port <'EDU-PI-002'> canTorqueMessage;
    }
    #Mechanical part <'EDU-PC-006'> housing {
        doc /* Cast aluminium housing shared by both motor variants, BOM EDU-HSG-4000. */
        #Mechanical port <'EDU-PI-003'> mountingFlange;
    }

    allocate eDrive.motor to motor.motor50kW;
    allocate eDrive.motor to motor.motor80kW;
    allocate eDrive.inverter to inverter;
    allocate eDrive.driveController to controllerFirmware;
    allocate eDrive.housing to housing;

    allocate eDrive.inverter.phaseOut to inverter.phaseTerminals;
    allocate eDrive.driveController.vehicleBus to controllerFirmware.canTorqueMessage;
    allocate eDrive.housing.vehicleMount to housing.mountingFlange;
}
