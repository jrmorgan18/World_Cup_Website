#!/usr/bin/env ruby
# frozen_string_literal: true

require "date"
require "json"
require "yaml"

ROOT = File.expand_path("..", __dir__)
EDITORIAL_PATH = File.join(ROOT, "_data", "ravens_dashboard.yml")
STATS_PATH = File.join(ROOT, "_data", "ravens_dashboard_stats.json")

METRIC_STATUSES = ["Elite", "Good", "Average", "Concern", "Problem"].freeze
UNIT_STATUSES = ["Elite", "Strength", "Solid", "Mixed", "Concern", "Major Concern"].freeze
CHAMPIONSHIP_STATUSES = ["Ready", "Trending Right", "Unclear", "Concern"].freeze
TRENDS = ["up", "down", "stable"].freeze
INJURY_STATUSES = ["Healthy", "Limited", "Questionable", "Doubtful", "Out", "Injured Reserve", "PUP", "Returning"].freeze
IMPORTANCE = ["Critical", "Starter", "Rotation", "Depth"].freeze

def assert(condition, message, errors)
  errors << message unless condition
end

editorial = YAML.safe_load_file(EDITORIAL_PATH, permitted_classes: [Date], aliases: false)
stats = JSON.parse(File.read(STATS_PATH, encoding: "utf-8"))
errors = []

definitions = editorial.fetch("metric_definitions")
definition_ids = definitions.map { |definition| definition.fetch("id") }
assert(definition_ids.uniq.length == definition_ids.length, "Metric ids must be unique", errors)
assert(definition_ids.length == 10, "The defensible free-source scorecard must contain ten metrics", errors)

definitions.each do |definition|
  assert(%w[higher lower].include?(definition["direction"]), "#{definition['id']} has an invalid direction", errors)
  assert(%w[signed_integer decimal_2 percentage_1].include?(definition["format"]), "#{definition['id']} has an invalid format", errors)
  assert(!definition["description"].to_s.empty?, "#{definition['id']} needs a description", errors)
end

scorecard_ids = editorial.fetch("scorecard_groups").flat_map { |group| group.fetch("metric_ids") }
assert(scorecard_ids.uniq.length == scorecard_ids.length, "Scorecard metrics must not be repeated", errors)
assert(scorecard_ids.sort == definition_ids.sort, "Every metric must appear exactly once in the scorecard", errors)
assert(scorecard_ids.none? { |id| id.include?("pressure") }, "Unverified pressure metrics must not be published", errors)

snapshots = stats.fetch("snapshots")
snapshot_ids = snapshots.map { |snapshot| snapshot.fetch("id") }
assert(snapshot_ids.uniq.length == snapshot_ids.length, "Snapshot ids must be unique", errors)
assert(snapshot_ids.include?(stats.fetch("current_snapshot")), "current_snapshot does not exist", errors)

def validate_snapshot(snapshot, definition_ids, errors)
  metrics = snapshot.fetch("metrics")
  assert(metrics.keys.sort == definition_ids.sort, "#{snapshot['id']} must contain every scorecard metric", errors)
  metrics.each do |metric_id, metric|
    value = metric["value"]
    rank = metric["rank"]
    assert(value.nil? || value.is_a?(Numeric), "#{snapshot['id']}.#{metric_id} value must be numeric or null", errors)
    assert(rank.nil? || (rank.is_a?(Integer) && rank.between?(1, 32)), "#{snapshot['id']}.#{metric_id} rank must be 1–32 or null", errors)
    assert(!metric["source"].to_s.empty?, "#{snapshot['id']}.#{metric_id} needs a source", errors)
  end
end

snapshots.each { |snapshot| validate_snapshot(snapshot, definition_ids, errors) }
benchmark = stats.fetch("benchmark_snapshot")
validate_snapshot(benchmark, definition_ids, errors)
benchmark.fetch("metrics").each do |metric_id, metric|
  assert(!metric["value"].nil?, "Benchmark #{metric_id} must be populated", errors)
  assert(!metric["rank"].nil?, "Benchmark #{metric_id} must have a league rank", errors)
