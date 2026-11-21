package VehicleUseCases {
    doc /* R layer: how actors use the vehicle. Each use case realizes customer requirements
     * and is realized by the features it performs. */

    private import Trace::*;
    private import VehicleFeatures::*;

    use case <'UC-001'> commute {
        @Realizes { need = "CRS-001"; }
        doc /* The driver takes up to four passengers on a daily commute and back. */
        subject vehicle;
        actor driver;
        actor passenger;
        perform occupantSeating;
        perform travelRange;
        perform propulsion;
    }

    use case <'UC-002'> transportOnTrailer {
        @Realizes { need = "CRS-002"; }
        doc /* A towing driver loads the vehicle onto a car trailer and secures it. */
        subject vehicle;
        actor towingDriver;
        perform trailerTransport;
    }
}
