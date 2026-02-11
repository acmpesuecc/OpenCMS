
---

# Commit Convention

Use clear, structured commit messages to maintain a readable project history.

---

## Format

```
<type>: <short summary>

<optional description>
```

---

## Types

- **feat**: new feature or capability
- **fix**: bug fix or correction
- **docs**: documentation changes only
- **style**: formatting, missing semicolons, whitespace (no logic change)
- **refactor**: code restructuring without changing behavior
- **test**: adding or updating tests
- **chore**: maintenance tasks (dependencies, config, tooling)

> If you want to introduce more types or sub-types, please make a Pull Request for the same :)

---

## Examples

**Good:**
```
feat: add billie jean


```

**Good:**
```
fix: handle rate limit errors

Added exponential backoff and retry logic.
```

**Good:**
```
docs: update README with timeline and stack usage
```

**Bad:**
```
updated stuff
```

**Bad:**
```
fix bug
```

---

## Guidelines

- Keep the summary line under 72 characters.
- Use lowercase for type and summary.
- Use present tense ("add" not "added").
- Focus on what and why, not how (code shows how).
- Reference issue numbers if applicable (e.g., `fix: resolve #42`).

---
