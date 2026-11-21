package SeatSwitchItems {
    doc /* What flows through the seat switch and across its boundary, and the interfaces that carry it. */

    item def KeyState { doc /* Pressed or released state of one key or knob direction. */ }
    item def LinFrame { doc /* A LIN frame: key states to the seat control unit, commands and dimming level from it. */ }
    item def FirmwareImage { doc /* A signed firmware image delivered over the diagnostic channel. */ }
    item def SupplyPower { doc /* 12 V vehicle supply. */ }
    item def Light { doc /* Light emitted through a key symbol. */ }

    port def KeyPort { doc /* Delivers key states. */ out item keyState : KeyState; }
    port def LinPort { doc /* Sends and receives LIN frames. */ inout item frame : LinFrame; }
    port def PowerPort { doc /* Supplies 12 V power. */ out item power : SupplyPower; }
    port def LightPort { doc /* Emits light through a key symbol. */ out item light : Light; }
    port def ClipPort { doc /* Snap-fit clip joint into the seat trim. */ }

    interface def KeyInterface {
        doc /* Key contacts or sensors to the controller. */
        end port source : KeyPort;
        end port sink : ~KeyPort;
    }
    interface def LinInterface {
        doc /* LIN connection between the switch and the seat control unit. */
        end port node : LinPort;
        end port commander : ~LinPort;
    }
    interface def ClipInterface {
        doc /* Clip joint between the seat trim and the switch housing. */
        end port trim : ~ClipPort;
        end port housing : ClipPort;
    }
}
