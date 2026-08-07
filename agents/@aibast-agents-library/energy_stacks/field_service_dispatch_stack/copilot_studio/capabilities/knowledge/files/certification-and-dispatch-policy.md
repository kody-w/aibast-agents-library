# Certification and Dispatch Policy

> SYNTHETIC — DEMO DATA. A fictional operator's policy, included so the
> agent's guardrails are grounded in a citable document rather than only in
> its instructions.

## Why certification gating exists

Field work on energy infrastructure is regulated, hazardous work. A
technician without the required certification on a job site is a safety
incident and a compliance violation regardless of outcome. The dispatch
system therefore treats certifications as a hard gate, not a preference.

## Certifications in use

| Certification | Covers |
|---------------|--------|
| electrical_high_voltage | Work on or near energized high-voltage equipment |
| transformer_maintenance | Substation transformer service, including oil systems |
| confined_space | Entry into vaults, tanks, and other confined spaces |
| wind_turbine | Tower climbs and nacelle work on wind turbines |
| crane_operation | Mobile and fixed crane operation |
| gas_turbine | Gas turbine mechanical service |
| combustion_systems | Burner and fuel-delivery systems |
| pipeline_inspection | In-service pipeline survey and inspection |
| welding_api1104 | Pipeline welding to API 1104 |
| hazmat | Hazardous materials handling and response |
| scada_systems | SCADA and industrial control system service |

## Dispatch rules

1. A service request lists required certifications. A technician is eligible
   only if they hold every one of them.
2. Emergencies do not relax the gate. If no certified technician is
   available, the dispatcher escalates to the on-call engineering manager,
   who may engage a qualified contractor or authorize mutual aid.
3. Technicians carry a daily job cap (`max_jobs`). Assignments beyond the cap
   require dispatcher override, which the agent never assumes.
4. The dispatch agent recommends. Only a human dispatcher assigns work,
   interrupts a break, or pulls a technician off an active job.
