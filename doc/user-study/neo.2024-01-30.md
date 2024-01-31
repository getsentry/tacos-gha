## Neo 2024-01-30

1. Create a simple PR against s4s dns:
   https://github.com/getsentry/ops/pull/9232
2. lock was held by prior PR! bukzor@9229
3. neo went to https://github.com/getsentry/ops/pull/9232 and added
   :taco::unlock label
4. failure:

   ```
   tf-lock-release: failure: not kneeyo1@9229.ops.getsentry.github.invalid: /home/runner/work/ops/ops/terragrunt/regions/single-tenant/dns/getsentry-net/s4s(bukzor@9229.ops.getsentry.github.invalid)
   ```

   let's switch those two

5. buck added the same label tf-lock-release: success:
   /home/runner/work/ops/ops/terragrunt/regions/single-tenant/dns/getsentry-net/s4s(bukzor@9229.ops.getsentry.github.invalid)
6. unprompted, neo added tacos:plan label to 9232
7. plan highlighting is broken a bit -- too long?
