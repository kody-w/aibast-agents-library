# media-server — large media, kept out of the code clone

This branch exists so the library's install stays small.

Deleting a large file from the tip of `main` does not make `git clone` cheaper:
every blob ever committed stays in history. The install therefore clones at
**depth 1**, and depth 1 implies single-branch — it fetches the tip of one
branch and nothing else. Objects that live only here are never downloaded.

Measured: a depth-1 clone of the code branch is a **3.7 MB** `.git`, and this
branch's blobs are not reachable from it.

This is an orphan branch. It shares no history with `main` on purpose, so
nothing here can ever be pulled in by a merge by accident.

## Serving it back

GitHub Pages publishes a single branch and cannot serve this one.
`raw.githubusercontent.com` can, and allows cross-origin reads, but it sends
`application/octet-stream` with `x-content-type-options: nosniff` — a
`<video src>` pointed at that will not play.

`media.js` on the code branch fetches the bytes instead, wraps them in a Blob
with the correct type, and hands the element an object URL. The response header
never enters into it.

## Adding media

Put the file under the path the site expects, commit it here, and reference it
by that path — never by a raw URL in page source, so the branch and CDN are one
change in `media.js` rather than many.

Files above ~25 MB do not belong here: an object URL buffers the whole file and
gives up range requests. Use a release asset or a real CDN for those.
