---
name: Generated validation uses Zod 4
description: The current API codegen output depends on Zod 4 helpers.
---

Keep the workspace Zod catalog on Zod 4 when regenerating the API validation package.

**Why:** Current Orval output emits `zod.int()`, which is unavailable in the workspace's older Zod 3 runtime and breaks the library typecheck after otherwise successful codegen.

**How to apply:** If generated API validation types fail on `Property 'int' does not exist`, check the workspace Zod catalog and reinstall dependencies before changing generated files.