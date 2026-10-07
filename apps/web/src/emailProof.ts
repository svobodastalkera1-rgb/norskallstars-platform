/** Consume proofs before provider scripts load; keep them out of history/referrers. */
const fragment = new URLSearchParams(location.hash.slice(1));
const purpose =
  location.pathname === "/account/verify"
    ? "verify"
    : location.pathname === "/account/reset"
      ? "reset"
      : null;
let proof =
  purpose && fragment.get("token")
    ? { purpose, token: fragment.get("token")! }
    : null;
if (fragment.has("token")) history.replaceState(null, "", location.pathname);
export function takeEmailProof() {
  const current = proof;
  proof = null;
  return current;
}
