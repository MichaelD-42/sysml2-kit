package EDriveRequirements {
    doc /* R layer: what the e-drive shall do, derived from the platform requirements. */

    private import Trace::*;

    requirement <'EDU-SR-001'> continuousPower {
        @Satisfies { need = "EDU-PRQ-001"; }
        doc /* The drive shall deliver a continuous shaft power of 50 kW or 80 kW, per ordered variant. */
    }
    requirement <'EDU-SR-002'> recoveryPower {
        @Satisfies { need = "EDU-PRQ-002"; }
        doc /* The drive shall return at least 30 kW of braking power to the battery. */
    }
    requirement <'EDU-SR-003'> torqueResponse {
        @Satisfies { need = "EDU-PRQ-003"; }
        doc /* The drive shall reach a requested torque within 10 ms of receiving the request. */
    }
    requirement <'EDU-SR-004'> commonMounting {
        @Satisfies { need = "EDU-PRQ-004"; }
        doc /* The drive shall mount to the subframe at the same four M12 bolt points in every power variant. */
    }
}
