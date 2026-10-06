# Branch workflow

- `main`: stable release checkpoints.
- `feature/develop`: integration branch for reviewed tasks.
- `feature/task-<number>-<slug>`: one implementation branch for each task.

For every task:

1. Update local `feature/develop` from GitHub.
2. Create the task branch from the current `feature/develop`.
3. Implement and verify only that task.
4. Open a PR from the task branch into `feature/develop`.
5. Review and approve the PR, then merge it.
6. Create the next task branch from the updated `feature/develop`.

Merge `feature/develop` into `main` only at a deliberate stable/release checkpoint. Task 1 uses `feature/task-1-postgresql-pipeline`.
