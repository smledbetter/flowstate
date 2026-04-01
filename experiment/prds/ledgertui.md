# ledgertui — Personal Finance TUI

**One-liner:** Terminal UI for tracking personal transactions with categories, running balances, monthly/yearly summary reports, and CSV import.

**Stack:** Rust (2021 edition). Dependencies: ratatui + crossterm (TUI), serde + serde_json (storage), chrono (dates), csv (import). Test: cargo test. Lint: cargo clippy.

**Quality Gates:** `cargo build` clean, `cargo clippy -- -D warnings` clean, `cargo test` all pass, coverage >= 80% (via cargo-tarpaulin or llvm-cov).

### Sprint 0 — Project Setup and Data Model
- Scaffold: Cargo.toml, src/main.rs, src/lib.rs, modules (model, store, tui, report)
- Data model: Transaction (id, date, amount_cents, description, category, account), Account (name, type: checking/savings/credit), Category (name, parent for hierarchy)
- JSON file storage: ledger.json in XDG data dir or current directory
- Set up gates: cargo build, clippy, test
- **AC:** Binary compiles, data model serializes/deserializes, gates pass, 8+ tests
- **LOC:** ~400

### Sprint 1 — TUI Framework and Transaction List
- Terminal UI with ratatui: full-screen layout with header, transaction list, status bar
- Transaction list: scrollable table with date, description, amount, category, running balance
- Color coding: green for income, red for expenses
- Keyboard navigation: j/k or arrow keys to scroll, q to quit
- Load/save transactions from JSON file on startup/exit
- **AC:** TUI renders transaction list, scrolling works, data persists between sessions, 20+ tests (logic tested without terminal)
- **LOC:** ~700

### Sprint 2 — Transaction Entry and Editing
- Add transaction: press 'a', modal form with fields (date, amount, description, category, account)
- Tab between fields, Enter to save, Esc to cancel
- Edit transaction: press 'e' on selected row, same form pre-populated
- Delete transaction: press 'd', confirmation prompt
- Input validation: date format (YYYY-MM-DD), amount as decimal (stored as cents), required fields
- Category autocomplete: type to filter existing categories
- **AC:** Add/edit/delete transactions via TUI, validation rejects bad input, autocomplete filters categories, 35+ total tests
- **LOC:** ~800

### Sprint 3 — Accounts and Categories
- Account management: press 'A' to switch to accounts view, add/edit/delete accounts
- Per-account transaction filtering: press 'f' to filter by account
- Category hierarchy: parent/child categories, display as "Food > Groceries"
- Category management screen: press 'C', add/rename/reparent/delete categories
- Transfer between accounts: press 't', creates paired transactions (debit + credit)
- **AC:** Multiple accounts with independent balances, category tree works, transfers balance correctly, 50+ total tests
- **LOC:** ~700

### Sprint 4 — Reports
- Monthly summary: press 'm', table showing income/expenses/net by category for selected month
- Yearly summary: press 'y', month-by-month bar chart (text-based) showing income vs expenses
- Category breakdown: pie-chart style percentage display per category
- Date range filter: press '/' to set custom date range for all views
- Export report to CSV: press 'x' from any report view
- **AC:** Monthly/yearly summaries compute correctly, bar chart renders, CSV export is valid, 65+ total tests
- **LOC:** ~700

### Sprint 5 — CSV Import and Polish
- CSV import: `ledgertui import file.csv` with column mapping (interactive prompt for which column is date, amount, etc.)
- Auto-detect common bank CSV formats (date formats, negative amounts as debits)
- Duplicate detection: skip transactions matching date+amount+description within same account
- Search transactions: press '/' in list view, fuzzy match on description
- Help overlay: press '?' to show all keybindings
- **AC:** CSV import handles 3+ date formats, duplicate detection works, search filters list, help displays, all gates green, 80+ total tests
- **LOC:** ~700

**Total estimated LOC:** ~4000 (including tests)

---
