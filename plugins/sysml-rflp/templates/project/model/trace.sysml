package Trace {
    doc /*
     * Links from model elements to needs written outside the model (sphinx-needs ids),
     * e.g. customer requirements in RST. One annotation per target need:
     *     use case <'UC-001'> commute { @Realizes { need = "CRS-001"; } }
     * Links between model elements use native SysML (satisfy, verify, allocate, perform).
     */
    private import ScalarValues::String;

    metadata def Realizes  { attribute need : String[1..*]; }
    metadata def Satisfies { attribute need : String[1..*]; }
    metadata def Verifies  { attribute need : String[1..*]; }
}
