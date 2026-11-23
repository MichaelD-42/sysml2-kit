package WindowSwitchItems {
    doc /* What flows through the window switch and across its boundary, and the interfaces that carry it. */

    private import ScalarValues::Integer;
    private import ScalarValues::Boolean;

    item def KeyState { doc /* Released, first stage (manual) or second stage (express) of one key, or pressed and released for the child-lock key. */ }
    item def SupplyPower { doc /* 12 V vehicle supply (KL30). */ }
    item def Light { doc /* Light emitted through a key symbol or the child-lock telltale. */ }

    // LIN 2.2A at 19.2 kbit/s, enhanced checksum; the customer's LDF lays out frames and signals, the model names them only
    item def LinFrame {
        doc /* A LIN frame: header from the master, response of up to 8 data bytes and checksum. */
        attribute frameId : Integer;
    }
    item def SwitchStatusFrame :> LinFrame {
        doc /* Unconditional frame published by the switch, frame identifier per the LDF and the coded door position. */
        attribute windowKeyStages : Integer;      // two bits per window key: released, manual, express
        attribute childLockKeyPressed : Boolean;
        attribute aliveCounter : Integer;
        attribute responseError : Boolean;        // LIN response_error bit
    }
    item def DoorCommandFrame :> LinFrame {
        doc /* Unconditional frame published by the door control unit and subscribed by the switch. */
        attribute dimmingLevel : Integer;         // night design, percent
        attribute childLockActive : Boolean;      // telltale on
        attribute aliveCounter : Integer;
    }
    item def WakeUpPulse { doc /* Dominant pulse of 250 µs to 5 ms on the LIN bus that ends bus sleep. */ }

    port def KeyPort { doc /* Delivers key states. */ out item keyState : KeyState; }
    port def LinPort {
        doc /* The single-wire LIN bus, referenced to KL31. */
        inout item linFrame : LinFrame;
        inout item wakeUp : WakeUpPulse;
    }
    port def UartPort { doc /* TxD and RxD between the LIN transceiver and the microcontroller UART. */ }
    port def PowerPort { doc /* Supplies power. */ out item power : SupplyPower; }
    port def GroundPort { doc /* Ground return (KL31), also the LIN reference. */ }
    port def LightPort { doc /* Emits light through a key symbol. */ out item light : Light; }
    port def PwmPort { doc /* PWM dimming outputs of the microcontroller timers. */ }
    port def LedDrivePort { doc /* PWM-dimmed constant current into a group of LEDs. */ }
    port def SignalPort { doc /* Signals exchanged between SW components, by name per the LDF. */ }
    port def ClipPort { doc /* Snap-fit clip joint into the door trim. */ }

    interface def KeyInterface {
        doc /* Key contacts to the controller. */
        end port source : KeyPort;
        end port sink : ~KeyPort;
    }
    interface def ClipInterface {
        doc /* Clip joint between the door trim and the switch housing. */
        end port trim : ~ClipPort;
        end port housing : ClipPort;
    }
}
