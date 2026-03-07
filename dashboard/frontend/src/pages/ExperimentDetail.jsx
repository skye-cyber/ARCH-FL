import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { experimentService } from "../services/api";
import {
  FaFlask,
  FaSpinner,
  FaExclamationTriangle,
  FaChartLine,
  FaClock,
  FaInfoCircle,
  FaPlay,
  FaStop,
  FaTrash,
  FaRedo,
  FaCheck,
} from "react-icons/fa";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

export default function ExperimentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [experiment, setExperiment] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);

  useEffect(() => {
    const fetchExperimentData = async () => {
      try {
        setLoading(true);

        // Fetch experiment details
        const experimentResponse = await experimentService.getById(id);
        setExperiment(experimentResponse.data);

        // Fetch experiment results
        const resultsResponse = await experimentService.getResults(id);
        setResults(resultsResponse.data);

        setLoading(false);
      } catch (err) {
        console.error("Error fetching experiment data:", err);
        setError("Failed to load experiment data. Please try again later.");
        setLoading(false);
      }
    };

    fetchExperimentData();
  }, [id]);

  // Prepare chart data
  const prepareChartData = () => {
    if (results.length === 0) return null;

    // Group results by round
    const rounds = {};
    results.forEach((result) => {
      if (!rounds[result.round]) {
        rounds[result.round] = { accuracy: [], loss: [] };
      }
      if (result.accuracy !== null && result.accuracy !== undefined) {
        rounds[result.round].accuracy.push(result.accuracy);
      }
      if (result.loss !== null && result.loss !== undefined) {
        rounds[result.round].loss.push(result.loss);
      }
    });

    const roundNumbers = Object.keys(rounds).sort(
      (a, b) => parseInt(a) - parseInt(b),
    );

    return {
      labels: roundNumbers.map((r) => `Round ${r}`),
      datasets: [
        {
          label: "Average Accuracy",
          data: roundNumbers.map((r) => {
            const accValues = rounds[r].accuracy;
            return accValues.length > 0
              ? accValues.reduce((a, b) => a + b, 0) / accValues.length
              : 0;
          }),
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.1,
          yAxisID: "y",
        },
        {
          label: "Average Loss",
          data: roundNumbers.map((r) => {
            const lossValues = rounds[r].loss;
            return lossValues.length > 0
              ? lossValues.reduce((a, b) => a + b, 0) / lossValues.length
              : 0;
          }),
          borderColor: "rgb(239, 68, 68)",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.1,
          yAxisID: "y1",
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Experiment Performance Over Rounds",
      },
    },
    scales: {
      y: {
        type: "linear",
        display: true,
        position: "left",
        title: {
          display: true,
          text: "Accuracy",
        },
      },
      y1: {
        type: "linear",
        display: true,
        position: "right",
        title: {
          display: true,
          text: "Loss",
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <FaSpinner className="animate-spin text-blue-600 text-2xl mx-auto mb-4" />
        <p className="text-gray-600">Loading experiment details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <FaExclamationTriangle className="text-red-600 text-2xl mx-auto mb-4" />
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const performAction = async (actionType) => {
    setActionLoading(true);
    setActionResult(null);

    try {
      let response;
      switch (actionType) {
        case "run":
          response = await experimentService.run(id);
          break;
        case "cancel":
          response = await experimentService.cancel(id);
          break;
        case "delete":
          response = await experimentService.delete(id);
          navigate("/experiments");
          return;
        case "restart":
          response = await experimentService.restart(id);
          break;
        default:
          return;
      }

      // Refresh experiment data
      const experimentResponse = await experimentService.getById(id);
      setExperiment(experimentResponse.data);

      setActionResult({
        type: "success",
        message: response.message,
      });
    } catch (error) {
      console.error(`Error performing ${actionType} action:`, error);
      setActionResult({
        type: "error",
        message: `Failed to perform ${actionType} action: ${error.response?.data?.detail || error.message}`,
      });
    } finally {
      setActionLoading(false);
    }
  };

  if (!experiment) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <FaExclamationTriangle className="text-yellow-500 text-2xl mx-auto mb-4" />
        <p className="text-yellow-600">Experiment not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Action Result Notification */}
      {actionResult && (
        <div
          className={`fixed top-4 right-4 z-50 bg-${actionResult.type === "success" ? "green" : "red"}-100 border border-${actionResult.type === "success" ? "green" : "red"}-400 text-${actionResult.type === "success" ? "green" : "red"}-700 px-4 py-3 rounded-lg flex items-center`}
        >
          <FaCheck
            className={`mr-2 ${actionResult.type === "success" ? "text-green-600" : "text-red-600"}`}
          />
          <span>{actionResult.message}</span>
          <button
            onClick={() => setActionResult(null)}
            className="ml-2 text-xs underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Back navigation */}
      <div className="bg-white rounded-lg shadow p-4">
        <Link
          to="/experiments"
          className="inline-flex items-center text-blue-600 hover:text-blue-800"
        >
          ← Back to Experiments
        </Link>
      </div>

      {/* Experiment header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center">
              <FaFlask className="text-blue-600 mr-2" />
              {experiment.name}
            </h2>
            <p className="text-gray-600 mt-2">
              {experiment.description || "No description provided"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                experiment.status === "completed"
                  ? "bg-green-100 text-green-800"
                  : experiment.status === "running"
                    ? "bg-blue-100 text-blue-800"
                    : experiment.status === "failed"
                      ? "bg-red-100 text-red-800"
                      : experiment.status === "cancelled"
                        ? "bg-gray-100 text-gray-800"
                        : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {experiment.status}
            </span>
            <div className="flex items-center gap-2">
              {experiment.status === "pending" && (
                <button
                  onClick={() => performAction("run")}
                  disabled={actionLoading}
                  className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center"
                >
                  <FaPlay className="mr-1" />
                  <span>Run</span>
                </button>
              )}
              {experiment.status === "running" && (
                <button
                  onClick={() => performAction("cancel")}
                  disabled={actionLoading}
                  className="text-yellow-600 hover:text-yellow-700 text-sm font-medium flex items-center"
                >
                  <FaStop className="mr-1" />
                  <span>Cancel</span>
                </button>
              )}
              {(experiment.status === "completed" ||
                experiment.status === "cancelled" ||
                experiment.status === "failed") && (
                <button
                  onClick={() => performAction("restart")}
                  disabled={actionLoading}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
                >
                  <FaRedo className="mr-1" />
                  <span>Restart</span>
                </button>
              )}
              {experiment.status !== "running" && (
                <button
                  onClick={() => performAction("delete")}
                  disabled={actionLoading}
                  className="text-red-600 hover:text-red-700 text-sm font-medium flex items-center"
                >
                  <FaTrash className="mr-1" />
                  <span>Delete</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Experiment details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <FaInfoCircle className="text-gray-600 mr-2" />
            Experiment Configuration
          </h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">Dataset</p>
              <p className="font-medium">{experiment.dataset_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Architecture</p>
              <p className="font-medium">{experiment.architecture_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Number of Clients</p>
              <p className="font-medium">{experiment.num_clients}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Data Distribution</p>
              <p className="font-medium">
                {experiment.iid ? "IID" : "Non-IID"}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p className="font-medium">
                {new Date(experiment.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Last Updated</p>
              <p className="font-medium">
                {new Date(experiment.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <FaChartLine className="text-gray-600 mr-2" />
            Training Parameters
          </h3>
          <div className="space-y-3">
            {Object.entries(JSON.parse(experiment.parameters)).map(
              ([key, value]) => (
                <div key={key}>
                  <p className="text-sm text-gray-500 capitalize">
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="font-medium">
                    {typeof value === "object"
                      ? JSON.stringify(value)
                      : String(value)}
                  </p>
                </div>
              ),
            )}
          </div>
        </div>
      </div>

      {/* Performance chart */}
      {chartData && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="h-96">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>
      )}

      {/* Results table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <FaChartLine className="text-gray-600 mr-2" />
            Detailed Results ({results.length} records)
          </h3>
        </div>
        {results.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Round
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Loss
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.slice(0, 10).map((result) => (
                  <tr key={result.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium">{result.round}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm">
                        Client {result.client_id || "Global"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {result.accuracy !== null &&
                      result.accuracy !== undefined ? (
                        <span className="text-green-600 font-medium">
                          {(result.accuracy * 100).toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {result.loss !== null && result.loss !== undefined ? (
                        <span className="text-red-600 font-medium">
                          {result.loss.toFixed(4)}
                        </span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-500">
                        {new Date(result.timestamp).toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {results.length > 10 && (
              <div className="p-4 text-center text-sm text-gray-500">
                Showing first 10 results. Total: {results.length} records.
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            <FaClock className="text-2xl mx-auto mb-2 text-gray-400" />
            <p>No results available for this experiment yet</p>
            {experiment.status === "pending" && (
              <p className="text-sm mt-1">
                Results will appear once the experiment starts
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
