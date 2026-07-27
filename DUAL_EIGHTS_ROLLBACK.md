# Dual Eights presentation switch

The World Cup presentation is preserved in the same codebase. The active
presentation is controlled by one value in `_config.yml`:

```yaml
site_mode: dual_eights
```

To restore the old World Cup homepage, navigation and footer, change it to:

```yaml
site_mode: legacy
```

Commit and push that one-line change to the deployment branch. GitHub Pages
will rebuild the site with the legacy presentation. Existing article URLs do
not change in either mode.

To test legacy mode locally without editing the primary setting, build with:

```powershell
bundle exec jekyll serve --config _config.yml,_config.preview.yml,_config.legacy.yml
```

Switch `_config.yml` back to `dual_eights` to restore the new presentation.
