# Deployment runbook reference

This runbook is a reference contract only. It must not be interpreted as authority to deploy V1.

1. Build the image in an approved controlled environment.
2. Record the immutable image digest and complete image/security review.
3. Replace the PROD digest placeholder through an approved change.
4. Render the selected overlay and inspect Deployment, Service, HPA, and NetworkPolicy output.
5. Obtain target-cluster, namespace, identity, secret, and change authority.
6. Use the organization-approved deployment mechanism outside this repository.
7. Verify readiness, rollout state, metrics collection, CNI policy enforcement, and operational alerts in the target environment.

No `kubectl apply` command is provided because V1 neither owns nor validates a Kubernetes cluster.
