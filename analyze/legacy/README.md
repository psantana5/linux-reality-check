# Legacy Scripts (Deprecated)

These scripts use parametric statistics that are **not academically sound** for systems performance data.

## Why Deprecated?

- Use mean/std instead of median/IQR
- Assume normal distributions (violated by latency data)
- T-tests on means (wrong for heavy-tailed distributions)
- Normal distribution overlays
- KDE smoothing that hides tail behavior

## What to Use Instead

| Old Script | New Script | Reason |
|------------|------------|--------|
| `hypothesis_test.py` | `../hypothesis.py` | Quantile-based comparison |
| `plot_advanced.py` | `../plot_robust.py` | ECDF, no normal fits |

## Academic Impact

**Using these scripts** → Paper rejection: "Normality assumption violated"  
**Using new scripts** → Paper acceptance: "Methodology is sound"

See `../../docs/ACADEMIC_STATISTICS.md` for details.
