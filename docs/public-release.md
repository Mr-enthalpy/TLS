# Public branch generation

`internal/main` is the source of truth for development. In this repository,
the current internal source branch is `main`; if the repository is later split
by remotes, treat the internal remote's `main` branch as `internal/main`.

The `public` branch is a generated view. Do not edit it by hand.

## Design

- Maintain one real source tree on the internal branch.
- Generate `public` from the internal worktree with `scripts/sync-public.sh`.
- Use `.public-include` as the allowlist of files that may enter `public`.
- Keep the `public` branch history disconnected from the internal branch by
  creating it as an orphan branch.
- Exclude vendor SDK archives, DLLs, LIB files, FTDI drivers, internal tests,
  private scripts, local hardware logs, and private build assets unless they
  have been explicitly reviewed and added to `.public-include`.

The public file set is allowlist-driven. Do not replace it with a broad
denylist such as "copy everything except third_party".

## Generate public locally

Run from a clean internal worktree:

```bash
scripts/sync-public.sh
```

The script uses a sibling worktree by default:

```text
../<repo-name>-public
```

This location is outside the internal repository, so it does not need to be
ignored by the internal `.gitignore`. To use a different location:

```bash
PUBLIC_WORKTREE=/path/to/public-worktree scripts/sync-public.sh
```

The script refuses to run if the internal worktree is dirty, if the public
worktree has manual changes, or if a manifest entry is missing.

## Publish

Push the generated branch explicitly to the public remote:

```bash
git push public-remote public:main
```

Use the public remote name configured for the public repository. Do not push
internal branches to the public remote.

## Never merge internal into public

Do not run:

```bash
git checkout public
git merge main
git merge internal/main
```

Merging connects the public branch history to internal history. That can expose
private files through Git history even if the final tree looks clean.

If the public branch ever becomes polluted, delete it and regenerate it as an
orphan branch from the internal source tree.