end

metric_editorial = editorial.dig("editorial", "metric_assessments")
assert(metric_editorial.keys.sort == definition_ids.sort, "Editorial assessments must match the metrics", errors)
metric_editorial.each do |metric_id, assessment|
  status = assessment["status"]
  assert(status.nil? || METRIC_STATUSES.include?(status), "#{metric_id} has an invalid editorial status", errors)
end

expected_units = ["Quarterback", "Running backs", "Wide receivers", "Tight ends", "Offensive line", "Defensive line", "Edge rushers", "Linebackers", "Secondary", "Specialists"]
units = editorial.dig("editorial", "units")
assert(units.map { |unit| unit["name"] } == expected_units, "Unit report card must contain the ten expected units in order", errors)
units.each do |unit|
  assert(UNIT_STATUSES.include?(unit["assessment"]), "#{unit['name']} has an invalid assessment", errors)
  assert(TRENDS.include?(unit["trend"]), "#{unit['name']} has an invalid trend", errors)
end

changes = editorial.dig("editorial", "weekly_changes")
assert(changes.length.between?(3, 5), "What Changed must contain 3–5 items", errors)
changes.each { |change| assert(TRENDS.include?(change["direction"]), "#{change['title']} has an invalid direction", errors) }

championship = editorial.dig("editorial", "championship_check")
assert(championship.length == 5, "Championship Check must contain exactly five items", errors)
championship.each do |item|
  assert(CHAMPIONSHIP_STATUSES.include?(item["status"]), "#{item['category']} has an invalid championship status", errors)
end

editorial.fetch("injuries").each do |injury|
  assert(INJURY_STATUSES.include?(injury["status"]), "#{injury['player']} has an invalid injury status", errors)
  assert(IMPORTANCE.include?(injury["importance"]), "#{injury['player']} has an invalid importance", errors)
  assert(!injury["expected_availability"].to_s.empty?, "#{injury['player']} needs explicit availability text", errors)
  assert(injury["source_url"].to_s.start_with?("https://"), "#{injury['player']} needs a linked source", errors)
end

preseason_games = editorial.fetch("preseason_games")
preseason_games.each do |game|
  assert(%w[W L T].include?(game["result"]), "#{game['week']} has an invalid result", errors)
  expected = game["ravens_score"] > game["opponent_score"] ? "W" : (game["ravens_score"] < game["opponent_score"] ? "L" : "T")
  assert(game["result"] == expected, "#{game['week']} result does not match its score", errors)
  assert(game["recap_url"].to_s.start_with?("https://www.baltimoreravens.com/"), "#{game['week']} needs an official recap", errors)
end
points_for = preseason_games.sum { |game| game["ravens_score"] }
points_against = preseason_games.sum { |game| game["opponent_score"] }
assert(points_for == editorial.dig("preseason_form", "points_for"), "Preseason points for do not match the game list", errors)
assert(points_against == editorial.dig("preseason_form", "points_against"), "Preseason points against do not match the game list", errors)
assert(points_for - points_against == editorial.dig("preseason_form", "point_differential"), "Preseason point differential does not match", errors)

assert(stats.dig("header", "record").match?(/^\d{1,2}-\d{1,2}(?:-\d{1,2})?$/), "Header record has an invalid format", errors)
assert(stats.dig("header", "next_game", "opponent_abbr") == "IND", "Expected Week 1 opponent is not Indianapolis", errors) if stats.fetch("season") == 2026
Date.iso8601(editorial.dig("meta", "last_updated").to_s)
Date.iso8601(stats.fetch("as_of"))

if errors.any?
  warn "Ravens dashboard validation failed with #{errors.length} error(s):"
  errors.each { |error| warn "  - #{error}" }
  exit 1
end

puts "Ravens dashboard data passed source, schema, benchmark, and current-state checks."
