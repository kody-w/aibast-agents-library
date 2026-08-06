import subprocess, sys
pairs=[("care-gap-closure-agent","healthcare"),("clinical-notes-summarizer-agent","healthcare"),("patient-intake-and-scheduling-agent","healthcare"),
("financial-advisor-agent","financial_services"),("fraud-detection-and-alert-agent","financial_services"),("underwriting-support-agent","financial_services"),
("energy-operations-suite","energy"),("field-services-dispatch-agent","energy"),
("building-permit-processing-agent","government"),("utility-billing-and-assistance-agent","government"),
("personalized-shopping-agent","retail_cpg"),("returns-and-complaints-resolution-agent","retail_cpg"),
("license-renewal-and-expansion-agent","software"),("product-feedback-synthesizer-agent","software"),
("proposal-generation-agent","professional_services"),("time-entry-billing-agent","professional_services"),
("ask-hr-agent","cross_industry"),("customer-escalations-agent","cross_industry"),
("supply-risk-monitoring-agent","manufacturing")]
for slug,bucket in pairs:
    r=subprocess.run(["python3","film/kit/harvest.py","--cut",slug,"--bucket",bucket],capture_output=True,text=True)
    print("\n".join(l for l in r.stdout.splitlines() if "safe window" in l or l.startswith("[OK] film")), flush=True)
    if r.returncode: print("FAIL",slug,r.stderr[-300:], flush=True)
print("HARVEST DONE")
