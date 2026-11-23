// Validate SysML files with the OMG Pilot Implementation: parse, link and run its validator on each.
//   java -cp jupyter-sysml-kernel-<v>-all.jar tests/PilotCheck.java <sysml.library> <file.sysml>...
// tests/pilot.py runs it on the examples and the authoring patterns.
// Prints one line per error or warning (file:line: severity: message); exits 1 on any error.
import java.io.File;
import java.util.List;
import org.eclipse.emf.ecore.resource.Resource;
import org.eclipse.xtext.resource.XtextResource;
import org.eclipse.xtext.util.CancelIndicator;
import org.eclipse.xtext.validation.CheckMode;
import org.eclipse.xtext.validation.Issue;
import org.omg.sysml.interactive.SysMLInteractive;

public class PilotCheck {
    public static void main(String[] args) throws Exception {
        SysMLInteractive pilot = SysMLInteractive.getInstance();
        pilot.loadLibrary(args[0]);
        for (int i = 1; i < args.length; i++) {
            pilot.read(new File(args[i]).getAbsolutePath());
        }
        pilot.resolveAllInputResources();
        int errors = 0;
        for (Resource resource : pilot.getInputResources()) {
            XtextResource xtext = (XtextResource) resource;
            List<Issue> issues = xtext.getResourceServiceProvider().getResourceValidator()
                .validate(xtext, CheckMode.ALL, CancelIndicator.NullImpl);
            for (Issue issue : issues) {
                if (issue.getSeverity() == org.eclipse.xtext.diagnostics.Severity.ERROR) errors++;
                System.out.println(resource.getURI().toFileString() + ":" + issue.getLineNumber() + ": "
                    + issue.getSeverity().toString().toLowerCase() + ": " + issue.getMessage());
            }
        }
        System.out.println(pilot.getInputResources().size() + " file(s), " + errors + " error(s)");
        System.exit(errors > 0 ? 1 : 0);
    }
}
