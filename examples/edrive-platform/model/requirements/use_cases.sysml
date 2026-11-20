package EDriveUseCases {
    doc /* R layer: how the vehicle uses the e-drive. Each use case realizes platform requirements
     * and is realized by the features it performs. */

    private import Trace::*;
    private import EDriveFeatures::*;

    use case <'EDU-UC-001'> driveVehicle {
        @Realizes { need = "EDU-PRQ-001"; }
        @Realizes { need = "EDU-PRQ-003"; }
        doc /* The driver requests torque with the pedal; the drive turns it into wheel torque. */
        subject eDrive;
        actor driver;
        actor vehicleControlUnit;
        perform tractionDrive;
    }

    use case <'EDU-UC-002'> recoverBrakingEnergy {
        @Realizes { need = "EDU-PRQ-002"; }
        doc /* The driver brakes; the drive runs as a generator and charges the battery. */
        subject eDrive;
        actor driver;
        actor vehicleControlUnit;
        perform regenerativeBraking;
    }
}
