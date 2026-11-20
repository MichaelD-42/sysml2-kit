package EDriveLogical {
    doc /* L layer: technology-neutral components and interfaces, the functions allocated to them,
     * and the system requirements they satisfy. */

    private import EDriveFeatures::*;
    private import EDriveRequirements::*;

    part <'EDU-LC-001'> eDrive {
        doc /* The electric drive unit as a whole. */
        part <'EDU-LC-002'> motor {
            doc /* Converts between electrical power and shaft torque. */
            port <'EDU-LI-001'> phaseIn;
        }
        part <'EDU-LC-003'> inverter {
            doc /* Converts between battery DC and motor AC. */
            port <'EDU-LI-002'> phaseOut;
        }
        part <'EDU-LC-004'> driveController {
            doc /* Decides the current setpoint from vehicle requests. */
            port <'EDU-LI-003'> vehicleBus;
        }
        part <'EDU-LC-005'> housing {
            doc /* Encloses the drive and carries its loads into the vehicle. */
            port <'EDU-LI-004'> vehicleMount;
        }

        connect inverter.phaseOut to motor.phaseIn;
    }

    allocate tractionDrive.controlTorque.receiveTorqueRequest to eDrive.driveController;
    allocate tractionDrive.controlTorque.computeCurrentSetpoint to eDrive.driveController;
    allocate tractionDrive.convertPower to eDrive.inverter;
    allocate tractionDrive.produceTorque to eDrive.motor;
    allocate tractionDrive.carryReactionLoads to eDrive.housing;
    allocate regenerativeBraking.limitRecoveryCurrent to eDrive.driveController;
    allocate regenerativeBraking.generatePower to eDrive.motor;
    allocate regenerativeBraking.rectifyPower to eDrive.inverter;

    satisfy continuousPower by eDrive.motor;
    satisfy recoveryPower by eDrive.inverter;
    satisfy torqueResponse by eDrive.driveController;
    satisfy commonMounting by eDrive.housing;
}
