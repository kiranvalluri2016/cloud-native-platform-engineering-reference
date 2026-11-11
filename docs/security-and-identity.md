# Security, identity, and network boundaries

## Pod hardening

The Deployment applies non-root execution, a numeric user/group, `RuntimeDefault` seccomp, dropped Linux capabilities, a read-only root filesystem, and disabled privilege escalation. The only writable mount is a size-bounded ephemeral `/tmp` volume.

## NetworkPolicy coverage

The NetworkPolicy applies to Pods labeled `app.kubernetes.io/name: platform-api`.

- **Ingress:** only TCP 8080 from Pods labeled `platform.example.io/access: platform-api` in the same namespace. The rule deliberately has no `namespaceSelector`, preventing DEV and PROD cross-namespace ingress.
- **Egress:** only DNS TCP/UDP 53 to a selector representing kube-system DNS Pods.
- **Not represented:** ingress controller traffic, external egress, service mesh traffic, cloud metadata services, DNS provider variance, and CNI enforcement behavior.

Because NetworkPolicy enforcement is implemented by the target CNI, manifest rendering is not proof that these controls are active in a cluster.

## Identity and secrets

The dedicated ServiceAccount has `automountServiceAccountToken: false`. V1 has no workload-identity annotation, client identifier, tenant identifier, or cloud-role binding. A future approved deployment may use projected short-lived tokens and a provider-specific identity binding, but that belongs to a separate evidence-backed integration.

The source contains no Secret object or value. The optional `secretKeyRef` is only a runtime contract; approved deployment tooling must supply the named secret outside this repository.
