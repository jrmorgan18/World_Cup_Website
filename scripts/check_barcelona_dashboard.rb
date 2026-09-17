#!/usr/bin/env ruby
# frozen_string_literal: true

# Validates the Barcelona dashboard data before it is published. The generated
# JSON and the editorial YAML have to agree on the metric slate, and every rank
# has to fall inside the field of the competition it was calculated in.

require "date"
require "json"
require "yaml"

ROOT = File.expand_path("..", __dir__)
EDITORIAL_PATH = File.join(ROOT, "_data", "barcelona_dashboard.yml")
STATS_PATH = File.join(ROOT, "_data", "barcelona_dashboard_stats.json")

METRIC_STATUSES = ["Elite", "Good", "Average", "Concern", "Problem"].freeze
FORMATS = %w[signed_integer integer decimal_1 decimal_2 signed_decimal_2 percentage_1].freeze
COMPETITIONS = %w[laliga ucl].freeze
EXPECTED_METRIC_COUNT = 16

def assert(condition, message, errors)
  errors << message unless condition
end

editorial = YAML.safe_load_file(EDITORIAL_PATH, permitted_classes: [Date], aliases: false)
stats = JSON.parse(File.read(STATS_PATH, encoding: "utf-8"))
errors = []

definitions = editorial.fetch("metric_definitions")
definition_ids = definitions.map { |definition| definition.fetch("id") }
assert(definition_ids.uniq.length == definition_ids.length, "Metric ids must be unique", errors)
assert(
  definition_ids.length == EXPECTED_METRIC_COUNT,
  "The scorecard must contain #{EXPECTED_METRIC_COUNT} metrics, found #{definition_ids.length}",
  errors
)

definitions.each do |definition|
  id = definition["id"]
  assert(%w[higher lower].include?(definition["direction"]), "#{id} has an invalid direction", errors)
  assert(FORMATS.include?(definition["format"]), "#{id} has an invalid format", errors)
  assert(!definition["description"].to_s.empty?, "#{id} needs a description", errors)
  assert(!definition["group"].to_s.empty?, "#{id} needs a group", errors)
  assert(definition["stable_delta"].is_a?(Numeric), "#{id} needs a numeric stable_delta", errors)
end

scorecard_ids = editorial.fetch("scorecard_groups").flat_map { |group| group.fetch("metric_ids") }
assert(scorecard_ids.uniq.length == scorecard_ids.length, "Scorecard metrics must not be repeated", errors)
assert(scorecard_ids.sort == definition_ids.sort, "Every metric must appear exactly once in the scorecard", errors)

# Editorial assessments are optional per metric but must be valid where present.
assessments = editorial.dig("editorial", "metric_assessments") || {}
assert(
  (assessments.keys - COMPETITIONS).empty?,
  "Metric assessments must be keyed by competition (#{COMPETITIONS.join(', ')})",
  errors
)
assessments.each do |competition, entries|
  entries.each do |metric_id, assessment|
    assert(definition_ids.include?(metric_id), "#{competition} assessment references unknown metric #{metric_id}", errors)
    assert(
      METRIC_STATUSES.include?(assessment["status"]),
      "#{competition}.#{metric_id} has an invalid status: #{assessment['status']}",
      errors
    )
    assert(
      !assessment["interpretation"].to_s.empty?,
      "#{competition}.#{metric_id} needs an interpretation",
      errors
    )
  end
end

competitions = stats.fetch("competitions")
assert(
  COMPETITIONS.all? { |key| competitions.key?(key) },
  "Both competitions must be present in the generated stats",
  errors
)

