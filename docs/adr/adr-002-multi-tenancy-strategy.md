# ADR 002: Multi-tenancy Strategy

## Status
Accepted

## Context
The platform needs to support multiple tenants (e.g., different companies or teams) using the same installation. Requirements include:
1.  **Data Isolation:** A tenant should generally only see their own resources and plans.
2.  **Global Resources:** Tenants should benefit from a shared "global" library of curated resources (e.g., public documentation, popular courses).
3.  **Efficiency:** Creating separate database instances or vector collections for every small tenant is operationally heavy and resource-intensive.

## Decision
We have chosen a **Shared Collection with Filter-based Isolation** strategy.

1.  **Vector Database (Qdrant):**
    *   We use a single `resources` collection for all tenants.
    *   Each point (resource) has a `tenant_id` field in its payload.
    *   Queries MUST include a filter: `filter: { must: [{ key: "tenant_id", match: { value: <current_tenant_id> } }] }`.
    *   Global resources are tagged with `tenant_id: "global"`.
    *   Queries can optionally include global resources using a `should` clause (OR logic) or by searching both contexts if needed (currently implemented as strict separation for simplicity, with global being a special case).

2.  **Relational Database (Postgres):**
    *   Tables (`resource`, `learning_plans`, `quizzes`) include a `tenant_id` column.
    *   Row-Level Security (RLS) could be enabled in the future, but currently, isolation is enforced at the application service layer (Gateway/Orchestrator).

## Consequences

### Positive
*   **Operational Simplicity:** Only one Qdrant collection and one Postgres database to manage, backup, and scale.
*   **Resource Efficiency:** Dense packing of vectors in Qdrant is more memory-efficient than sparse collections for many small tenants.
*   **Flexibility:** Easy to promote a resource from "tenant-specific" to "global" by changing a metadata field.

### Negative
*   **Security Risk:** Isolation depends entirely on correct application logic. A bug in the query filter construction could leak data between tenants.
*   **Performance "Noisy Neighbor":** One heavy tenant could impact the search performance for others since they share the same index.

## Alternatives Considered
*   **Database/Collection per Tenant:**
    *   *Pros:* Perfect isolation, easy data deletion (drop collection).
    *   *Cons:* High resource overhead (memory/CPU) for Qdrant to maintain hundreds/thousands of separate HNSW graphs. Not viable for a "freemium" or high-volume SaaS model without massive infrastructure.
