require "minitest/autorun"
require "tmpdir"
require "fileutils"
require "jekyll"
require_relative "../_plugins/video_retention"

class VideoRetentionTest < Minitest::Test
  Post = Struct.new(:date, :output)
  Page = Struct.new(:output)
  Collection = Struct.new(:docs)
  StaticFile = Struct.new(:relative_path, :path)
  Site = Struct.new(:config, :time, :posts, :collections, :pages, :static_files, :data)

  def clip(path, caption = "Original <strong>caption</strong>.")
    "<figure class=\"article-video\"><video controls><source src=\"#{path}\"><a href=\"#{path}\">Watch clip</a></video><figcaption>#{caption}</figcaption></figure>"
  end

  def with_site(posts, pages: [], baseurl: "")
    Dir.mktmpdir("video-retention-test") do |root|
      files = %w[old shared recent boundary orphan].map do |name|
        relative = "/assets/videos/#{name}.mp4"
        path = File.join(root, relative.delete_prefix("/"))
        FileUtils.mkdir_p(File.dirname(path))
        File.binwrite(path, "archived original #{name}")
        StaticFile.new(relative, path)
      end
      collection = Collection.new(posts)
      site = Site.new({"video_retention_days" => 14, "baseurl" => baseurl},
                      Time.utc(2026, 10, 19, 18), collection, {"posts" => collection},
                      pages, files, {})
      yield site, files
    end
  end

  def test_expiry_boundary_future_and_shared_files
    old = Post.new(Time.new(2026, 10, 4, 23, 0, 0, "-04:00"), "<p>Keep prose.</p>" + clip("/assets/videos/old.mp4") + clip("/assets/videos/shared.mp4"))
    boundary = Post.new(Time.utc(2026, 10, 5), clip("/assets/videos/boundary.mp4"))
    recent = Post.new(Time.utc(2026, 10, 13), clip("/assets/videos/shared.mp4"))
    future = Post.new(Time.utc(2026, 10, 20), clip("/assets/videos/recent.mp4"))
    intact = [boundary, recent, future].map { |post| post.output.dup }
    with_site([old, boundary, recent, future]) do |site, originals|
      report = VideoRetention.apply(site)
      assert_equal ["/assets/videos/old.mp4"], report["omitted_files"]
      assert_equal 1, report["expired_articles"]
      refute_includes old.output, "<video"
      refute_includes old.output, "/assets/videos/"
      assert_includes old.output, "<p>Keep prose.</p>"
      assert_equal 2, old.output.scan("Original <strong>caption</strong>.").length
      assert_equal 1, old.output.scan("class=\"article-video-expiry-note\"").length
      assert_equal intact, [boundary, recent, future].map(&:output)
      assert originals.all? { |file| File.binread(file.path).start_with?("archived original") }
      assert site.static_files.any? { |file| file.relative_path.end_with?("orphan.mp4") }
    end
  end

  def test_other_page_protects_a_shared_clip
    old = Post.new(Time.utc(2026, 9, 1), clip("/assets/videos/old.mp4"))
    page = Page.new('<a href="https://dualeights.com/assets/videos/old.mp4">Video</a>')
    with_site([old], pages: [page]) do |site, _|
      assert_empty VideoRetention.apply(site)["omitted_files"]
      refute_includes old.output, "<video"
    end
  end

  def test_baseurl_query_strings_and_external_players
    remote = '<video src="https://another.example/assets/videos/remote.mp4"></video>'
    old = Post.new(Time.utc(2026, 9, 1), '<figure><img src="/preview/stock.jpg"></figure>' + clip("/preview/assets/videos/old.mp4?t=2&amp;x=3") + remote)
    with_site([old], baseurl: "/preview") do |site, _|
      report = VideoRetention.apply(site)
      assert_equal ["/assets/videos/old.mp4"], report["omitted_files"]
      assert_includes old.output, remote
      assert_includes old.output, '<figure><img src="/preview/stock.jpg"></figure>'
      refute_includes old.output, "/preview/assets/videos/old.mp4"
    end
  end

  def test_standalone_player_and_download_link
    html = '<article><video src="/assets/videos/old.mp4"></video><a href="/assets/videos/old.mp4">Download</a><p>Rest.</p></article>'
    result, count = VideoRetention.expire_players(html, 14, "")
    assert_equal 2, count
    assert_empty VideoRetention.clip_paths(result)
    assert_includes result, "<span>Download</span>"
    assert_includes result, "<p>Rest.</p>"
    assert_equal 1, result.scan("article-video-expiry-note").length
  end

  def test_unknown_markup_fails_instead_of_publishing_broken_media
    assert_raises(RuntimeError) { VideoRetention.expire_players('<source src="/assets/videos/old.mp4">', 14, "") }
  end

  def test_date_can_be_advanced_without_changing_sources
    post = Post.new(Time.utc(2026, 10, 13), clip("/assets/videos/recent.mp4"))
    with_site([post]) do |site, _|
      assert_empty VideoRetention.apply(site, today: Date.new(2026, 10, 27))["omitted_files"]
      assert_equal ["/assets/videos/recent.mp4"], VideoRetention.apply(site, today: Date.new(2026, 10, 28))["omitted_files"]
    end
  end

  def test_nonpositive_retention_is_rejected
    with_site([]) do |site, _|
      site.config["video_retention_days"] = 0
      assert_raises(RuntimeError) { VideoRetention.apply(site) }
    end
  end

  def test_real_build_excludes_expired_files_and_cleans_previous_output
    Dir.mktmpdir("video-retention-build") do |root|
      source = File.join(root, "source")
      destination = File.join(root, "built")
      FileUtils.mkdir_p(File.join(source, "_posts"))
      FileUtils.mkdir_p(File.join(source, "assets", "videos"))
      {"old" => "2026-10-04", "recent" => "2026-10-13"}.each do |name, date|
        File.write(File.join(source, "_posts", "#{date}-#{name}.html"),
                   "---\nlayout: null\npermalink: /#{name}/\n---\n<p>Article prose.</p>" + clip("/assets/videos/#{name}.mp4"))
        File.binwrite(File.join(source, "assets", "videos", "#{name}.mp4"), name)
      end
      config = Jekyll.configuration({"source" => source, "destination" => destination,
                                     "quiet" => true, "future" => true,
                                     "time" => Time.utc(2026, 10, 19), "plugins_dir" => []})
      Jekyll::Site.new(config).process
      refute File.exist?(File.join(destination, "assets", "videos", "old.mp4"))
      assert File.exist?(File.join(destination, "assets", "videos", "recent.mp4"))
      refute_includes File.read(File.join(destination, "old", "index.html")), "<video"
      assert_includes File.read(File.join(destination, "recent", "index.html")), "<video"

      # Rebuild into the same output: Jekyll must remove the newly expired copy,
      # not leave yesterday's file in the upload artifact.
      config["time"] = Time.utc(2026, 10, 28)
      Jekyll::Site.new(config).process
      refute File.exist?(File.join(destination, "assets", "videos", "recent.mp4"))
      refute_includes File.read(File.join(destination, "recent", "index.html")), "<video"
      assert_equal "old", File.binread(File.join(source, "assets", "videos", "old.mp4"))
      assert_equal "recent", File.binread(File.join(source, "assets", "videos", "recent.mp4"))
    end
  end
end
