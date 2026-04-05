# Frontend Agents

## Import paths

Always use the `@/` alias for imports. Never use relative paths (`./` or `../`).

```ts
// Good
import { LoadingShimmer } from '@/app/evaluate-contract/LoadingShimmer';

// Bad
import { LoadingShimmer } from './LoadingShimmer';
import { LoadingShimmer } from '../../evaluate-contract/LoadingShimmer';
```

The alias is configured in `tsconfig.json` as `@/*` -> `./*`.
