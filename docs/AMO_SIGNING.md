# Mozilla Signing and Persistent Installation

Firefox Release requires Mozilla signing for ordinary persistent installation of self-distributed extensions.

GoreeCloud Redirector uses the fixed Firefox extension ID `redirector@goreecloud.com`. The manifest also declares `data_collection_permissions.required = ["none"]`.

## Preferred release channel

Use **unlisted/self-distributed** signing. This keeps GoreeCloud in control of distribution while still receiving the Mozilla certificate required by Firefox.

## Web upload path

1. Sign in to the Firefox Add-ons Developer Hub with the GoreeCloud Mozilla account.
2. Submit a new add-on and choose self-distribution / "On your own".
3. Upload the release XPI or ZIP produced from this source tree.
4. Complete Mozilla validation/review requirements.
5. Download the Mozilla-signed XPI.
6. Preserve the signed XPI as the release artifact and verify persistent installation through Firefox **Install Add-on From File**.

## web-ext path

Keep AMO credentials outside the repository. Export them only in the local shell used for signing:

```bash
export AMO_JWT_ISSUER='user:...'
export AMO_JWT_SECRET='...'
./scripts/sign-unlisted.sh
```

The signing helper refuses to run when either variable is absent. Do not place these values in `.env`, source files, documentation, issue comments, or GitHub Actions secrets unless a separately approved GoreeCloud credential-management workflow is established.

## Acceptance gate

A signed XPI is not automatically Stable. After signing, verify:

- persistent installation succeeds;
- Firefox restart retains the extension;
- `https://keep.google.com/` redirects to `https://memos.goreecloud.com/`;
- the built-in toggle persists and behaves correctly;
- custom redirect permission prompts work;
- light and dark popup/settings views remain coherent;
- no unexpected permission or data-collection prompt appears;
- the signed artifact version and extension ID match the source manifest.
