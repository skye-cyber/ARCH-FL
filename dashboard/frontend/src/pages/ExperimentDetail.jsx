import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { experimentService } from "../services/api";
import {
  FlaskConical,
  Loader2,
  AlertTriangle,
  LineChart,
  Clock,
  Info,
  Play,
  Square,
  Trash2,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronLeft,
  Database,
  Network,
  Users,
  GitBranch,
  Settings2,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Download,
  Share2,
  Eye,
  Calendar,
  Activity,
  Gauge,
  Layers,
  Zap,
  PieChart,
  Table2,
  Maximize2,
  Minimize2,
} from "lucide-react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
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
  const [viewMode, setViewMode] = useState("chart"); // 'chart' or 'table'
  const [expandedImage, setExpandedImage] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState("accuracy");
  const [timeRange, setTimeRange] = useState("all");

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

  const getStatusConfig = (status) => {
    switch (status) {
      case "completed":
        return {
          icon: CheckCircle2,
          color: "green",
          bg: "bg-green-50",
          text: "text-green-700",
          border: "border-green-200",
          gradient: "from-green-500 to-emerald-500",
          message: "Experiment completed successfully",
        };
      case "running":
        return {
          icon: Activity,
          color: "blue",
          bg: "bg-blue-50",
          text: "text-blue-700",
          border: "border-blue-200",
          gradient: "from-blue-500 to-indigo-500",
          message: "Training in progress",
        };
      case "failed":
        return {
          icon: XCircle,
          color: "red",
          bg: "bg-red-50",
          text: "text-red-700",
          border: "border-red-200",
          gradient: "from-red-500 to-rose-500",
          message: "Training failed - check logs",
        };
      case "cancelled":
        return {
          icon: AlertCircle,
          color: "gray",
          bg: "bg-gray-50",
          text: "text-gray-700",
          border: "border-gray-200",
          gradient: "from-gray-500 to-slate-500",
          message: "Experiment cancelled",
        };
      default:
        return {
          icon: Clock,
          color: "yellow",
          bg: "bg-yellow-50",
          text: "text-yellow-700",
          border: "border-yellow-200",
          gradient: "from-yellow-500 to-amber-500",
          message: "Waiting to start",
        };
    }
  };

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

    // Apply time range filter
    const filteredRounds =
      timeRange === "all"
        ? roundNumbers
        : roundNumbers.slice(-parseInt(timeRange));

    return {
      labels: filteredRounds.map((r) => `Round ${r}`),
      datasets: [
        {
          label: "Average Accuracy",
          data: filteredRounds.map((r) => {
            const accValues = rounds[r].accuracy;
            return accValues.length > 0
              ? (accValues.reduce((a, b) => a + b, 0) / accValues.length) * 100
              : 0;
          }),
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y",
        },
        {
          label: "Average Loss",
          data: filteredRounds.map((r) => {
            const lossValues = rounds[r].loss;
            return lossValues.length > 0
              ? lossValues.reduce((a, b) => a + b, 0) / lossValues.length
              : 0;
          }),
          borderColor: "rgb(239, 68, 68)",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.4,
          fill: true,
          yAxisID: "y1",
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          usePointStyle: true,
          boxWidth: 6,
        },
      },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.8)",
        titleColor: "rgb(243, 244, 246)",
        bodyColor: "rgb(209, 213, 219)",
        borderColor: "rgb(75, 85, 99)",
        borderWidth: 1,
      },
    },
    scales: {
      y: {
        type: "linear",
        display: true,
        position: "left",
        title: {
          display: true,
          text: "Accuracy (%)",
          color: "rgb(107, 114, 128)",
        },
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
      },
      y1: {
        type: "linear",
        display: true,
        position: "right",
        title: {
          display: true,
          text: "Loss",
          color: "rgb(107, 114, 128)",
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const chartData = prepareChartData();

  // Calculate summary statistics
  const calculateStats = () => {
    if (results.length === 0) return null;

    const accuracies = results
      .filter((r) => r.accuracy !== null)
      .map((r) => r.accuracy);
    const losses = results.filter((r) => r.loss !== null).map((r) => r.loss);

    return {
      bestAccuracy:
        accuracies.length > 0 ? Math.max(...accuracies) * 100 : null,
      avgAccuracy:
        accuracies.length > 0
          ? (accuracies.reduce((a, b) => a + b, 0) / accuracies.length) * 100
          : null,
      bestLoss: losses.length > 0 ? Math.min(...losses) : null,
      totalRounds: Math.max(...results.map((r) => r.round)),
      totalRecords: results.length,
    };
  };

  const stats = calculateStats();
  const status = experiment ? getStatusConfig(experiment.status) : null;
  const StatusIcon = status?.icon;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md"
        >
          <div className="relative">
            <motion.div
              animate={{
                rotate: 360,
                scale: [1, 1.1, 1],
              }}
              transition={{
                rotate: { duration: 2, repeat: Infinity, ease: "linear" },
                scale: { duration: 1, repeat: Infinity },
              }}
              className="mb-6"
            >
              <FlaskConical className="w-16 h-16 text-blue-600 mx-auto" />
            </motion.div>
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute -top-2 -right-2 w-4 h-4 bg-blue-500 rounded-full"
            />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Loading Experiment
          </h3>
          <p className="text-gray-500">
            Fetching experiment details and results...
          </p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md"
        >
          <div className="bg-red-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-10 h-10 text-red-600" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Unable to Load Experiment
          </h3>
          <p className="text-gray-500 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-600/20"
          >
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  if (!experiment) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Experiment Not Found
          </h3>
          <p className="text-gray-500 mb-6">
            The experiment you're looking for doesn't exist.
          </p>
          <Link
            to="/experiments"
            className="inline-flex items-center px-6 py-3 bg-gray-900 text-white font-medium rounded-xl hover:bg-gray-800 transition-all"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back to Experiments
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50 pb-8">
      {/* Action Result Notification */}
      <AnimatePresence>
        {actionResult && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className={`fixed top-4 right-4 z-50 bg-${actionResult.type === "success" ? "green" : "red"}-50 border border-${actionResult.type === "success" ? "green" : "red"}-200 rounded-xl shadow-lg p-4 max-w-md`}
          >
            <div className="flex items-start">
              {actionResult.type === "success" ? (
                <CheckCircle2 className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p
                  className={`text-sm font-medium text-${actionResult.type === "success" ? "green" : "red"}-800`}
                >
                  {actionResult.type === "success" ? "Success" : "Error"}
                </p>
                <p
                  className={`text-xs text-${actionResult.type === "success" ? "green" : "red"}-600 mt-1`}
                >
                  {actionResult.message}
                </p>
              </div>
              <button
                onClick={() => setActionResult(null)}
                className={`ml-4 text-${actionResult.type === "success" ? "green" : "red"}-500 hover:text-${actionResult.type === "success" ? "green" : "red"}-700`}
              >
                <XCircle className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/experiments"
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </Link>
              <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
                <FlaskConical className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {experiment.name}
                </h1>
                <p className="text-sm text-gray-500 mt-0.5 flex items-center">
                  <Calendar className="w-3 h-3 mr-1" />
                  Created {new Date(experiment.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              {status && (
                <div
                  className={`flex items-center px-3 py-1.5 ${status.bg} border ${status.border} rounded-lg mr-2`}
                >
                  <StatusIcon className={`w-4 h-4 ${status.text} mr-2`} />
                  <span className={`text-sm font-medium ${status.text}`}>
                    {experiment.status}
                  </span>
                </div>
              )}

              {experiment.status === "pending" && (
                <button
                  onClick={() => performAction("run")}
                  disabled={actionLoading}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium rounded-xl hover:from-green-700 hover:to-emerald-700 transition-all shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  Run
                </button>
              )}
              {experiment.status === "running" && (
                <button
                  onClick={() => performAction("cancel")}
                  disabled={actionLoading}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-yellow-600 to-amber-600 text-white text-sm font-medium rounded-xl hover:from-yellow-700 hover:to-amber-700 transition-all shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Square className="w-4 h-4 mr-2" />
                  )}
                  Cancel
                </button>
              )}
              {(experiment.status === "completed" ||
                experiment.status === "cancelled" ||
                experiment.status === "failed") && (
                <button
                  onClick={() => performAction("restart")}
                  disabled={actionLoading}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RotateCcw className="w-4 h-4 mr-2" />
                  )}
                  Restart
                </button>
              )}
              {experiment.status !== "running" && (
                <button
                  onClick={() => performAction("delete")}
                  disabled={actionLoading}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-red-600 to-rose-600 text-white text-sm font-medium rounded-xl hover:from-red-700 hover:to-rose-700 transition-all shadow-sm disabled:opacity-50"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 mr-2" />
                  )}
                  Delete
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Database className="w-4 h-4 text-blue-600" />
                </div>
                <span className="text-xs text-gray-400">Dataset</span>
              </div>
              <p className="text-sm font-medium text-gray-900 mb-1">
                {experiment.dataset_name}
              </p>
              <p className="text-xs text-gray-500">Medical Imaging</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Network className="w-4 h-4 text-purple-600" />
                </div>
                <span className="text-xs text-gray-400">Architecture</span>
              </div>
              <p className="text-sm font-medium text-gray-900 mb-1">
                {experiment.architecture_name}
              </p>
              <p className="text-xs text-gray-500">Neural Network</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="w-4 h-4 text-green-600" />
                </div>
                <span className="text-xs text-gray-400">Clients</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-1">
                {experiment.num_clients}
              </p>
              <p className="text-xs text-gray-500">Active Participants</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <GitBranch className="w-4 h-4 text-amber-600" />
                </div>
                <span className="text-xs text-gray-400">Distribution</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-1">
                {experiment.iid ? "IID" : "Non-IID"}
              </p>
              <p className="text-xs text-gray-500">
                {experiment.iid ? "Uniform" : "Skewed"} Data
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-5 text-white"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 bg-white/20 rounded-lg">
                  <Activity className="w-4 h-4 text-white" />
                </div>
                <span className="text-xs text-blue-200">Progress</span>
              </div>
              <p className="text-2xl font-bold mb-1">
                {stats
                  ? `${Math.round((stats.totalRounds / (experiment.parameters?.epochs || 1)) * 100)}%`
                  : "0%"}
              </p>
              <p className="text-xs text-blue-200">
                Round {stats?.totalRounds || 0} of{" "}
                {experiment.parameters?.epochs || 10}
              </p>
            </motion.div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Configuration */}
            <div className="space-y-6">
              {/* Experiment Configuration */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
              >
                <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
                  <Settings2 className="w-5 h-5 mr-2 text-gray-600" />
                  Configuration
                </h3>
                <div className="space-y-4">
                  {[
                    {
                      label: "Epochs",
                      value: experiment.parameters?.epochs,
                      icon: Layers,
                      color: "blue",
                    },
                    {
                      label: "Batch Size",
                      value: experiment.parameters?.batch_size,
                      icon: Database,
                      color: "purple",
                    },
                    {
                      label: "Learning Rate",
                      value: experiment.parameters?.learning_rate,
                      icon: Gauge,
                      color: "amber",
                    },
                    {
                      label: "Optimizer",
                      value: experiment.parameters?.optimizer || "Adam",
                      icon: Zap,
                      color: "green",
                    },
                  ].map((param, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
                    >
                      <div className="flex items-center">
                        <div
                          className={`p-2 bg-${param.color}-100 rounded-lg mr-3`}
                        >
                          <param.icon
                            className={`w-4 h-4 text-${param.color}-600`}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {param.label}
                        </span>
                      </div>
                      <span className="text-sm font-semibold text-gray-900">
                        {param.value || "N/A"}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Performance Summary */}
              {stats && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.25 }}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
                    <BarChart3 className="w-5 h-5 mr-2 text-emerald-600" />
                    Performance Summary
                  </h3>
                  <div className="space-y-4">
                    <div className="p-4 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl">
                      <p className="text-xs text-emerald-600 mb-1">
                        Best Accuracy
                      </p>
                      <p className="text-2xl font-bold text-emerald-700">
                        {stats.bestAccuracy?.toFixed(2) || "N/A"}%
                      </p>
                      <div className="flex items-center mt-2 text-xs text-emerald-600">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        <span>Peak performance</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-gray-50 rounded-xl">
                        <p className="text-xs text-gray-500 mb-1">
                          Avg Accuracy
                        </p>
                        <p className="text-lg font-semibold text-gray-900">
                          {stats.avgAccuracy?.toFixed(2) || "N/A"}%
                        </p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-xl">
                        <p className="text-xs text-gray-500 mb-1">Best Loss</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {stats.bestLoss?.toFixed(4) || "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-gray-100">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Total Rounds</span>
                        <span className="font-semibold text-gray-900">
                          {stats.totalRounds}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mt-2">
                        <span className="text-gray-600">Total Records</span>
                        <span className="font-semibold text-gray-900">
                          {stats.totalRecords}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Right Column - Chart and Results */}
            <div className="lg:col-span-2 space-y-6">
              {/* Chart Controls */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <LineChart className="w-5 h-5 mr-2 text-blue-600" />
                    Training Progress
                  </h3>

                  <div className="flex items-center gap-2">
                    <select
                      value={timeRange}
                      onChange={(e) => setTimeRange(e.target.value)}
                      className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="all">All Rounds</option>
                      <option value="10">Last 10 Rounds</option>
                      <option value="20">Last 20 Rounds</option>
                      <option value="50">Last 50 Rounds</option>
                    </select>

                    <button
                      onClick={() =>
                        setViewMode(viewMode === "chart" ? "table" : "chart")
                      }
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {viewMode === "chart" ? (
                        <Table2 className="w-4 h-4" />
                      ) : (
                        <BarChart3 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Chart or Table */}
                {viewMode === "chart" ? (
                  <div className="h-80">
                    {chartData ? (
                      <Line data={chartData} options={chartOptions} />
                    ) : (
                      <div className="h-full flex items-center justify-center">
                        <div className="text-center">
                          <LineChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                          <p className="text-gray-500">
                            No training data available yet
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="pb-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Round
                          </th>
                          <th className="pb-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Client
                          </th>
                          <th className="pb-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Accuracy
                          </th>
                          <th className="pb-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Loss
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {results.slice(0, 10).map((result) => (
                          <tr key={result.id} className="hover:bg-gray-50">
                            <td className="py-3 text-sm font-medium text-gray-900">
                              #{result.round}
                            </td>
                            <td className="py-3 text-sm text-gray-600">
                              Client {result.client_id || "Global"}
                            </td>
                            <td className="py-3 text-right">
                              {result.accuracy !== null ? (
                                <span className="text-sm font-medium text-green-600">
                                  {(result.accuracy * 100).toFixed(2)}%
                                </span>
                              ) : (
                                <span className="text-sm text-gray-400">-</span>
                              )}
                            </td>
                            <td className="py-3 text-right">
                              {result.loss !== null ? (
                                <span className="text-sm font-medium text-red-600">
                                  {result.loss.toFixed(4)}
                                </span>
                              ) : (
                                <span className="text-sm text-gray-400">-</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </motion.div>

              {/* Detailed Results Table */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden"
              >
                <div className="p-6 border-b border-gray-100">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                      <Database className="w-5 h-5 mr-2 text-purple-600" />
                      Detailed Results
                    </h3>
                    <span className="px-3 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded-full">
                      {results.length} records
                    </span>
                  </div>
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
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Accuracy
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Loss
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Timestamp
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {results.slice(0, 20).map((result) => (
                          <tr
                            key={result.id}
                            className="hover:bg-gray-50 transition-colors"
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="font-medium text-gray-900">
                                #{result.round}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-gray-600">
                                Client {result.client_id || "Global"}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              {result.accuracy !== null ? (
                                <span className="inline-flex items-center px-2 py-1 bg-green-50 text-green-700 text-sm font-medium rounded-lg">
                                  {(result.accuracy * 100).toFixed(2)}%
                                </span>
                              ) : (
                                <span className="text-sm text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              {result.loss !== null ? (
                                <span className="inline-flex items-center px-2 py-1 bg-red-50 text-red-700 text-sm font-medium rounded-lg">
                                  {result.loss.toFixed(4)}
                                </span>
                              ) : (
                                <span className="text-sm text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right">
                              <span className="text-sm text-gray-500">
                                {new Date(
                                  result.timestamp,
                                ).toLocaleTimeString()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {results.length > 20 && (
                      <div className="p-4 text-center border-t border-gray-100">
                        <p className="text-sm text-gray-500">
                          Showing first 20 results.{" "}
                          <button className="text-blue-600 hover:text-blue-700 font-medium">
                            View all {results.length} records
                          </button>
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-12 text-center">
                    <div className="bg-gray-50 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                      <Clock className="w-8 h-8 text-gray-400" />
                    </div>
                    <p className="text-gray-600 font-medium mb-1">
                      No results available
                    </p>
                    <p className="text-sm text-gray-500">
                      {experiment.status === "pending"
                        ? "Results will appear once the experiment starts"
                        : experiment.status === "running"
                          ? "Training in progress - results will appear shortly"
                          : "No results recorded for this experiment"}
                    </p>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
