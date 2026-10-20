# Keep short-lived article clips out of the Pages artifact once they expire.
# Originals and article source files are never changed by this build hook.
require "cgi"
require "date"
require "set"
require "uri"

module VideoRetention
  FIGURE = /<figure\b[^>]*>.*?<\/figure\s*>/mi
  VIDEO = /<video\b[^>]*>.*?<\/video\s*>/mi
  LINK = /<a\b[^>]*>.*?<\/a\s*>/mi

  def self.clip_paths(html, baseurl = "")
    html.to_s.scan(/\b(?:src|href)\s*=\s*(["'])(.*?)\1/mi).filter_map do |_, value|
      uri = URI.parse(CGI.unescapeHTML(value))
      next if uri.host && !%w[dualeights.com www.dualeights.com].include?(uri.host)
      next if uri.scheme && !%w[http https].include?(uri.scheme)

      path = uri.path.to_s
      path = path.delete_prefix(baseurl) unless baseurl.empty?
      next unless path.start_with?("/assets/videos/")
      next if path.split("/").any? { |part| %w[. ..].include?(part) }

      path
    rescue URI::InvalidURIError
      nil
    end.to_set
  end

  def self.expire_players(html, days, baseurl)
    removed = 0
    notice = "<p class=\"article-video-expiry-note\"><em>Video clips are available for #{days} days after publication. This article's clips have been archived.</em></p>"
    archive_notice = lambda do
      if removed.zero?
        removed += 1
        notice + "\n"
      else
        removed += 1
        ""
      end
    end
    result = html.gsub(FIGURE) do |figure|
      next figure unless figure.match?(VIDEO) && !clip_paths(figure, baseurl).empty?

      # Captions are editorial text too: retain their wording as ordinary prose.
      archive_notice.call + figure.scan(/<figcaption\b[^>]*>(.*?)<\/figcaption\s*>/mi).map do |caption|
        "<p class=\"article-clip-caption\">#{caption.first}</p>"
      end.join("\n")
    end
    result = result.gsub(VIDEO) do |video|
      next video if clip_paths(video, baseurl).empty?

      archive_notice.call
    end
    result = result.gsub(LINK) do |link|
      next link if clip_paths(link, baseurl).empty?

      archive_notice.call + "<span>#{link.sub(/\A<a\b[^>]*>/mi, '').sub(/<\/a\s*>\z/mi, '')}</span>"
    end
    unless clip_paths(result, baseurl).empty?
      raise "Video retention: unsupported clip markup remains in an expired article"
    end
    [result, removed]
  end

  def self.apply(site, today: site.time.utc.to_date)
    days = Integer(site.config.fetch("video_retention_days", 14))
    raise "video_retention_days must be positive" unless days.positive?

    baseurl = site.config.fetch("baseurl", "").to_s.sub(%r{/$}, "")
    cutoff = today - days
    candidates = Set.new
    expired_posts = 0
    removed_players = 0
    site.posts.docs.each do |post|
      # Keep the complete boundary date; only articles MORE than 14 days old expire.
      next unless post.date.to_date < cutoff

      paths = clip_paths(post.output, baseurl)
      next if paths.empty?

      candidates.merge(paths)
      post.output, removed = expire_players(post.output, days, baseurl)
      expired_posts += 1
      removed_players += removed
    end

    # A reused clip must remain available if a current article or another page
    # still references it. Never remove unrelated/unrecognized static files.
    documents = site.collections.values.flat_map(&:docs)
    referenced = (documents + site.pages).each_with_object(Set.new) do |page, paths|
      paths.merge(clip_paths(page.output, baseurl))
    end
    retired = candidates - referenced
    omitted_bytes = 0
    omitted_files = []
    site.static_files.reject! do |file|
      path = file.relative_path.tr("\\", "/")
      next false unless retired.include?(path)

      omitted_files << path
      omitted_bytes += File.size(file.path)
      true
    end
    report = { "as_of" => today.iso8601, "days" => days,
               "expired_articles" => expired_posts, "removed_players" => removed_players,
               "omitted_files" => omitted_files, "omitted_bytes" => omitted_bytes }
    site.data["video_retention_report"] = report
    report
  end
end

Jekyll::Hooks.register :site, :post_render do |site|
  report = VideoRetention.apply(site)
  Jekyll.logger.info "Video retention:", "#{report['expired_articles']} expired articles; #{report['omitted_files'].length} clips / #{report['omitted_bytes']} bytes excluded (#{report['days']}-day policy)"
end
