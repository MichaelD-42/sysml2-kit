// Constraints for tests/test_constraints.py. After a change, re-export:
//   sysml export tests/fixtures/expressions.sysml -o tests/fixtures/expressions.json && python tests/fixtures/strip.py tests/fixtures/expressions.json
package Expressions {
    private import ScalarValues::*;
    private import ISQ::*;
    private import SI::*;

    part def Rated {
        attribute mass : MassValue = 48 [g];
        attribute force : ForceValue = 4.5 [N];
        attribute minTemp : ThermodynamicTemperatureValue = -40 ['°C'];
        attribute ip : String = "IP5K4";
        attribute cycles : Integer = 200000;
        attribute lum = 20 [cd / m^2];
        attribute ok : Boolean = true;
        attribute unset : Integer;
        part a { attribute nad : Integer = 33; }
        part b { attribute nad : Integer = 34; }

        constraint holdsMass { mass <= 60 [g] }
        constraint holdsForce { force >= 3.0 [N] and force <= 6.5 [N] }
        constraint holdsTemp { minTemp <= -40 ['°C'] }
        constraint holdsIp { ip == "IP5K4" }
        constraint holdsCycles { cycles >= 200000 }
        constraint holdsLum { lum >= 8 [cd/m^2] and lum <= 40 [cd/m^2] }
        constraint holdsChain { a.nad != b.nad }
        constraint holdsNotOr { not (mass > 60 [g]) or cycles < 1 }
        constraint holdsBool { ok }

        constraint failsMass { mass <= 40 [g] }
        constraint failsCycles { cycles >= 300000 }
        constraint failsIp { ip == "IP6K9K" }

        constraint unitsDiffer { mass <= 0.06 [kg] }
        constraint noValue { a.nad != unset }
        constraint arithmetic { cycles * 2 >= 1 }
    }
}
