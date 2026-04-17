# logslice

A CLI tool to filter and slice structured log files by time range and field patterns.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
logslice [OPTIONS] <logfile>
```

### Examples

Filter logs between two timestamps:

```bash
logslice --start "2024-01-15T08:00:00" --end "2024-01-15T09:00:00" app.log
```

Filter by field pattern:

```bash
logslice --field "level=ERROR" --field "service=api" app.log
```

Combine time range and field filters:

```bash
logslice --start "2024-01-15T08:00:00" --end "2024-01-15T09:00:00" \
         --field "level=ERROR" app.log
```

Output to a file:

```bash
logslice --start "2024-01-15T08:00:00" --field "level=WARN" app.log -o filtered.log
```

### Options

| Flag | Description |
|------|-------------|
| `--start` | Start of time range (ISO 8601) |
| `--end` | End of time range (ISO 8601) |
| `--field` | Field pattern to match (repeatable) |
| `-o, --output` | Write results to file instead of stdout |
| `--format` | Log format: `json`, `logfmt` (default: `json`) |

---

## License

This project is licensed under the [MIT License](LICENSE).