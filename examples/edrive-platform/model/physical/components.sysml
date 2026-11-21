package EDrivePhysical {
    doc /* P layer: the parts that are built and shipped, one engineering domain each, with the
     * logical components and interfaces allocated to them. Each doc names the BOM part number. */

    private import Trace::*;
    private import EDriveLogical::*;
    private import EDriveItems::*;
    private import ISQ::*;
    private import SI::*;
    private import ScalarValues::String;

    // a variation owns only its variants, so the motor's characteristics live in its definition
    part def Motor {
        doc /* Characteristics every motor variant states. */
        attribute ratedPower : PowerValue;
        attribute peakTorque : TorqueValue;
        attribute mass : MassValue;
        attribute maxSpeed : AngularVelocityValue;
        port phaseWindings : ~HighVoltagePort;
        port coolantInlet : ~CoolantPort;
        port coolantOutlet : CoolantPort;
        constraint peakTorqueLimit { peakTorque <= 400 [N*m] }
    }

    // the variant is chosen per vehicle program; both members are platform parts
    #Electrical variation part <'EDU-PC-001'> motor : Motor {
        doc /* Permanent-magnet synchronous motor family, BOM EDU-MOT-1000. */
        variant #Electrical part <'EDU-PC-002'> motor50kW {
            doc /* 50 kW continuous, BOM EDU-MOT-1050. */
            attribute :>> ratedPower = 50 [kW];
            attribute :>> peakTorque = 250 [N*m];
            attribute :>> mass = 38 [kg];
            attribute :>> maxSpeed = 1680 [rad/s];
        }
        variant #Electrical part <'EDU-PC-003'> motor80kW {
            doc /* 80 kW continuous, BOM EDU-MOT-1080. */
            attribute :>> ratedPower = 80 [kW];
            attribute :>> peakTorque = 350 [N*m];
            attribute :>> mass = 46 [kg];
            attribute :>> maxSpeed = 1680 [rad/s];
        }
    }
    #Electrical part <'EDU-PC-004'> inverter {
        doc /* 400 V silicon-carbide traction inverter, BOM EDU-INV-2000. */
        attribute dcLinkVoltage : ElectricPotentialDifferenceValue = 400 [V];
        attribute maxCoolantTemperature : ThermodynamicTemperatureValue = 65 ['°C'];
        #Electrical port <'EDU-PI-001'> phaseTerminals : HighVoltagePort;
        port dcTerminals : ~HighVoltagePort;
        port coolantInlet : ~CoolantPort;
        port coolantOutlet : CoolantPort;
        // above the coolant limit the inverter derates its output current
        constraint coolantDerating {
            in coolantTemperature : ThermodynamicTemperatureValue;
            coolantTemperature <= maxCoolantTemperature
        }
    }
    #Software part <'EDU-PC-005'> controllerFirmware {
        doc /* Drive control firmware on the inverter control board, BOM EDU-SW-3000. */
        #Software port <'EDU-PI-002'> canTorqueMessage : ~CanPort;
    }
    #Mechanical part <'EDU-PC-006'> housing {
        doc /* Cast aluminium housing shared by both motor variants, BOM EDU-HSG-4000. */
        attribute ipRating : String = "IP67";
        attribute mass : MassValue = 22 [kg];
        #Mechanical port <'EDU-PI-003'> mountingFlange : MountPort;
    }

    part eDriveUnit {
        doc /* The drive unit as delivered: motor, inverter, firmware and housing behind five ports. */
        ref part motor :> EDrivePhysical::motor;
        ref part inverter :> EDrivePhysical::inverter;
        ref part controllerFirmware :> EDrivePhysical::controllerFirmware;
        ref part housing :> EDrivePhysical::housing;

        port hvIn : ~HighVoltagePort;
        port canBus : ~CanPort;
        port coolantIn : ~CoolantPort;
        port coolantOut : CoolantPort;
        port mount : MountPort;

        interface : HighVoltageInterface connect inverter.phaseTerminals to motor.phaseWindings;
        interface : CoolantInterface connect inverter.coolantOutlet to motor.coolantInlet;

        bind hvIn = inverter.dcTerminals;
        bind canBus = controllerFirmware.canTorqueMessage;
        bind coolantIn = inverter.coolantInlet;
        bind coolantOut = motor.coolantOutlet;
        bind mount = housing.mountingFlange;
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
