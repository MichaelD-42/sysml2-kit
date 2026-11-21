package EDriveItems {
    doc /* What flows through the drive unit and across its boundary, and the interfaces that carry it. */

    item def ElectricPower { doc /* High-voltage electrical power, DC from the battery or AC to the motor. */ }
    item def ShaftTorque { doc /* Mechanical torque on the rotor shaft. */ }
    item def TorqueRequest { doc /* Torque setpoint sent by the vehicle over CAN. */ }
    item def Coolant { doc /* Water-glycol coolant. */ }

    port def HighVoltagePort { doc /* Supplies high-voltage power. */ out item power : ElectricPower; }
    port def CanPort { doc /* Sends torque requests on the vehicle CAN bus. */ out item request : TorqueRequest; }
    port def CoolantPort { doc /* Delivers coolant. */ out item coolant : Coolant; }
    port def MountPort { doc /* Carries mass and torque reaction loads. */ }

    interface def HighVoltageInterface {
        doc /* High-voltage connection from a power source to a consumer. */
        end port source : HighVoltagePort;
        end port sink : ~HighVoltagePort;
    }
    interface def CanInterface {
        doc /* CAN connection from the vehicle network to a controller. */
        end port sender : CanPort;
        end port receiver : ~CanPort;
    }
    interface def CoolantInterface {
        doc /* Coolant line from an outlet to an inlet. */
        end port outlet : CoolantPort;
        end port inlet : ~CoolantPort;
    }
    interface def MountInterface {
        doc /* Bolted joint between a carrier and the part it holds. */
        end port carrier : ~MountPort;
        end port carried : MountPort;
    }
}
