# Contributing Translations

> Sovereign intelligence should not depend on a single language.

Thank you for helping make SovereignStack accessible to a global audience. Every new language expands the network's reach and demonstrates the project's commitment to digital sovereignty.

## Which Documents to Translate

Priority order (start with the first):

| Priority | Document | Location |
|----------|----------|----------|
| 1 | README | `docs/i18n/<lang>/README.md` |
| 2 | CONSTITUTION | `docs/i18n/<lang>/CONSTITUTION.md` |
| 3 | ARCHITECTURE | `docs/i18n/<lang>/ARCHITECTURE.md` |

## Translation Guidelines

### Accuracy
- Preserve the meaning and intent of the English original.
- Technical terms (URI, RFC, OASA, Merkle, vLLM, gVisor, etc.) should remain in English unless a widely-accepted local equivalent exists.
- The closing line *"Sovereign intelligence should not depend on a single language"* must be translated into the target language.

### Structure
- Keep the same Markdown heading structure (`#`, `##`, `###`) as the English original.
- Internal links to `/docs/i18n/<lang>/...` should point to files within the same language directory.
- Links to root-level files (`/README.md`, `/CONSTITUTION.md`, `/GOVERNANCE.md`) should remain absolute paths from repository root.

### Metadata
Each translated file should begin with a header noting the language and canonical source:

```markdown
# Document Title — Language Name

**Language:** Native name (English name)  
**Canonical source:** `/path/to/english/original.md`
```

### Review Requirements
- **New translations:** minimum 1 native speaker review before merge
- **Updates:** minimum 1 native speaker review for significant changes
- **Machine translation:** allowed as a starting point, but must be reviewed by a native speaker before submission

## How to Add a New Language

1. **Check the index** at `docs/i18n/README.md` to see if the language already exists.
2. **Fork the repository** and create a branch: `i18n/<lang-code>/`
3. **Create the directory:** `docs/i18n/<lang-code>/`
4. **Translate the 3 core documents** following the guidelines above.
5. **Update the index:** add a row to the language table in `docs/i18n/README.md`.
6. **Submit a pull request** with `[i18n] <Language Name>` as the title.

## Language Code Reference

| Code | Language | Native Name |
|------|----------|-------------|
| `ar` | Arabic | العربية |
| `cs` | Czech | Čeština |
| `de` | German | Deutsch |
| `en` | English | English |
| `es` | Spanish | Español |
| `fr` | French | Français |
| `hi` | Hindi | हिन्दी |
| `it` | Italian | Italiano |
| `ja` | Japanese | 日本語 |
| `ko` | Korean | 한국어 |
| `nl` | Dutch | Nederlands |
| `pl` | Polish | Polski |
| `pt-BR` | Portuguese (Brazil) | Português |
| `ru` | Russian | Русский |
| `sv` | Swedish | Svenska |
| `tr` | Turkish | Türkçe |
| `uk` | Ukrainian | Українська |
| `zh-CN` | Chinese (Simplified) | 中文 |

## Getting Help

- Open a [GitHub Issue](https://github.com/Kubenew/SovereignStack/issues) with the `i18n` label
- Join the `#i18n` channel in our community chat
- Ask a maintainer for a native-speaker review match

---

*Sovereign intelligence should not depend on a single language.*
