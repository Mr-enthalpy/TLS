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

## Remote topology

Use two different remotes with different purposes.

Private remote, complete internal repository:

```text
private  git@github.com:Mr-enthalpy/tls_c1.git
```

This remote receives full internal branches and history:

```bash
git push private main internal
```

Public release remote, generated public repository:

```text
public-release  git@github.com:Mr-enthalpy/TLS.git
```

This remote receives only the generated local `public` branch:

```bash
git push public-release public:main
```

`public:main` means: push the local `public` branch to the `main` branch in
the public-release remote. Do not push local `main` or `internal` to the public
remote.

If this clone still uses `origin` for the private repository, either keep using
`origin` for private work or rename it deliberately:

```bash
git remote rename origin private
git remote add public-release git@github.com:Mr-enthalpy/TLS.git
```

Do not add the public repository as the default push target for internal
branches.

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

Push the generated branch explicitly to the public-release remote:

```bash
git push public-release public:main
```

Keep full internal history on the private remote:

```bash
git push private main internal
```

If the local `internal` branch does not exist, create or map it intentionally
before using that command. The important invariant is that the public-release
remote only receives local `public`.

## Forbidden commands

Never push internal branches to the public-release remote:

```bash
git push public-release main
git push public-release internal
git push public-release --all
```

Never merge or rebase internal history into `public`:

```bash
git merge main
git merge internal
git rebase main
git rebase internal
```

These commands contaminate the public branch history or publish the wrong
branch. A clean final tree is not enough; Git history must also remain clean.

## Never merge internal into public

Do not run:

```bash
git checkout public
git merge main
git merge internal/main
git rebase main
git rebase internal/main
```

Merging connects the public branch history to internal history. That can expose
private files through Git history even if the final tree looks clean.

If the public branch ever becomes polluted, delete it and regenerate it as an
orphan branch from the internal source tree.
