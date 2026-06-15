# Init commit checklist

Before the first commit:

- [ ] Rename author in `ModFile.json` if needed.
- [ ] Decide whether to add a license.
- [ ] Run `python tools/check_layout.py`.
- [ ] Confirm `Directory.Build.props` is not committed.
- [ ] Commit scaffold only; do not include local Terra Invicta DLLs or UMM DLLs.

Suggested commit message:

```text
Initial missile fire-control mod scaffold
```
