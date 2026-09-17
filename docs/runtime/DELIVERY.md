# Runtime boundary

Master Repo has no application staging or production service and manages no
customer data. Validation, source merge and standard publication are governed by
[repository delivery](../repository/DELIVERY.md).

Consumer deployment and global skill installation are separate authorized
operations. Testing this source never connects a consumer branch to a runtime.
