// Checked SysML v2 patterns for RFLP models. Validate: sysml check <this file> <project>/model/trace.sysml
// The fragments illustrate each pattern; together they are not a rule-complete model (some needs lack links).
// One package per layer and file; package names carry a system prefix (`Pump...`) because
// unprefixed names like `UseCases` collide with standard library packages.
package PumpPatterns {
    doc /* Short names <'X-NNN'> mark elements that become sphinx-needs needs. */

    private import Trace::*;          // @Realizes / @Satisfies / @Verifies { need = "..."; }
    private import ScalarValues::*;

    // --- R: use cases realize customer requirements (RST needs) and perform functions ---
    // The objective's doc is the need title, "The <actor> wants to <goal>"; the name stays the identifier.
    use case <'UC-101'> coolEngine {
        @Realizes { need = "CRS-101"; }                 // one annotation per need is the safe form
        objective { doc /* The driver wants to drive under load without overheating the engine */ }
        doc /* The driver drives under load; the engine stays within temperature limits. */
        subject pumpSystem;
        actor driver;
        perform engineCooling;                          // => FEAT-101 realizes UC-101
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

    // --- R: a constraint states a value over a physical part's attribute; it carries an id and satisfies a CRS ---
    // Plain values go here, never as a bare attribute. A constraint is owned by the physical part it limits
    // (an #Assembly for the product as a whole), never by a logical component: values belong to the solution.
    // The bridge evaluates it against the values the part states or inherits; one that does not hold fails.
    #Assembly part <'PC-111'> pumpModule {
        doc /* The pump module as delivered. */
        attribute mass : Real = 2.1;
        attribute maxContinuousSpeed : Real = 3500.0;
        constraint <'CON-101'> maxMass {
            @Satisfies { need = "CRS-103"; }
            doc /* The module mass shall not exceed 2.5 kg. */
            mass <= 2.5
        }
        // met in part (the customer asks for 4000 rpm): the constraint states what is met, a `partial`
        // compliance statement (CST, in the docs) answering CRS-104 states the gap
        constraint <'CON-102'> continuousSpeed {
            @Satisfies { need = "CRS-104"; partial = true; }
            doc /* The pump shall run continuously up to 3500 rpm. */
            maxContinuousSpeed >= 3500.0
        }
    }

    // --- F: a feature (noun name) owns solution-neutral functions (verb + noun), nested for sub-functions ---
    #Feature action <'FEAT-101'> engineCooling {
        @Matches { need = "CRS-101"; }                  // covers this customer need; add `partial = true;` if only in part
        doc /* Keeps the engine within its temperature limits. */
        action <'F-101'> coolingFunctions {
            doc /* Top-level cooling function. */
            action <'F-102'> circulate { doc /* Move coolant through the loop. */ }
            action <'F-103'> rejectHeat { doc /* Transfer heat from coolant to ambient air. */ }
            first circulate then rejectHeat;
        }
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
    allocate engineCooling.coolingFunctions.circulate to pumpSystem.pump;
    allocate engineCooling.coolingFunctions.rejectHeat to pumpSystem.radiator;
    satisfy minFlow by pumpSystem.pump;               // both ends need short names
    satisfy maxPower by pumpSystem.pump;

    // --- P: physical components, one domain keyword each (#Mechanical, #Electrical, #Software); an
    // assembly across domains (the product as built) is #Assembly, no domain, and owns or references them ---
    #Electrical part <'PC-101'> pumpUnit {
        doc /* Brushless coolant pump, BOM PMP-100. */
        #Electrical port <'PI-101'> hoseOutlet;
    }
    #Mechanical part <'PC-102'> heatExchanger { doc /* Aluminium cross-flow radiator, BOM RAD-200. */ }
    allocate pumpSystem.pump to pumpUnit;               // LC => PC
    allocate pumpSystem.radiator to heatExchanger;
    allocate pumpSystem.pump.outlet to pumpUnit.hoseOutlet;   // LI => PI

    // --- P: software architecture and design are physical components: SW components and SW units ---
    // Firmware owns SW components, a SW component owns its SW units; each carries its own #Software.
    // A SW component's interfaces are ports, wired by connections. Software requirements (SWR, in the
    // docs) are allocated to the SW component or unit that implements them (`:allocated_to:`); unit tests verify the SWRs (JUnit).
    #Software part <'PC-107'> pumpFirmware {
        doc /* Pump controller firmware, module PMP-FW-100. */
        #Software part <'PC-108'> motorControl {
            doc /* SW component: runs the pump motor at the commanded speed. */
            #Software port <'PI-102'> speedCommand;
            #Software part <'PC-109'> speedController {
                doc /* SW unit: PI loop from speed set point to PWM duty. */
                #Software port setpoint;
                #Software port duty;
            }
            #Software part <'PC-110'> pwmDriver {
                doc /* SW unit: drives the PWM timer. */
                #Software port duty;
            }
            bind speedCommand = speedController.setpoint;
            connect speedController.duty to pwmDriver.duty;
        }
    }
    allocate pumpSystem.pump to pumpFirmware.motorControl;   // LC => SW component, not to its units

    // --- P: variation (platform side): variants are members; ids on variants need the kit's sysml fork ---
    variation #Electrical part <'PC-103'> controller {
        doc /* Pump controller family. */
        variant #Electrical part <'PC-104'> controllerBasic { doc /* Fixed speed. */ }
        variant #Electrical part <'PC-105'> controllerPwm { doc /* Speed control by PWM. */ }
    }

    // --- P: reuse in an RFQ project: subset (`:>`) a platform part or a variant; the project's subsetting
    // is what selects a variant (the platform's own allocations to its variants only offer them) ---
    #Electrical part <'PC-106'> selectedController :> controller::controllerPwm {
        doc /* Platform PWM controller, selected for this program. */
    }
    // a platform part this program changes: #Modified, and the doc says what changes
    #Mechanical #Modified part <'PC-112'> oemHeatExchanger :> heatExchanger {
        doc /* Radiator RAD-200 with the customer's mounting brackets: a new bracket die, BOM RAD-210. */
    }

    // --- V: system test cases verify system requirements ---
    verification <'STC-101'> flowBenchTest {
        doc /* Measure flow on the test bench at nominal speed. */
        objective { verify minFlow; verify maxPower; }
    }

    // --- V: a test verifies a constraint (@Verifies) or implements a customer test requirement (CTR) ---
    verification <'STC-102'> housingMassTest {
        @Verifies { need = "CON-101"; }                 // a constraint is not a requirement usage: @Verifies, not `verify`
        doc /* Weigh the housing on a calibrated scale; pass at 2.5 kg or less. */
    }
    verification <'STC-103'> customerEnduranceTest {
        @Implements { need = "CTR-101"; }               // a CTR is the customer's own test; implement it, do not rewrite it
        @Verifies { need = "CON-102"; }                 // optional: also verifies a constraint
        doc /* Run the endurance profile of CTR-101; pass when flow stays above 20 l/min. */
    }
}
