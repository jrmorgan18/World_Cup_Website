# Published article video retention

Self-hosted article clips are available for 14 days after an article's publication
date. On every Jekyll build (including every publication and dashboard deployment),
`_plugins/video_retention.rb` removes players and direct clip links from articles
**more than** 14 calendar days old. The build date is UTC; articles exactly 14 days
old remain intact until the next calendar day.

The build excludes the retired files under `assets/videos/` from the published
Pages artifact. A clip reused by a newer article or another page is kept until
that remaining reference also expires. Unrelated static files are not removed.

Article prose, captions, images, URLs, navigation and original publication dates
stay unchanged. Expired articles display a short archive notice instead of broken
players. Captions become ordinary paragraphs with their original wording.

This is publication-time cleanup, not an exact-time scheduled deletion. The next
site deployment applies the current cutoff; no separate recurring job is needed.
The normal automated dashboard deployments also rebuild the site.

No original video or article source is deleted: `assets/videos/` remains in Git,
and full downloads and editing copies in the local `media/` directory are untouched.
Only the generated public site drops the expired video copies. This reduces the
Pages deployment size, not the Git repository's historical size.

To adjust the policy, change `video_retention_days` in `_config.yml`. Do not bypass
the plugin with a safe-mode build for production. The Pages workflow runs its tests
before building and checks internal links afterwards.

Run the policy tests with:

```sh
bundle exec ruby scripts/test_video_retention.rb
```
