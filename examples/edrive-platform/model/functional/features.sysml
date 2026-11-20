package EDriveFeatures {
    doc /* F layer: what the product line sells (features, noun names) and the functions each
     * feature owns, independent of how they are built. */

    private import Trace::*;

    #Feature action <'EDU-FEAT-001'> tractionDrive {
        doc /* Wheel torque on demand from battery power. */
        action <'EDU-F-001'> controlTorque {
            doc /* Turn a torque request into a current setpoint. */
            action <'EDU-F-002'> receiveTorqueRequest { doc /* Read the torque request from the vehicle. */ }
            action <'EDU-F-003'> computeCurrentSetpoint { doc /* Derive phase current from requested torque and speed. */ }
            first receiveTorqueRequest then computeCurrentSetpoint;
        }
        action <'EDU-F-004'> convertPower { doc /* Convert battery DC into three-phase AC. */ }
        action <'EDU-F-005'> produceTorque { doc /* Convert electrical power into shaft torque. */ }
        action <'EDU-F-006'> carryReactionLoads { doc /* Transfer torque reaction and mass loads to the vehicle. */ }

        first controlTorque then convertPower;
        first convertPower then produceTorque;
    }

    #Feature action <'EDU-FEAT-002'> regenerativeBraking {
        doc /* Braking energy returned to the battery. */
        action <'EDU-F-007'> limitRecoveryCurrent { doc /* Cap recovery current to what the battery accepts. */ }
        action <'EDU-F-008'> generatePower { doc /* Convert shaft torque into electrical power. */ }
        action <'EDU-F-009'> rectifyPower { doc /* Convert three-phase AC into battery DC. */ }

        first generatePower then rectifyPower;
    }
}
