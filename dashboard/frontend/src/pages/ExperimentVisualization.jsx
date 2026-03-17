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
  Wifi,
  WifiOff,
} from "lucide-react";
import { useState, useEffect } from "react";
import {
  experimentService,
  architectureService,
  datasetService,
} from "../services/api";
// import { useWebSocket } from "../hooks/useWebSocket";
// import { WebSocketMessageType } from "../types/websocket";
import { useExperimentPolling } from "../hooks/useExperimentPolling";

export default function ExperimentVisualization() {
  const { experimentId } = useParams();
  const [experiment, setExperiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeClient, setActiveClient] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [selectedRound, setSelectedRound] = useState(1);

  // Real-time metrics state
  const [liveMetrics, setLiveMetrics] = useState({
    accuracy: null,
    loss: null,
    currentRound: null,
    clientUpdates: [],
    roundMetrics: {},
  });

  /*
  // WebSocket integration
  //   const {
  //     isConnected,
  //     lastMessage,
  //     error: wsError,
  //     sendMessage,
  //     connectionStats,
  //   } = useWebSocket(experimentId, {
  //     onConnect: () => {
  //       console.log("Connected to real-time updates");
  //     },
  //     onDisconnect: () => {
  //       console.log("Disconnected from real-time updates");
  //     },
  //     onMessage: (message) => {
  //       handleWebSocketMessage(message);
  //     },
  //   });

  // Handle incoming WebSocket messages
    const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case WebSocketMessageType.ROUND_COMPLETED:
        setLiveMetrics((prev) => ({
          ...prev,
          currentRound: message.round,
          roundMetrics: {
            ...prev.roundMetrics,
            [message.round]: {
              accuracy: message.accuracy,
              loss: message.loss,
              timestamp: message.timestamp,
            },
          },
        }));
        setSelectedRound(message.round);
        break;

      case WebSocketMessageType.METRICS_UPDATE:
        setLiveMetrics((prev) => ({
          ...prev,
          accuracy: message.accuracy,
          loss: message.loss,
        }));
        break;

      case WebSocketMessageType.CLIENT_UPDATE:
        setLiveMetrics((prev) => ({
          ...prev,
          clientUpdates: [
            ...prev.clientUpdates.slice(-9), // Keep last 10 updates
            {
              clientId: message.client_id,
              round: message.round,
              accuracy: message.accuracy,
              loss: message.loss,
              timestamp: message.timestamp,
            },
          ],
        }));

        // Animate active client
        setActiveClient(message.client_id);
        setTimeout(() => setActiveClient(null), 2000);
        break;

      case WebSocketMessageType.EXPERIMENT_COMPLETED:
        setExperiment((prev) => ({
          ...prev,
          status: "completed",
        }));
        break;

      case WebSocketMessageType.EXPERIMENT_FAILED:
        setExperiment((prev) => ({
          ...prev,
          status: "failed",
        }));
        break;

      case WebSocketMessageType.PROGRESS_UPDATE:
        // Update progress if needed
        break;

      default:
        console.log("Unhandled message type:", message.type);
    }
  };
*/
  // Use polling for real-time updates
  const {
    data: progressData,
    loading: pollingLoading,
    error: pollingError,
    isPolling,
  } = useExperimentPolling(experimentId, {
    interval: 2000, // Poll every 2 seconds
    enabled: experiment?.status === "running",
    onProgressUpdate: (data) => {
      // Update live metrics
      if (data.metrics) {
        setLiveMetrics({
          accuracy: data.metrics.latest_accuracy,
          loss: data.metrics.latest_loss,
          currentRound: data.progress.current_round,
        });
      }
      console.log("Polling", data);

      // Update client activity
      if (data.clients?.details) {
        // Find recently active clients
        const activeClients = Object.entries(data.clients.details)
          .filter(
            ([_, stats]) => stats.last_round === data.progress.completed_rounds,
          )
          .map(([id]) => parseInt(id));

        if (activeClients.length > 0) {
          setActiveClient(activeClients[0]);
          setTimeout(() => setActiveClient(null), 1500);
        }
      }
    },
    onComplete: (data) => {
      // Handle experiment completion
      setExperiment((prev) => ({
        ...prev,
        status: "completed",
      }));
    },
  });
  console.log(progressData);
  // Fetch initial experiment data
  useEffect(() => {
    const fetchExperiment = async () => {
      try {
        setLoading(true);
        const experimentResponse =
          await experimentService.getById(experimentId);

        // Parse parameters
        const parameters = experimentResponse?.data?.parameters;
        if (parameters && typeof parameters === "string") {
          try {
            const paramObj = JSON.parse(parameters);
            if (paramObj) {
              experimentResponse.data.parameters = paramObj;
            }
          } catch (err) {}
        }

        // Fetch architecture
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
            experimentResponse.data.architecture = archResponse.data;
          } catch (err) {}
        }

        // Fetch dataset
        if (experimentResponse.data.dataset_name) {
          const datasetResponse = await datasetService.getByName(
            experimentResponse.data.dataset_name,
          );
          const metadataInfo = datasetResponse?.data?.metadata;
          if (metadataInfo && typeof metadataInfo === "string") {
            try {
              const metadataObj = JSON.parse(metadataInfo);
              if (metadataObj) {
                datasetResponse.data.metadata = metadataObj;
              }
              experimentResponse.data.datasetInfo = datasetResponse.data;
            } catch (err) {}
          }
        }

        setExperiment(experimentResponse.data);

        // Set initial selected round
        if (experimentResponse.data.parameters?.epochs) {
          setSelectedRound(1);
        }

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

  // Connection status indicator (using polling instead of WebSocket)
  const ConnectionStatus = () => (
    <div
      className={`flex items-center px-3 py-1.5 rounded-lg ${
        isPolling ? "bg-green-50" : "bg-yellow-50"
      }`}
    >
      <div
        className={`w-2 h-2 rounded-full mr-2 ${
          isPolling ? "bg-green-500 animate-pulse" : "bg-yellow-500"
        }`}
      />
      <span
        className={`text-xs font-medium ${
          isPolling ? "text-green-700" : "text-yellow-700"
        }`}
      >
        {isPolling ? "Live Updates" : "Polling Stopped"}
      </span>
    </div>
  );
  // Update animation based on connection status and experiment state
  useEffect(() => {
    if (experiment?.status === "running") {
      setIsAnimating(true);
    } else {
      setIsAnimating(false);
    }
  }, [experiment?.status]);

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

  // Get current metrics (live or from experiment data)
  const currentAccuracy =
    liveMetrics.accuracy || experiment.metrics?.final_accuracy || 0;
  const currentLoss = liveMetrics.loss || experiment.metrics?.final_loss || 0;
  const currentRound = liveMetrics.currentRound || selectedRound;

  return (
    <div className="space-y-6">
      {/* Connection Status Bar (new) */}
      {/*experiment.status === "running" && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex items-center justify-between px-4 py-2 rounded-lg ${
            isConnected
              ? "bg-green-50 border border-green-200"
              : "bg-yellow-50 border border-yellow-200"
          }`}
        >
          <div className="flex items-center">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-600 mr-2" />
                <span className="text-sm text-green-700">
                  Live updates active
                </span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-yellow-600 mr-2" />
                <span className="text-sm text-yellow-700">
                  Connecting to live updates...
                </span>
              </>
            )}
          </div>
          {5 > connectionStats.reconnectAttempts > 0 && (
            <span className="text-xs text-gray-500">
              Reconnect attempt {connectionStats.reconnectAttempts}/5
            </span>
          )}
        </motion.div>
      )*/}

      {/* Header with status */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl">
              <Network className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Experiment Visualization
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {experiment?.status === "running"
                  ? `Round ${progressData?.progress?.current_round || 1} of ${progressData?.progress?.total_rounds || 10}`
                  : "Federated learning process"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ConnectionStatus />
            {/* Rest of your status component */}
          </div>
        </div>
      </div>

      {/* Main Visualization */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 overflow-hidden"
      >
        {/* Process Flow - Keep existing visualization but enhance with live updates */}
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

              {/* Clients Grid with Live Updates */}
              <div className="flex space-x-6">
                {[...Array(Math.min(experiment.num_clients, 4))].map(
                  (_, index) => {
                    const clientNum = index + 1;
                    const isActive =
                      (activeClient === clientNum ||
                        liveMetrics.clientUpdates.some(
                          (update) =>
                            update.clientId === clientNum &&
                            Date.now() - new Date(update.timestamp).getTime() <
                              3000,
                        )) &&
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
                              className={`w-6 h-6 ${
                                isActive ? "text-white" : "text-gray-600"
                              }`}
                            />
                          </motion.div>
                          <p
                            className={`text-sm font-medium ${
                              isActive ? "text-green-600" : "text-gray-700"
                            }`}
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
      </motion.div>

      {/* Info Grid - Keep existing but enhance with live metrics */}
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
              <div className="flex gap-4">
                <div>{experiment.datasetInfo.size.human}</div>{" "}
                <div>{experiment.datasetInfo.metadata.num_classes} classes</div>
              </div>
            </div>
          </div>
        </motion.div>{" "}
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
              <p>
                <span className="text-sky-600 font-semibold">
                  {String(experiment.architecture.config.input_shape)}
                </span>{" "}
                Input Shape
              </p>
            </div>
          </div>
        </motion.div>
        {/* Clients Card with Live Counter */}
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
            <div className="flex items-center justify-between text-xs text-gray-600">
              <div className="flex items-center">
                <Zap className="w-3 h-3 mr-1" />
                <span>{experiment.iid ? "IID" : "Non-IID"}</span>
              </div>
              {experiment.status === "running" && (
                <motion.span
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-green-600"
                >
                  {liveMetrics.clientUpdates.length} active
                </motion.span>
              )}
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

      {/* Training Parameters and Progress with Live Metrics */}
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

        {/* Progress with Live Metrics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <Activity className="w-5 h-5 mr-2 text-emerald-600" />
            Training Progress
            {experiment.status === "running" && (
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="ml-2 text-xs font-normal text-green-600"
              >
                ● LIVE
              </motion.span>
            )}
          </h3>

          <div className="space-y-6">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">
                  Round {currentRound} of {experiment.parameters?.epochs || 10}
                </span>
                <span className="font-medium text-gray-900">
                  {Math.round(
                    (currentRound / (experiment.parameters?.epochs || 10)) *
                      100,
                  )}
                  %
                </span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: "0%" }}
                  animate={{
                    width: `${(currentRound / (experiment.parameters?.epochs || 10)) * 100}%`,
                  }}
                  transition={{ duration: 0.5 }}
                  className="h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full"
                />
              </div>
            </div>

            {/* Live Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <motion.div
                key={`accuracy-${currentAccuracy}`}
                initial={{ scale: 1 }}
                animate={liveMetrics.accuracy ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.3 }}
                className="p-3 bg-gray-50 rounded-xl"
              >
                <p className="text-xs text-gray-500 mb-1">Accuracy</p>
                <div className="flex items-end justify-between">
                  <p className="text-lg font-bold text-gray-900">
                    {currentAccuracy
                      ? (currentAccuracy * 100).toFixed(2)
                      : "0.00"}
                    %
                  </p>
                  {liveMetrics.accuracy && (
                    <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
                      +
                      {(
                        liveMetrics.accuracy * 100 -
                        (experiment.metrics?.final_accuracy || 0) * 100
                      ).toFixed(2)}
                      %
                    </span>
                  )}
                </div>
              </motion.div>

              <motion.div
                key={`loss-${currentLoss}`}
                initial={{ scale: 1 }}
                animate={liveMetrics.loss ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.3 }}
                className="p-3 bg-gray-50 rounded-xl"
              >
                <p className="text-xs text-gray-500 mb-1">Loss</p>
                <div className="flex items-end justify-between">
                  <p className="text-lg font-bold text-gray-900">
                    {currentLoss ? currentLoss.toFixed(4) : "0.0000"}
                  </p>
                  {liveMetrics.loss && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                      {(
                        currentLoss - (experiment.metrics?.final_loss || 0)
                      ).toFixed(4)}
                    </span>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Recent Client Updates */}
            {liveMetrics.clientUpdates.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-4 p-3 bg-gray-50 rounded-xl"
              >
                <p className="text-xs font-medium text-gray-600 mb-2">
                  Recent Client Updates
                </p>
                <div className="space-y-2">
                  {liveMetrics.clientUpdates.slice(-3).map((update, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-gray-500">
                        Client {update.clientId} (Round {update.round})
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-green-600">
                          {(update.accuracy * 100).toFixed(2)}%
                        </span>
                        <span className="text-red-600">
                          {update.loss.toFixed(4)}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Round Selector */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setSelectedRound(Math.max(1, currentRound - 1))}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex items-center space-x-2">
                {[...Array(5)].map((_, i) => {
                  const round = currentRound - 2 + i;
                  if (
                    round > 0 &&
                    round <= (experiment.parameters?.epochs || 10)
                  ) {
                    return (
                      <button
                        key={round}
                        onClick={() => setSelectedRound(round)}
                        className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                          round === currentRound
                            ? "bg-blue-600 text-white"
                            : round === selectedRound
                              ? "bg-blue-100 text-blue-600"
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
                      currentRound + 1,
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

      {/* Live Client Activity Feed */}
      {experiment.status === "running" &&
        isConnected &&
        liveMetrics.clientUpdates.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <Radio className="w-5 h-5 mr-2 text-purple-600" />
              Live Client Activity
            </h3>
            <div className="grid grid-cols-4 gap-4">
              {liveMetrics.clientUpdates.slice(-4).map((update, idx) => (
                <motion.div
                  key={idx}
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border border-purple-100"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-purple-700">
                      Client {update.clientId}
                    </span>
                    <span className="text-xs text-gray-500">
                      Round {update.round}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Accuracy:</span>
                      <span className="font-medium text-green-600">
                        {(update.accuracy * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Loss:</span>
                      <span className="font-medium text-red-600">
                        {update.loss.toFixed(4)}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
    </div>
  );
}
