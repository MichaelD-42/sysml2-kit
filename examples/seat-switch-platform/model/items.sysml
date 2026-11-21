package SeatSwitchItems {
    doc /* What flows through the seat switch and across its boundary, and the interfaces that carry it. */

    private import ScalarValues::Integer;
    private import ScalarValues::Boolean;

    item def KeyState { doc /* Pressed or released state of one key or knob direction. */ }
    item def FirmwareImage { doc /* A signed firmware image delivered over the diagnostic channel. */ }
    item def SupplyPower { doc /* 12 V vehicle supply (KL30). */ }
    item def Light { doc /* Light emitted through a key symbol. */ }

    // LIN 2.2A at 19.2 kbit/s, enhanced checksum; the customer's LDF lays out frames and signals, the model names them only
    item def LinFrame {
        doc /* A LIN frame: header from the master (break, sync, protected identifier), response of up to 8 data bytes and checksum. */
        attribute frameId : Integer;
    }
    item def SwitchStatusFrame :> LinFrame {
        doc /* Unconditional frame published by the switch, frame identifier per the LDF and the coded seat position. */
        attribute seatKnobDirection : Integer;    // none, fore, aft, up, down, recline forward, recline back
        attribute lumbarPadDirection : Integer;   // none, up, down, in, out
        attribute heatingKeyPressed : Boolean;
        attribute coolingKeyPressed : Boolean;
        attribute massageKeyPressed : Boolean;
        attribute aliveCounter : Integer;
        attribute responseError : Boolean;        // LIN response_error bit
    }
    item def SeatCommandFrame :> LinFrame {
        doc /* Unconditional frame published by the seat control unit and subscribed by every switch. */
        attribute dimmingLevel : Integer;         // night design, percent
        attribute heatingLevel : Integer;         // comfort level indication, 0 to 3
        attribute coolingLevel : Integer;
        attribute massageLevel : Integer;
        attribute aliveCounter : Integer;
    }
    item def MasterRequestFrame :> LinFrame {
        doc /* Diagnostic frame 0x3C, header and response from the master: node address (NAD), PCI and a UDS request or a LIN node configuration request. */
        attribute :>> frameId = 60;               // 0x3C
        attribute nad : Integer;
    }
    item def SlaveResponseFrame :> LinFrame {
        doc /* Diagnostic frame 0x3D: header from the master, response from the addressed switch with its NAD, PCI and the UDS or node configuration response. */
        attribute :>> frameId = 61;               // 0x3D
        attribute nad : Integer;
    }
    item def GoToSleepCommand :> MasterRequestFrame {
        doc /* Master request with NAD 0x00 and first data byte 0x00: every node enters sleep. */
        attribute :>> nad = 0;
    }
    item def WakeUpPulse { doc /* Dominant pulse of 250 µs to 5 ms on the LIN bus, sent by any node to end bus sleep; no separate wake line. */ }

    port def KeyPort { doc /* Delivers key states. */ out item keyState : KeyState; }
    port def LinPort {
        doc /* The single-wire LIN bus, referenced to KL31. */
        inout item frame : LinFrame;
        inout item wakeUp : WakeUpPulse;
    }
    port def UartPort { doc /* TxD and RxD, logic-level serial lines between the LIN transceiver and the microcontroller UART; not a LIN port. */ }
    port def TransceiverModePort { doc /* EN line from the microcontroller (normal or sleep mode), and the transceiver's wake-up indication on RxD. */ }
    port def InhibitPort { doc /* INH output of the LIN transceiver: high while awake, low in sleep. */ }
    port def PowerPort { doc /* Supplies power. */ out item power : SupplyPower; }
    port def GroundPort { doc /* Ground return (KL31), also the LIN reference. */ }
    port def LightPort { doc /* Emits light through a key symbol. */ out item light : Light; }
    port def PwmPort { doc /* PWM dimming outputs of the microcontroller timers. */ }
    port def LedDrivePort { doc /* PWM-dimmed constant current into a group of LEDs. */ }
    port def SensorBusPort { doc /* Serial sensor bus (SPI) between the hall sensors and the microcontroller. */ }
    port def SignalPort { doc /* Signals exchanged between SW components, by name per the LDF. */ }
    port def DiagnosticPort { doc /* UDS requests and responses between SW components. */ }
    port def FaultPort { doc /* Fault events (stuck key, open LED, supply out of range) reported to the fault memory. */ }
    port def CodingPort { doc /* Values written by end-of-line coding: button set and node address (NAD). */ }
    port def DownloadPort { doc /* Firmware image blocks from UDS RequestDownload and TransferData. */ in item image : FirmwareImage; }
    port def ImageStatusPort { doc /* Whether the application image is downloaded and verified for start. */ }
    port def ClipPort { doc /* Snap-fit clip joint into the seat trim. */ }

    interface def KeyInterface {
        doc /* Key contacts or sensors to the controller. */
        end port source : KeyPort;
        end port sink : ~KeyPort;
    }
    interface def ClipInterface {
        doc /* Clip joint between the seat trim and the switch housing. */
        end port trim : ~ClipPort;
        end port housing : ClipPort;
    }
}
