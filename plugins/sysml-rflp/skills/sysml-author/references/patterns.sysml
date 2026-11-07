// Checked SysML v2 patterns for RFLP models. Validate: sysml check <this file> <project>/model/trace.sysml
// One package per layer and file; package names carry a system prefix (`Pump...`) because
// unprefixed names like `UseCases` collide with standard library packages.
package PumpPatterns {
    doc /* Short names <'X-NNN'> mark elements that become sphinx-needs needs. */

    private import Trace::*;          // @Realizes / @Satisfies / @Verifies { need = "..."; }
    private import ScalarValues::*;

    // --- R: use cases realize customer requirements (RST needs) and perform functions ---
    use case <'UC-101'> coolEngine {
        @Realizes { need = "CRS-101"; }                 // one annotation per need is the safe form
        doc /* The driver drives under load; the engine stays within temperature limits. */
        subject pumpSystem;
        actor driver;
        perform coolingFunctions.circulate;             // => F-102 realizes UC-101
    }

    // --- R: system requirements are requirement usages; text-only is a full requirement ---
    requirement <'SR-101'> minFlow {
        @Satisfies { need = ("CRS-101", "CRS-102"); }   // a sequence also works with the forked sysml CLI
        doc /* The cooling loop shall deliver at least 20 l/min of coolant. */
    }
    requirement <'SR-102'> maxPower {
        @Satisfies { need = "CRS-102"; }
        doc /* The pump shall draw at most 150 W. */
        attribute power : Real;
        require constraint { power <= 150.0 }          // optional formal part
    }

    // --- F: a usage tree of solution-neutral functions (verb + noun) ---
    action <'F-101'> coolingFunctions {
        doc /* Top-level cooling function. */
        action <'F-102'> circulate { doc /* Move coolant through the loop. */ }
        action <'F-103'> rejectHeat { doc /* Transfer heat from coolant to ambient air. */ }
        first circulate then rejectHeat;
    }

    // --- L: a usage tree of technology-neutral components with ports (interfaces) ---
    part <'LC-101'> pumpSystem {
        doc /* The cooling system. */
        part <'LC-102'> pump {
            doc /* Pressurizes coolant. */
            port <'LI-101'> outlet;
        }
        part <'LC-103'> radiator {
            doc /* Exchanges heat with air. */
            port <'LI-102'> inlet;
        }
        connect pump.outlet to radiator.inlet;
    }

    // --- L: allocation (leaf function -> exactly one leaf component) and satisfaction ---
    allocate coolingFunctions.circulate to pumpSystem.pump;
    allocate coolingFunctions.rejectHeat to pumpSystem.radiator;
    satisfy minFlow by pumpSystem.pump;               // both ends need short names
    satisfy maxPower by pumpSystem.pump;

    // --- V: system test cases verify system requirements ---
    verification <'STC-101'> flowBenchTest {
        doc /* Measure flow on the test bench at nominal speed. */
        objective { verify minFlow; verify maxPower; }
    }
}
