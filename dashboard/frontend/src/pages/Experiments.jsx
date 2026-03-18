import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  experimentService,
  datasetService,
  architectureService,
} from "../services/api";
import {
  FlaskConical,
  Plus,
  Search,
  Loader2,
  AlertTriangle,
  Play,
  Square,
  Trash2,
  RotateCcw,
  CheckCircle2,
  XCircle,
  MoreVertical,
  ChevronDown,
  Download,
  Share2,
  Eye,
  ListVideoIcon,
  Calendar,
  Clock,
  Database,
  Network,
  Users,
  GitBranch,
  Filter,
  RefreshCw,
} from "lucide-react";

export default function Experiments() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [datasets, setDatasets] = useState([]);
  const [architectures, setArchitectures] = useState([]);
  const [selectedExperiments, setSelectedExperiments] = useState([]);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  const [bulkActionMenuOpen, setBulkActionMenuOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");

  const actionMenuRef = useRef(null);
  const bulkActionMenuRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch experiments
        const experimentsResponse = await experimentService.getAll();
        setExperiments(experimentsResponse.data);

        // Fetch datasets
        const datasetsResponse = await datasetService.getAll();
        setDatasets(datasetsResponse.data);

        // Fetch architectures
        const architecturesResponse = await architectureService.getRegistry();
        setArchitectures(architecturesResponse.data);

        setLoading(false);
      } catch (err) {
        console.error("Error fetching experiments:", err);
        setError("Failed to load experiments. Please try again later.");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        actionMenuRef.current &&
        !actionMenuRef.current.contains(event.target)
      ) {
        setActionMenuOpen(null);
      }
      if (
        bulkActionMenuRef.current &&
        !bulkActionMenuRef.current.contains(event.target)
      ) {
        setBulkActionMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredExperiments = experiments.filter((experiment) => {
    const matchesSearch =
      experiment.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      experiment.dataset_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || experiment.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const toggleExperimentSelection = (experimentId) => {
    setSelectedExperiments((prev) => {
      if (prev.includes(experimentId)) {
        return prev.filter((id) => id !== experimentId);
      } else {
        return [...prev, experimentId];
      }
    });
  };

  const selectAll = () => {
    if (selectedExperiments.length === filteredExperiments.length) {
      setSelectedExperiments([]);
    } else {
      setSelectedExperiments(filteredExperiments.map((exp) => exp.id));
    }
  };

  const getBulkActions = () => {
    if (selectedExperiments.length === 0) return [];

    const selected = experiments.filter((exp) =>
      selectedExperiments.includes(exp.id),
    );
    const hasRunning = selected.some((exp) => exp.status === "running");
    const hasPending = selected.some((exp) => exp.status === "pending");
    const hasCompleted = selected.some((exp) => exp.status === "completed");
    const hasCancelled = selected.some((exp) => exp.status === "cancelled");
    const hasFailed = selected.some((exp) => exp.status === "failed");

    const actions = [];

    if (hasRunning || hasPending) {
      actions.push({
        id: "cancel",
        label: "Cancel Selected",
        icon: Square,
        color: "text-yellow-600",
        hoverColor: "hover:bg-yellow-50",
      });
    }

    if (hasCompleted || hasCancelled || hasFailed) {
      actions.push({
        id: "restart",
        label: "Restart Selected",
        icon: RotateCcw,
        color: "text-blue-600",
        hoverColor: "hover:bg-blue-50",
      });
    }

    if (!hasRunning) {
      actions.push({
        id: "run",
        label: "Run Selected",
        icon: Play,
        color: "text-green-600",
        hoverColor: "hover:bg-green-50",
      });
      actions.push({
        id: "delete",
        label: "Delete Selected",
        icon: Trash2,
        color: "text-red-600",
        hoverColor: "hover:bg-red-50",
      });
    }

    return actions;
  };

  const getSingleActions = (experiment) => {
    const actions = [
      {
        id: "view",
        label: "View Details",
        icon: Eye,
        color: "text-blue-600",
        hoverColor: "hover:bg-blue-50",
        link: `/experiments/${experiment.id}`,
      },
      {
        id: "Monitor",
        label: "Live Monitor",
        icon: ListVideoIcon,
        color: "text-green-500",
        hoverColor: "hover:bg:green-700",
        link: `/livemonitor/${experiment.id}`,
      },
    ];

    if (experiment.status === "pending") {
      actions.push({
        id: "run",
        label: "Run Experiment",
        icon: Play,
        color: "text-green-600",
        hoverColor: "hover:bg-green-50",
      });
    }
    if (experiment.status === "running") {
      actions.push({
        id: "cancel",
        label: "Cancel Experiment",
        icon: Square,
        color: "text-yellow-600",
        hoverColor: "hover:bg-yellow-50",
      });
    }
    if (["completed", "cancelled", "failed"].includes(experiment.status)) {
      actions.push({
        id: "restart",
        label: "Restart Experiment",
        icon: RotateCcw,
        color: "text-blue-600",
        hoverColor: "hover:bg-blue-50",
      });
    }
    if (experiment.status !== "running") {
      actions.push({
        id: "delete",
        label: "Delete Experiment",
        icon: Trash2,
        color: "text-red-600",
        hoverColor: "hover:bg-red-50",
      });
    }

    actions.push(
      {
        id: "export",
        label: "Export Results",
        icon: Download,
        color: "text-purple-600",
        hoverColor: "hover:bg-purple-50",
      },
      {
        id: "share",
        label: "Share",
        icon: Share2,
        color: "text-indigo-600",
        hoverColor: "hover:bg-indigo-50",
      },
    );

    return actions;
  };

  const performBulkAction = async (action) => {
    setActionLoading(true);
    setActionResult(null);

    try {
      const response = await experimentService.batchActions({
        action: action.id,
        experiment_ids: selectedExperiments,
      });

      setActionResult({
        type: "success",
        message: `${action.label} completed successfully on ${response.successful} experiment(s)`,
      });

      // Refresh experiments list
      const experimentsResponse = await experimentService.getAll();
      setExperiments(experimentsResponse.data);
      setSelectedExperiments([]);
    } catch (error) {
      console.error(`Error performing ${action.id} action:`, error);
      setActionResult({
        type: "error",
        message: `Failed to perform ${action.label}`,
      });
    } finally {
      setActionLoading(false);
      setBulkActionMenuOpen(false);
    }
  };

  const performSingleAction = async (experimentId, actionType) => {
    setActionLoading(true);
    try {
      let response;
      switch (actionType) {
        case "run":
          response = await experimentService.run(experimentId);
          break;
        case "cancel":
          response = await experimentService.cancel(experimentId);
          break;
        case "delete":
          response = await experimentService.delete(experimentId);
          break;
        case "restart":
          response = await experimentService.restart(experimentId);
          break;
        default:
          return;
      }

      setActionResult({
        type: "success",
        message: `Experiment ${actionType} completed successfully`,
      });

      // Refresh experiments list
      const experimentsResponse = await experimentService.getAll();
      setExperiments(experimentsResponse.data);
      setActionMenuOpen(null);
    } catch (error) {
      console.error(`Error performing ${actionType} action:`, error);
      setActionResult({
        type: "error",
        message: `Failed to ${actionType} experiment`,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: {
        bg: "bg-yellow-50",
        text: "text-yellow-700",
        dot: "bg-yellow-400",
        label: "Pending",
      },
      running: {
        bg: "bg-blue-50",
        text: "text-blue-700",
        dot: "bg-blue-400",
        label: "Running",
      },
      completed: {
        bg: "bg-green-50",
        text: "text-green-700",
        dot: "bg-green-400",
        label: "Completed",
      },
      failed: {
        bg: "bg-red-50",
        text: "text-red-700",
        dot: "bg-red-400",
        label: "Failed",
      },
      cancelled: {
        bg: "bg-gray-50",
        text: "text-gray-700",
        dot: "bg-gray-400",
        label: "Cancelled",
      },
    };

    const style = config[status] || config.pending;

    return (
      <span
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${style.dot} mr-1.5`}></span>
        {style.label}
      </span>
    );
  };

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
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
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
            Loading Experiments
          </h3>
          <p className="text-gray-500">
            Fetching your federated learning experiments...
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
            Unable to Load Experiments
          </h3>
          <p className="text-gray-500 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-600/20"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
                <FlaskConical className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Experiments
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">
                  Manage and monitor your federated learning experiments
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {selectedExperiments.length > 0 && (
                <div className="relative" ref={bulkActionMenuRef}>
                  <button
                    onClick={() => setBulkActionMenuOpen(!bulkActionMenuOpen)}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-all shadow-sm"
                  >
                    <span>Actions</span>
                    <span className="ml-2 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {selectedExperiments.length}
                    </span>
                    <ChevronDown className="w-4 h-4 ml-2" />
                  </button>

                  <AnimatePresence>
                    {bulkActionMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-100 py-1 z-50"
                      >
                        {getBulkActions().map((action) => (
                          <button
                            key={action.id}
                            onClick={() => performBulkAction(action)}
                            disabled={actionLoading}
                            className={`w-full flex items-center px-4 py-2.5 text-sm ${action.color} ${action.hoverColor} transition-colors disabled:opacity-50`}
                          >
                            <action.icon className="w-4 h-4 mr-3" />
                            {action.label}
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              <Link
                to="/experiments/new"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium rounded-xl hover:from-green-700 hover:to-emerald-700 transition-all shadow-sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Experiment
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search experiments by name or dataset..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {filteredExperiments.length > 0 && (
              <button
                onClick={selectAll}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium px-3 py-2"
              >
                {selectedExperiments.length === filteredExperiments.length
                  ? "Deselect All"
                  : "Select All"}
              </button>
            )}
          </div>
        </div>

        {/* Action Result Notification */}
        <AnimatePresence>
          {actionResult && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`mb-6 p-4 rounded-xl flex items-center ${
                actionResult.type === "success"
                  ? "bg-green-50 border border-green-200"
                  : "bg-red-50 border border-red-200"
              }`}
            >
              {actionResult.type === "success" ? (
                <CheckCircle2 className="w-5 h-5 text-green-600 mr-3" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mr-3" />
              )}
              <p
                className={`text-sm ${
                  actionResult.type === "success"
                    ? "text-green-700"
                    : "text-red-700"
                }`}
              >
                {actionResult.message}
              </p>
              <button
                onClick={() => setActionResult(null)}
                className="ml-auto text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Experiments Table */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {filteredExperiments.length === 0 ? (
            <div className="p-12 text-center">
              <div className="bg-gray-50 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                <FlaskConical className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">
                No experiments found
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                {searchTerm
                  ? "Try adjusting your search or filters"
                  : "Get started by creating your first federated learning experiment"}
              </p>
              {!searchTerm && (
                <Link
                  to="/experiments/new"
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Experiment
                </Link>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                      <input
                        type="checkbox"
                        checked={
                          selectedExperiments.length ===
                          filteredExperiments.length
                        }
                        onChange={selectAll}
                        className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Dataset
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Architecture
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Clients
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredExperiments.map((experiment) => (
                    <motion.tr
                      key={experiment.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-4 py-4 whitespace-nowrap w-12">
                        <input
                          type="checkbox"
                          checked={selectedExperiments.includes(experiment.id)}
                          onChange={() =>
                            toggleExperimentSelection(experiment.id)
                          }
                          className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          to={`/experiments/${experiment.id}`}
                          className="flex items-center group"
                        >
                          <div className="p-1.5 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors mr-3">
                            <FlaskConical className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                              {experiment.name}
                            </p>
                            <p className="text-xs text-gray-500">
                              ID: {experiment.id} {/*.slice(0, 8)}...*/}
                            </p>
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Database className="w-4 h-4 text-gray-400 mr-2" />
                          <div>
                            <p className="text-sm text-gray-900">
                              {experiment.dataset_name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {datasets.find(
                                (d) => d.name === experiment.dataset_name,
                              )?.type || "Medical Imaging"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Network className="w-4 h-4 text-gray-400 mr-2" />
                          <div>
                            <p className="text-sm text-gray-900">
                              {experiment.architecture_name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {architectures.find(
                                (a) => a.name === experiment.architecture_name,
                              )?.model_type || "Neural Network"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 text-gray-400 mr-2" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {experiment.num_clients}
                            </p>
                            <p className="text-xs text-gray-500">
                              {experiment.iid ? "IID" : "Non-IID"}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(experiment.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                          <div>
                            <p className="text-sm text-gray-900">
                              {new Date(
                                experiment.created_at,
                              ).toLocaleDateString()}
                            </p>
                            <p className="text-xs text-gray-500">
                              <Clock className="w-3 h-3 inline mr-1" />
                              {new Date(
                                experiment.created_at,
                              ).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="relative" ref={actionMenuRef}>
                          <button
                            onClick={() =>
                              setActionMenuOpen(
                                actionMenuOpen === experiment.id
                                  ? null
                                  : experiment.id,
                              )
                            }
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <AnimatePresence>
            {actionMenuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="absolute right-0 -bottom-32 mt-1 w-48 bg-white rounded-xl shadow-xl border border-gray-100 py-1 z-[30]"
              >
                {getSingleActions(
                  experiments.filter((exp) => exp.id === actionMenuOpen)[0],
                ).map((action) =>
                  action.link ? (
                    <Link
                      key={action.id}
                      to={action.link}
                      className={`flex items-center px-4 py-2.5 text-sm ${action.color} ${action.hoverColor} transition-colors`}
                      onClick={() => setActionMenuOpen(null)}
                    >
                      <action.icon className="w-4 h-4 mr-3" />
                      {action.label}
                    </Link>
                  ) : (
                    <button
                      key={action.id}
                      onClick={() =>
                        performSingleAction(actionMenuOpen, action.id)
                      }
                      disabled={actionLoading}
                      className={`w-full flex items-center px-4 py-2.5 text-sm ${action.color} ${action.hoverColor} transition-colors disabled:opacity-50`}
                    >
                      <action.icon className="w-4 h-4 mr-3" />
                      {action.label}
                    </button>
                  ),
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Summary Footer */}
        {filteredExperiments.length > 0 && (
          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <div>
              Showing {filteredExperiments.length} of {experiments.length}{" "}
              experiments
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-1"></span>
                Completed:{" "}
                {experiments.filter((e) => e.status === "completed").length}
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-1"></span>
                Running:{" "}
                {experiments.filter((e) => e.status === "running").length}
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-yellow-400 rounded-full mr-1"></span>
                Pending:{" "}
                {experiments.filter((e) => e.status === "pending").length}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
