import { useState, useEffect } from "react";
import { useNavigate } from "react-router";

interface AuditEvent {
  id: string;
  created_at: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  actor_username: string | null;
  severity: string;
  description: string;
  metadata: any;
}

interface BiasAlert {
  type: string;
  severity: string;
  message: string;
}

interface ScoreStatistics {
  mean: number;
  median: number;
  std_dev: number;
  variance: number;
  min: number;
  max: number;
  skewness: number;
}

const renderJson = (value: unknown) => {
  if (!value) return null;
  return (
    <pre className="mt-2 whitespace-pre-wrap rounded-md bg-slate-900/60 p-3 text-xs text-slate-200">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
};

export default function AuditDashboard() {
  const navigate = useNavigate();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({
    event_type: "",
    severity: "",
    limit: "50"
  });

  useEffect(() => {
    fetchAuditEvents();
  }, [filter]);

  const fetchAuditEvents = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem("access_token") || localStorage.getItem("authToken");
      
      const params = new URLSearchParams();
      if (filter.event_type) params.append("event_type", filter.event_type);
      if (filter.severity) params.append("severity", filter.severity);
      params.append("limit", filter.limit);

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        `/api/audit/ranking/?${params.toString()}`,
        { headers }
      );

      if (response.ok) {
        const data = await response.json();
        setEvents(data.results || data);
      } else if (response.status === 401 || response.status === 403) {
        setError("Authentication required. Please log in.");
        setTimeout(() => navigate("/login"), 2000);
      } else {
        const errorText = await response.text();
        setError(`Failed to fetch audit events: ${response.status} - ${errorText.substring(0, 100)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "verbose":
        return "bg-slate-700 text-slate-200 border-slate-600";
      case "debug":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "log":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getEventTypeIcon = (eventType: string) => {
    if (eventType.includes("bias")) return "BIAS";
    if (eventType.includes("started")) return "START";
    if (eventType.includes("completed")) return "DONE";
    if (eventType.includes("failed")) return "FAIL";
    if (eventType.includes("scored")) return "SCORE";
    return "EVENT";
  };

  const renderBiasDetails = (event: AuditEvent) => {
    if (!event.event_type.includes("bias")) return null;

    const biasIndicators = event.metadata?.bias_indicators || [];
    const recommendations = event.metadata?.recommendations || [];
    const stats: ScoreStatistics | null = event.metadata?.score_statistics;

    return (
      <div className="mt-3 space-y-3">
        {/* Bias Alerts */}
        {biasIndicators.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <h4 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
              Bias Indicators Detected ({biasIndicators.length})
            </h4>
            <div className="space-y-2">
              {biasIndicators.map((alert: BiasAlert, idx: number) => (
                <div
                  key={idx}
                  className={`p-2 rounded border ${
                    alert.severity === "critical"
                      ? "bg-red-50 border-red-300"
                      : alert.severity === "warning"
                      ? "bg-yellow-50 border-yellow-300"
                      : "bg-blue-50 border-blue-300"
                  }`}
                >
                  <div className="font-medium text-sm">
                    {alert.type.replace(/_/g, " ").toUpperCase()}
                  </div>
                  <div className="text-sm mt-1">{alert.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Score Statistics */}
        {stats && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-3">
            <h4 className="font-semibold text-blue-300 mb-2">Score Distribution</h4>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-slate-400">Mean:</span>{" "}
                <span className="font-mono text-slate-200">{stats.mean.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-400">Median:</span>{" "}
                <span className="font-mono text-slate-200">{stats.median.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-400">Std Dev:</span>{" "}
                <span className="font-mono text-slate-200">{stats.std_dev.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-400">Range:</span>{" "}
                <span className="font-mono text-slate-200">
                  {stats.min.toFixed(0)} - {stats.max.toFixed(0)}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Variance:</span>{" "}
                <span className="font-mono text-slate-200">{stats.variance.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-400">Skewness:</span>{" "}
                <span className="font-mono text-slate-200">{stats.skewness.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-3">
            <h4 className="font-semibold text-green-300 mb-2">Recommendations</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-300">
              {recommendations.map((rec: string, idx: number) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderDecisionDetails = (event: AuditEvent) => {
    if (!event.event_type.includes("ranking.candidate.scored")) return null;

    const details = event.metadata?.details || {};
    const inputData = details.input_data || null;

    return (
      <div className="mt-4 rounded-lg border border-slate-700/70 bg-slate-900/50 p-4">
        <h4 className="text-sm font-semibold text-slate-200">Decision Details</h4>
        <div className="mt-2 grid grid-cols-1 gap-3 text-sm text-slate-300 md:grid-cols-3">
          <div>
            <span className="text-slate-400">Candidate ID:</span>{" "}
            <span className="font-mono">{event.metadata?.candidate_id || "-"}</span>
          </div>
          <div>
            <span className="text-slate-400">Score:</span>{" "}
            <span className="font-mono">
              {typeof event.metadata?.score === "number"
                ? event.metadata.score.toFixed(2)
                : "-"}
            </span>
          </div>
          <div>
            <span className="text-slate-400">Rank:</span>{" "}
            <span className="font-mono">{event.metadata?.rank ?? "-"}</span>
          </div>
        </div>
        <div className="mt-3 text-sm text-slate-300">
          <div className="text-slate-400">Input data used for scoring:</div>
          {renderJson(inputData)}
        </div>
        {details && details.weights_used && (
          <div className="mt-3 text-sm text-slate-300">
            <div className="text-slate-400">Weights used:</div>
            {renderJson(details.weights_used)}
          </div>
        )}
        {details && (details.matched_items || details.missing_items) && (
          <div className="mt-3 text-sm text-slate-300">
            <div className="text-slate-400">Matched / Missing items:</div>
            {renderJson({
              matched: details.matched_items || {},
              missing: details.missing_items || {},
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">
            Audit & Compliance Dashboard
          </h1>
          <p className="text-slate-400">
            Monitor ranking events, bias detection, and compliance logs
          </p>
        </div>

        {/* Filters */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Event Type
              </label>
              <select
                value={filter.event_type}
                onChange={(e) => setFilter({ ...filter, event_type: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-slate-100 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">All Events</option>
                <optgroup label="Ranking Events">
                  <option value="ranking.bias.checked">Bias Checked</option>
                  <option value="ranking.bias.detected">Bias Detected</option>
                  <option value="ranking.run.started">Run Started</option>
                  <option value="ranking.run.completed">Run Completed</option>
                  <option value="ranking.run.failed">Run Failed</option>
                  <option value="ranking.scoring.completed">Scoring Completed</option>
                  <option value="ranking.candidates.loaded">Candidates Loaded</option>
                  <option value="ranking.candidate.scored">Candidate Scored</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Severity
              </label>
              <select
                value={filter.severity}
                onChange={(e) => setFilter({ ...filter, severity: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-slate-100 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">All Severities</option>
                <option value="log">Log</option>
                <option value="debug">Debug</option>
                <option value="verbose">Verbose</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Limit
              </label>
              <select
                value={filter.limit}
                onChange={(e) => setFilter({ ...filter, limit: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-slate-100 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="10">10 events</option>
                <option value="50">50 events</option>
                <option value="100">100 events</option>
                <option value="500">500 events</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={fetchAuditEvents}
                disabled={loading}
                className="w-full px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:bg-slate-700 transition-colors"
              >
                {loading ? "Loading..." : "Refresh"}
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">Error: {error}</p>
          </div>
        )}

        {/* Events List */}
        <div className="space-y-4">
          {events.length === 0 && !loading && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-lg shadow-md p-12 text-center">
              <p className="text-slate-400 text-lg">No audit events found</p>
              <p className="text-slate-500 text-sm mt-2">
                Try adjusting your filters or run a ranking to generate events
              </p>
            </div>
          )}

          {events.map((event) => (
            <div
              key={event.id}
              className="bg-slate-900/60 border border-slate-800 rounded-lg shadow-md border-l-4 border-l-emerald-500 hover:shadow-lg transition-shadow"
            >
              <div className="p-6">
                {/* Event Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-semibold text-slate-400">
                      {getEventTypeIcon(event.event_type)}
                    </span>
                    <div>
                      <h3 className="font-semibold text-lg text-slate-100">
                        {event.event_type}
                      </h3>
                      <p className="text-sm text-slate-400 mt-1">{event.description}</p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(
                      event.severity
                    )}`}
                  >
                    {event.severity.toUpperCase()}
                  </span>
                </div>

                {/* Event Metadata */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-4 pt-4 border-t border-slate-700">
                  <div>
                    <span className="text-slate-400">Timestamp:</span>
                    <p className="font-mono text-xs mt-1 text-slate-300">
                      {new Date(event.created_at).toLocaleString()}
                    </p>
                  </div>
                  {event.actor_username && (
                    <div>
                      <span className="text-slate-400">Actor:</span>
                      <p className="font-medium mt-1 text-slate-300">
                        {event.actor_username}
                      </p>
                    </div>
                  )}
                  {event.entity_id && (
                    <div>
                      <span className="text-slate-400">Entity ID:</span>
                      <p className="font-mono text-xs mt-1 text-slate-300">{event.entity_id}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-slate-400">Type:</span>
                    <p className="font-medium mt-1 text-slate-300">{event.entity_type}</p>
                  </div>
                </div>

                {/* Bias-specific details */}
                {renderBiasDetails(event)}
                {renderDecisionDetails(event)}
              </div>
            </div>
          ))}
        </div>

        {loading && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-lg shadow-md p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
            <p className="text-slate-400 mt-4">Loading audit events...</p>
          </div>
        )}
      </div>
    </div>
  );
}
