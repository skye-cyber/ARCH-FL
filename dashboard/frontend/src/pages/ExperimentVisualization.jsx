import { Link, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Server,
  Database,
  Network,
  Activity,
  RefreshCw,
  Cpu,
  HardDrive,
  Gauge,
  Clock,
  TrendingUp,
  Layers,
  GitBranch,
  Zap,
  CheckCircle2,
  XCircle,
  AlertCircle,
  PlayCircle,
  PauseCircle,
  ArrowLeftRight,
  Radio,
  CircleDot,
  Workflow,
  Users,
  ChevronLeft,
  ChevronRight,
  BarChart3,
} from "lucide-react";
import { useState, useEffect } from "react";
import { experimentService, architectureService, datasetService } from "../services/api";

export default function ExperimentVisualization({}) {
  const { experimentId } = useParams();
  const [experiment, setExperiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeClient, setActiveClient] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [selectedRound, setSelectedRound] = useState(1);

  useEffect(() => {
    const fetchExperiment = async () => {
      try {
        setLoading(true);
        const experimentResponse =
          await experimentService.getById(experimentId);
        const parameters = experimentResponse?.data?.parameters;
        if (parameters && typeof parameters === "string") {
          try {
            const paramObj = JSON.parse(parameters);
            if (paramObj) {
              experimentResponse.data.parameters = paramObj;
            }
          } catch (err) {}
        }
        const archResponse = await architectureService.getByName(
          experimentResponse.data.architecture_name,
        );
        const archConfig = archResponse?.data?.config;
        if (archConfig && typeof archConfig === "string") {
          try {
            const configObj = JSON.parse(archConfig);
            if (configObj) {
              archResponse.data.config = configObj;
            }
            experimentResponse.data.architecture = archResponse.data
            console.log(experimentResponse.data.architecture)

          } catch (err) {}
        }

        setExperiment(experimentResponse.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching experiment:", err);
        setError("Failed to load experiment data");
        setLoading(false);
      }
    };

    if (experimentId) {
      fetchExperiment();
    }
  }, [experimentId]);
  useEffect(() => {
    if (experiment?.status === "running") {
      setIsAnimating(true);
      // Simulate client communication animation
      const interval = setInterval(() => {
        setActiveClient(Math.floor(Math.random() * experiment.num_clients) + 1);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [experiment]);

  if (!experiment) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border-2 border-dashed border-gray-200 p-12 text-center"
      >
        <div className="relative">
          <motion.div
            animate={{
              rotate: [0, 360],
              scale: [1, 1.1, 1],
            }}
            transition={{
              rotate: { duration: 20, repeat: Infinity, ease: "linear" },
              scale: { duration: 3, repeat: Infinity },
            }}
            className="mb-6"
          >
            <Network className="w-16 h-16 text-gray-300 mx-auto" />
          </motion.div>
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute -top-2 -right-2 w-4 h-4 bg-blue-400 rounded-full blur-sm"
          />
        </div>
        <h3 className="text-xl font-semibold text-gray-700 mb-2">
          No Experiment Selected
        </h3>
        <p className="text-gray-500 mb-6">
          Choose an experiment from the list to view its federated learning
          visualization
        </p>
        <Link to="/experiments">
          <div className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm">
            <ArrowLeftRight className="w-4 h-4 mr-2" />
            Select an experiment to begin
          </div>
        </Link>
      </motion.div>
    );
  }

  const getStatusConfig = (status) => {
    switch (status) {
      case "completed":
        return {
          icon: CheckCircle2,
          color: "green",
          bg: "bg-green-50",
          text: "text-green-700",
          border: "border-green-200",
          message: "Training completed successfully",
        };
      case "running":
        return {
          icon: PlayCircle,
          color: "blue",
          bg: "bg-blue-50",
          text: "text-blue-700",
          border: "border-blue-200",
          message: "Federated learning in progress",
        };
      case "failed":
        return {
          icon: XCircle,
          color: "red",
          bg: "bg-red-50",
          text: "text-red-700",
          border: "border-red-200",
          message: "Training failed - check logs",
        };
      default:
        return {
          icon: AlertCircle,
          color: "yellow",
          bg: "bg-yellow-50",
          text: "text-yellow-700",
          border: "border-yellow-200",
          message: "Waiting to start",
        };
    }
  };

  const status = getStatusConfig(experiment.status);
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6">
      {/* Header with status */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
              <Network className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Experiment Visualization
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Real-time federated learning process
              </p>
            </div>
          </div>

          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className={`flex items-center px-4 py-2 ${status.bg} border ${status.border} rounded-xl`}
          >
            <StatusIcon className={`w-5 h-5 ${status.text} mr-2`} />
            <div>
              <p className={`text-sm font-medium ${status.text}`}>
                {experiment.status.charAt(0).toUpperCase() +
                  experiment.status.slice(1)}
              </p>
              <p className="text-xs text-gray-500">{status.message}</p>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Main Visualization */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 overflow-hidden"
      >
        {/* Process Flow */}
        <div className="relative py-8">
          {/* Background gradient line */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-200 via-purple-200 to-emerald-200 -translate-y-1/2" />

          <div className="relative flex items-center justify-between">
            {/* Global Model */}
            <motion.div whileHover={{ scale: 1.05 }} className="relative z-10">
              <div className="text-center">
                <motion.div
                  animate={
                    experiment.status === "running"
                      ? {
                          boxShadow: [
                            "0 0 0 0 rgba(59, 130, 246, 0.4)",
                            "0 0 0 10px rgba(59, 130, 246, 0)",
                          ],
                        }
                      : {}
                  }
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-3 shadow-lg"
                >
                  <Server className="w-8 h-8 text-white" />
                </motion.div>
                <p className="font-semibold text-gray-900">Global Model</p>
                <p className="text-xs text-gray-500 mt-1">Aggregator</p>
                {experiment.status === "running" && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="absolute -top-2 -right-2"
                  >
                    <Radio className="w-4 h-4 text-blue-500" />
                  </motion.div>
                )}
              </div>
            </motion.div>

            {/* Arrows and Clients */}
            <div className="flex-1 flex items-center justify-center space-x-8">
              <motion.div
                animate={
                  experiment.status === "running" ? { x: [0, 10, 0] } : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
              >
                <ArrowLeftRight className="w-6 h-6 text-gray-400" />
              </motion.div>

              {/* Clients Grid */}
              <div className="flex space-x-6">
                {[...Array(Math.min(experiment.num_clients, 4))].map(
                  (_, index) => {
                    const clientNum = index + 1;
                    const isActive =
                      activeClient === clientNum &&
                      experiment.status === "running";

                    return (
                      <motion.div
                        key={clientNum}
                        onHoverStart={() => setActiveClient(clientNum)}
                        onHoverEnd={() => setActiveClient(null)}
                        whileHover={{ y: -5 }}
                        className="relative"
                      >
                        <div className="text-center">
                          <motion.div
                            animate={
                              isActive
                                ? {
                                    scale: [1, 1.1, 1],
                                    boxShadow: [
                                      "0 0 0 0 rgba(16, 185, 129, 0.4)",
                                      "0 0 0 10px rgba(16, 185, 129, 0)",
                                    ],
                                  }
                                : {}
                            }
                            transition={{
                              duration: 1,
                              repeat: isActive ? Infinity : 0,
                            }}
                            className={`w-16 h-16 rounded-xl flex items-center justify-center mb-2 ${
                              isActive
                                ? "bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg"
                                : "bg-gradient-to-br from-gray-100 to-gray-200"
                            }`}
                          >
                            <Database
                              className={`w-6 h-6 ${isActive ? "text-white" : "text-gray-600"}`}
                            />
                          </motion.div>
                          <p
                            className={`text-sm font-medium ${isActive ? "text-green-600" : "text-gray-700"}`}
                          >
                            Client {clientNum}
                          </p>
                          {isActive && (
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="absolute -top-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap bg-gray-900 text-white text-xs px-2 py-1 rounded"
                            >
                              Transmitting
                            </motion.div>
                          )}
                        </div>
                      </motion.div>
                    );
                  },
                )}
                {experiment.num_clients > 4 && (
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mb-2">
                      <span className="text-gray-600 font-bold text-lg">
                        +{experiment.num_clients - 4}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">More</p>
                  </div>
                )}
              </div>

              <motion.div
                animate={
                  experiment.status === "running" ? { x: [0, -10, 0] } : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
              >
                <ArrowLeftRight className="w-6 h-6 text-gray-400" />
              </motion.div>
            </div>

            {/* Updated Model */}
            <motion.div whileHover={{ scale: 1.05 }} className="relative z-10">
              <div className="text-center">
                <motion.div
                  animate={
                    experiment.status === "running"
                      ? {
                          scale: [1, 1.05, 1],
                        }
                      : {}
                  }
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-green-500 rounded-2xl flex items-center justify-center mb-3 shadow-lg"
                >
                  <TrendingUp className="w-8 h-8 text-white" />
                </motion.div>
                <p className="font-semibold text-gray-900">Updated Model</p>
                <p className="text-xs text-gray-500 mt-1">Federated</p>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Communication Lines Animation */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ top: 0, left: 0 }}
        >
          <motion.path
            d="M 150 150 Q 300 100, 450 150"
            stroke="rgba(59, 130, 246, 0.2)"
            strokeWidth="2"
            fill="none"
            strokeDasharray="5,5"
            animate={{
              strokeDashoffset: [0, -10],
              opacity: [0.2, 0.4, 0.2],
            }}
            transition={{ duration: 3, repeat: Infinity }}
          />
        </svg>
      </motion.div>

      {/* Info Grid */}
      <div className="grid grid-cols-4 gap-6">
        {/* Dataset Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2.5 bg-blue-100 rounded-xl">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-xs text-gray-400">Dataset</span>
          </div>
          <p className="text-lg font-semibold text-gray-900 mb-1">
            {experiment.dataset_name}
          </p>
          <p className="text-xs text-gray-500">Medical Imaging</p>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center text-xs text-gray-600">
              <HardDrive className="w-3 h-3 mr-1" />
              <span>2.4 GB</span>
            </div>
          </div>
        </motion.div>

        {/* Architecture Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2.5 bg-purple-100 rounded-xl">
              <Layers className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-xs text-gray-400">Architecture</span>
          </div>
          <p className="text-lg font-semibold text-gray-900 mb-1">
            {experiment.architecture_name}
          </p>
          <p className="text-xs text-gray-500">Neural Network</p>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center text-xs text-gray-600">
              <Cpu className="w-3 h-3 mr-1" />
              <p><span className="text-sky-600 font-semibold">{String(experiment.architecture.config.input_shape)}</span> Input Shape</p>
            </div>
          </div>
        </motion.div>

        {/* Clients Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2.5 bg-green-100 rounded-xl">
              <Users className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-xs text-gray-400">Clients</span>
          </div>
          <p className="text-lg font-semibold text-gray-900 mb-1">
            {experiment.num_clients}
          </p>
          <p className="text-xs text-gray-500">Active Participants</p>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center text-xs text-gray-600">
              <Zap className="w-3 h-3 mr-1" />
              <span>
                {experiment.iid ? "IID Distribution" : "Non-IID Distribution"}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Distribution Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
        >
          <div className="flex items-start justify-between mb-3">
            <div
              className={`p-2.5 rounded-xl ${
                experiment.iid ? "bg-yellow-100" : "bg-orange-100"
              }`}
            >
              <GitBranch
                className={`w-5 h-5 ${
                  experiment.iid ? "text-yellow-600" : "text-orange-600"
                }`}
              />
            </div>
            <span className="text-xs text-gray-400">Distribution</span>
          </div>
          <p className="text-lg font-semibold text-gray-900 mb-1">
            {experiment.iid ? "IID" : "Non-IID"}
          </p>
          <p className="text-xs text-gray-500">Data Distribution</p>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center text-xs text-gray-600">
              <BarChart3 className="w-3 h-3 mr-1" />
              <span>{experiment.iid ? "Uniform" : "Skewed"}</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Training Parameters and Progress */}
      <div className="grid grid-cols-2 gap-6">
        {/* Parameters */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <Gauge className="w-5 h-5 mr-2 text-blue-600" />
            Training Parameters
          </h3>
          <div className="space-y-4">
            {[
              {
                label: "Epochs",
                value: experiment.parameters?.epochs || "N/A",
                icon: Clock,
                color: "blue",
              },
              {
                label: "Batch Size",
                value: experiment.parameters?.batch_size || "N/A",
                icon: Layers,
                color: "purple",
              },
              {
                label: "Learning Rate",
                value: experiment.parameters?.learning_rate || "N/A",
                icon: Zap,
                color: "amber",
              },
              {
                label: "Optimizer",
                value: experiment.parameters?.optimizer || "Adam",
                icon: Cpu,
                color: "green",
              },
            ].map((param, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
              >
                <div className="flex items-center">
                  <div className={`p-2 bg-${param.color}-100 rounded-lg mr-3`}>
                    <param.icon className={`w-4 h-4 text-${param.color}-600`} />
                  </div>
                  <span className="text-sm text-gray-600">{param.label}</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">
                  {param.value}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Progress */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <Activity className="w-5 h-5 mr-2 text-emerald-600" />
            Training Progress
          </h3>

          <div className="space-y-6">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">
                  Round {selectedRound} of {experiment.parameters?.epochs || 10}
                </span>
                <span className="font-medium text-gray-900">
                  {Math.round(
                    (selectedRound / (experiment.parameters?.epochs || 10)) *
                      100,
                  )}
                  %
                </span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: "0%" }}
                  animate={{
                    width: `${(selectedRound / (experiment.parameters?.epochs || 10)) * 100}%`,
                  }}
                  transition={{ duration: 0.5 }}
                  className="h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full"
                />
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  label: "Accuracy",
                  value: "94.2%",
                  change: "+2.3%",
                  color: "green",
                },
                {
                  label: "Loss",
                  value: "0.234",
                  change: "-0.12",
                  color: "blue",
                },
              ].map((metric, idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded-xl">
                  <p className="text-xs text-gray-500 mb-1">{metric.label}</p>
                  <div className="flex items-end justify-between">
                    <p className="text-lg font-bold text-gray-900">
                      {metric.value}
                    </p>
                    <span
                      className={`text-xs text-${metric.color}-600 bg-${metric.color}-50 px-1.5 py-0.5 rounded`}
                    >
                      {metric.change}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Round Selector */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setSelectedRound(Math.max(1, selectedRound - 1))}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex items-center space-x-2">
                {[...Array(5)].map((_, i) => {
                  const round = selectedRound - 2 + i;
                  if (
                    round > 0 &&
                    round <= (experiment.parameters?.epochs || 10)
                  ) {
                    return (
                      <button
                        key={round}
                        onClick={() => setSelectedRound(round)}
                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                          round === selectedRound
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        {round}
                      </button>
                    );
                  }
                  return null;
                })}
              </div>
              <button
                onClick={() =>
                  setSelectedRound(
                    Math.min(
                      experiment.parameters?.epochs || 10,
                      selectedRound + 1,
                    ),
                  )
                }
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Real-time Updates (if running) */}
      {experiment.status === "running" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Radio className="w-6 h-6 mr-3 animate-pulse" />
              <div>
                <p className="font-medium mb-1">Live Updates</p>
                <p className="text-sm text-blue-100">
                  Receiving real-time federated learning metrics
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <CircleDot className="w-3 h-3 text-green-300 mr-2 animate-ping" />
                <span className="text-sm">Active</span>
              </div>
              <button className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors">
                View Details
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