competitions.each do |key, competition|
  snapshots = competition["snapshots"] || []
  assert(!snapshots.empty?, "#{key} has no snapshots", errors)
  next if snapshots.empty?

  snapshot_ids = snapshots.map { |snapshot| snapshot["id"] }
  assert(snapshot_ids.uniq.length == snapshot_ids.length, "#{key} snapshot ids must be unique", errors)
  assert(
    competition["current_snapshot"] == snapshots.last["id"],
    "#{key} current_snapshot must be the most recent snapshot",
    errors
  )

  snapshots.each_with_index do |snapshot, index|
    label = "#{key}.#{snapshot['id']}"
    field = snapshot["teams_ranked"].to_i
    assert(field.positive?, "#{label} must record how many teams were ranked", errors)

    previous = snapshot["previous_snapshot"]
    if index.zero?
      assert(previous.nil?, "#{label} is the first snapshot and must not have a previous_snapshot", errors)
    else
      assert(
        previous == snapshots[index - 1]["id"],
        "#{label} must point at the snapshot before it",
        errors
      )
    end

    metrics = snapshot["metrics"] || {}
    assert(metrics.keys.sort == definition_ids.sort, "#{label} must contain every scorecard metric", errors)

    metrics.each do |metric_id, metric|
      value = metric["value"]
      rank = metric["rank"]
      assert(value.nil? || value.is_a?(Numeric), "#{label}.#{metric_id} value must be numeric or null", errors)
      assert(
        rank.nil? || (rank.is_a?(Integer) && rank.between?(1, field)),
        "#{label}.#{metric_id} rank must be 1–#{field} or null, found #{rank.inspect}",
        errors
      )
      assert(!metric["source"].to_s.empty?, "#{label}.#{metric_id} needs a source", errors)

      case metric_id
      when "blaugrana_index"
        assert(value.nil? || value.between?(0, 100), "#{label}.blaugrana_index must be 0–100", errors)
      when "possession_pct", "pass_accuracy", "clean_sheet_rate", "shot_conversion"
        assert(value.nil? || value.between?(0, 100), "#{label}.#{metric_id} must be a percentage", errors)
      when "ppda"
        assert(value.nil? || value.positive?, "#{label}.ppda must be positive", errors)
      end
    end
  end

  table = competition["table"] || []
  table.each do |row|
    assert(!row["team_id"].to_s.empty?, "#{key} table rows need a team id", errors)
    assert(
      row["rank"].nil? || row["rank"].is_a?(Integer),
      "#{key} table rank must be an integer, found #{row['rank'].inspect}",
      errors
    )
  end
end

# Barcelona must appear in every competition it is ranked in.
competitions.each do |key, competition|
  next if (competition["table"] || []).empty?

  assert(
    competition["table"].any? { |row| row["team_id"] == stats.dig("team", "id") },
    "#{key} table does not contain Barcelona",
    errors
  )
end

squad = stats["squad"] || []
assert(!squad.empty?, "The squad must not be empty", errors)
squad.each do |player|
  name = player["name"]
  assert(!player["player_id"].to_s.empty?, "#{name} needs a player id", errors)
  totals = player["totals"] || {}
  assert(totals["minutes"].is_a?(Integer), "#{name} needs integer total minutes", errors)
  assert(
    totals["minutes"] >= 0 && totals["minutes"] <= 90 * 80,
    "#{name} has an implausible minutes total: #{totals['minutes']}",
    errors
  )
  player.fetch("competitions", {}).each do |competition_key, split|
    assert(
      COMPETITIONS.include?(competition_key),
      "#{name} has an unexpected competition split: #{competition_key}",
      errors
    )
    assert(
      split["minutes"].nil? || split["minutes"] >= 0,
      "#{name} has negative minutes in #{competition_key}",
      errors
    )
  end
end

player_ids = squad.map { |player| player["player_id"] }
(editorial.dig("editorial", "player_notes") || {}).each_key do |player_id|
  assert(player_ids.include?(player_id), "Scouting note references a player not in the squad: #{player_id}", errors)
end

rotation = stats["rotation"] || {}
assert(rotation["window_days"].to_i.positive?, "The rotation window must be a positive number of days", errors)
(rotation["players"] || []).each do |player|
  assert(
    player["minutes"].to_i >= 0,
    "#{player['name']} cannot have negative minutes in the rotation window",
    errors
  )
  share = player["share"]
  assert(
    share.nil? || share.between?(0, 100),
    "#{player['name']} has an out-of-range minutes share: #{share.inspect}",
    errors
  )
end

congestion = stats["congestion"] || {}
assert(congestion["load_level"], "The congestion module must report a load level", errors)
assert(
  ["Light", "Moderate", "Heavy"].include?(congestion["load_level"]),
  "Unexpected congestion load level: #{congestion['load_level']}",
  errors
)

(editorial.dig("availability", "items") || []).each do |item|
  assert(!item["player"].to_s.empty?, "Availability entries need a player", errors)
  assert(!item["status"].to_s.empty?, "#{item['player']} needs an availability status", errors)
  assert(!item["source_url"].to_s.empty?, "#{item['player']} needs a source url", errors)
end

sources = editorial["sources"] || []
assert(!sources.empty?, "The dashboard must list its sources", errors)
sources.each do |source|
  assert(!source["url"].to_s.empty?, "#{source['name']} needs a url", errors)
  assert(!source["cadence"].to_s.empty?, "#{source['name']} needs an update cadence", errors)
end

assert(!(editorial["methodology_notes"] || []).empty?, "The dashboard must document its methodology", errors)

if errors.empty?
  laliga = competitions.dig("laliga", "snapshots")&.last
  ucl = competitions.dig("ucl", "snapshots")&.last
  puts "Barcelona dashboard data is valid."
  puts "  La Liga: #{laliga&.fetch('label', nil)} (#{laliga&.fetch('record', nil)})"
  puts "  Champions League: #{ucl&.fetch('label', nil)} (#{ucl&.fetch('record', nil)})"
  exit 0
end

warn "Barcelona dashboard validation failed:"
errors.each { |error| warn "  - #{error}" }
exit 1
