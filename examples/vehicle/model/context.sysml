package VehicleContext {
    doc /* The vehicle in its operating environment: the people and things it interacts with. */

    part vehicleContext {
        doc /* The vehicle in use, with everything outside it that it exchanges with. */
        part vehicle :> VehicleLogical::vehicle { doc /* The vehicle under development. */ }
        part driver { doc /* Drives the vehicle and requests torque. */ }
        part passenger { doc /* Rides in one of the four passenger seats. */ }
        part trailer { doc /* Car trailer that carries the vehicle, tied down at the frame. */ }
        part chargingStation { doc /* Recharges the traction battery. */ }
        part road { doc /* Carries the vehicle's weight and traction forces. */ }

        connect driver to vehicle;
        connect passenger to vehicle;
        connect trailer to vehicle;
        connect chargingStation to vehicle;
        connect road to vehicle;
    }
}
