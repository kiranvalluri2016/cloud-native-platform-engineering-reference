# Local validation boundary

The project validation is deliberately offline from Kubernetes and cloud providers.

```bash
PYTHON_COMMAND=.venv/bin/python ./scripts/validate-local.sh
docker build --tag cloud-native-reference:local .
docker run --rm --read-only --user 10001:10001 cloud-native-reference:local
```

The validation script runs the API and manifest tests, renders `k8s/overlays/dev` and `k8s/overlays/prod`, checks for prohibited GitHub Actions workflows, and scans repository source for common credential patterns. It excludes `.venv`, which is local ignored dependency state rather than source.

The runtime smoke check confirms that the image starts as a non-root user and can serve `/live` and `/ready` while Docker runs with a read-only root filesystem.

These commands do not run `kubectl apply`, connect to a Kubernetes API server, create a namespace, publish a container, or authenticate to a cloud provider. They do not prove admission policy, scheduling, CNI NetworkPolicy enforcement, HPA metrics, workload identity, or cluster-level observability behavior.
