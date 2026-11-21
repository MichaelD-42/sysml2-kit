package Trace {
    doc /*
     * Links from model elements to needs written outside the model (sphinx-needs ids),
     * e.g. customer requirements in RST. One annotation per target need:
     *     use case <'UC-001'> commute { @Realizes { need = "CRS-001"; } }
     * Links between model elements use native SysML (satisfy, verify, allocate, perform).
     */
    private import ScalarValues::String;
    private import ScalarValues::Boolean;

    metadata def Realizes  { attribute need : String[1..*]; }
    metadata def Satisfies { attribute need : String[1..*]; attribute partial : Boolean[0..1]; }
    metadata def Verifies  { attribute need : String[1..*]; }
    metadata def Implements { attribute need : String[1..*]; }

    // keywords: `#Feature action <'FEAT-001'> x;`, `#Electrical part <'PC-001'> y;`
    metadata def Feature;
    metadata def Mechanical;
    metadata def Electrical;
    metadata def Software;

    metadata def Matches { attribute need : String[1..*]; attribute partial : Boolean[0..1]; }
}
