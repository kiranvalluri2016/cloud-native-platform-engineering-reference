# Rollback runbook reference

Rollback must use a previously approved immutable image digest and a known-good rendered manifest revision. Do not roll back to a mutable tag.

1. Identify the failed deployment revision and the prior approved digest.
2. Confirm rollback authority and customer-impact communications.
3. Render the prior known-good overlay and compare the namespace, security, resource, and HPA contracts.
4. Execute the organization-approved rollback mechanism outside this repository.
5. Verify readiness, workload health, metrics, logs, and incident closure criteria.

V1 does not issue a cluster rollback command and does not claim rollback success.
