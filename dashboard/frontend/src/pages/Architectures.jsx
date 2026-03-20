import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { architectureService, experimentService } from "../services/api";

import {
  Network,
  Loader2,
  AlertTriangle,
  Code2,
  Info,
  Layers,
  Cpu,
  HardDrive,
  ChevronRight,
  Search,
  Filter,
  Grid3X3,
  LayoutGrid,
  Split,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Eye,
  Download,
  Share2,
  Plus,
  MoreVertical,
  Trash2,
  Copy,
  Edit,
  Check,
  X,
} from "lucide-react";

export default function Architectures() {
  const [architectures, setArchitectures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedArchitecture, setSelectedArchitecture] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionMenuOpen, setActionMenuOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [inUseArchitectures, setInUseArchitectures] = useState(new Set());

  useEffect(() => {
    fetchArchitectures();
  }, []);

  const fetchArchitectures = async () => {
    try {
      setLoading(true);
      const response = await architectureService.getRegistry();
      setArchitectures(response.data);

      // Get architectures in use by experiments
      try {
        const experimentsResponse = await experimentService.getAll()

        const experiments = await experimentsResponse.json();
        const usedArchitectures = new Set(
          experiments.map((exp) => exp.architecture_name),
        );
        setInUseArchitectures(usedArchitectures);
      } catch (err) {
        console.error("Error fetching experiments for usage check:", err);
      }

      // Auto-select first architecture if none selected
      if (response.data.length > 0 && !selectedArchitecture) {
        setSelectedArchitecture(response.data[0]);
      }
      setLoading(false);
    } catch (err) {
      console.error("Error fetching architectures:", err);
      setError("Failed to load architectures. Please try again later.");
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchArchitectures();
    setIsRefreshing(false);
  };

  const performAction = async (actionType) => {
    if (!selectedArchitecture) return;

    setActionLoading(true);
    setActionResult(null);

    try {
      let response;
      const architectureName = selectedArchitecture.name;

      switch (actionType) {
        case "delete":
          response = await architectureService.delete(architectureName);
          setSelectedArchitecture(null);
          break;
        case "duplicate":
          response = await architectureService.duplicate(architectureName);
          break;
        case "edit":
          // Navigate to edit page
          window.location.href = `/architectures/edit/${architectureName}`;
          return;
        default:
          return;
      }

      setActionResult({
        type: "success",
        message: response.message,
      });

      // Refresh architectures list
      await fetchArchitectures();
    } catch (error) {
      console.error(`Error performing ${actionType} action:`, error);
      setActionResult({
        type: "error",
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setActionLoading(false);
      setActionMenuOpen(false);
    }
  };

  const getAvailableActions = () => {
    if (!selectedArchitecture) return [];

    const actions = [
      {
        id: "edit",
        label: "Edit",
        icon: Edit,
        color: "text-blue-600",
        bg: "bg-blue-50",
      },
      {
        id: "duplicate",
        label: "Duplicate",
        icon: Copy,
        color: "text-green-600",
        bg: "bg-green-50",
      },
    ];

    // Only allow delete if not in use
    if (!inUseArchitectures.has(selectedArchitecture.name)) {
      actions.push({
        id: "delete",
        label: "Delete",
        icon: Trash2,
        color: "text-red-600",
        bg: "bg-red-50",
      });
    }

    return actions;
  };

  const getArchitectureTypes = () => {
    const types = ["all", ...new Set(architectures.map((a) => a.model_type))];
    return types;
  };

  const filteredArchitectures = architectures.filter((arch) => {
    const matchesSearch =
      arch.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      arch.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterType === "all" || arch.model_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const item = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 },
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-12 text-center max-w-md">
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
              <Network className="w-16 h-16 text-blue-600 mx-auto" />
            </motion.div>
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full"
            />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Loading Architectures
          </h3>
          <p className="text-gray-500">
            Fetching available model architectures...
          </p>
        </div>
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
            Unable to Load Architectures
          </h3>
          <p className="text-gray-500 mb-6">{error}</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg shadow-blue-600/20"
          >
            <Loader2
              className={`w-4 h-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50">
      {/* Action Result Notification */}
      {actionResult && (
        <div
          className={`fixed top-4 right-4 z-50 bg-${actionResult.type === "success" ? "green" : "red"}-100 border border-${actionResult.type === "success" ? "green" : "red"}-400 text-${actionResult.type === "success" ? "green" : "red"}-700 px-4 py-3 rounded-lg flex items-center`}
        >
          <Check
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

      {/* Action Menu */}
      {actionMenuOpen && selectedArchitecture && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Actions for "{selectedArchitecture.name}"
              </h3>
              <button
                onClick={() => setActionMenuOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3">
              {getAvailableActions().map((action) => (
                <button
                  key={action.id}
                  onClick={() => performAction(action.id)}
                  disabled={actionLoading}
                  className={`w-full flex items-center p-3 rounded-lg ${action.bg} hover:opacity-80 transition-opacity ${actionLoading ? "opacity-50" : ""}`}
                >
                  <action.icon className={`w-5 h-5 ${action.color} mr-3`} />
                  <span className="font-medium text-gray-900">
                    {action.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
                <Network className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Model Architectures
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">
                  Browse and manage neural network architectures
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Loader2
                  className={`w-5 h-5 ${isRefreshing ? "animate-spin" : ""}`}
                />
              </button>
              <button className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm">
                <Plus className="w-4 h-4 mr-2" />
                New Architecture
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Left Panel - Architectures List */}
          <div className="w-96 shrink-0">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden sticky top-24">
              {/* Search and Filters */}
              <div className="p-4 border-b border-gray-100">
                <div className="relative mb-3">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search architectures..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>

                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  <Filter className="w-4 h-4 text-gray-400 shrink-0" />
                  {getArchitectureTypes().map((type) => (
                    <button
                      key={type}
                      onClick={() => setFilterType(type)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
                        filterType === type
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      {type === "all" ? "All Types" : type}
                    </button>
                  ))}
                </div>
              </div>

              {/* Architectures List */}
              <div className="divide-y divide-gray-100 max-h-[90vh] h-full overflow-y-auto">
                <AnimatePresence>
                  {filteredArchitectures.map((arch, index) => (
                    <motion.div
                      key={arch.name}
                      variants={item}
                      initial="hidden"
                      animate="show"
                      transition={{ delay: index * 0.05 }}
                    >
                      <button
                        onClick={() => setSelectedArchitecture(arch)}
                        className={`w-full p-4 text-left transition-all hover:bg-gray-50 ${
                          selectedArchitecture?.name === arch.name
                            ? "bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-600"
                            : ""
                        }`}
                      >
                        <div className="flex items-start">
                          <div
                            className={`p-2 rounded-lg ${
                              selectedArchitecture?.name === arch.name
                                ? "bg-blue-100"
                                : "bg-gray-100"
                            }`}
                          >
                            <Layers
                              className={`w-4 h-4 ${
                                selectedArchitecture?.name === arch.name
                                  ? "text-blue-600"
                                  : "text-gray-500"
                              }`}
                            />
                          </div>
                          <div className="ml-3 flex-1">
                            <div className="flex items-center justify-between">
                              <p
                                className={`font-medium ${
                                  selectedArchitecture?.name === arch.name
                                    ? "text-blue-700"
                                    : "text-gray-900"
                                }`}
                              >
                                {arch.name}
                              </p>
                              <ChevronRight
                                className={`w-4 h-4 ${
                                  selectedArchitecture?.name === arch.name
                                    ? "text-blue-600"
                                    : "text-gray-400"
                                }`}
                              />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {arch.model_type}
                            </p>
                            {arch.compatible_datasets.length > 0 && (
                              <div className="flex items-center mt-2">
                                <HardDrive className="w-3 h-3 text-gray-400 mr-1" />
                                <span className="text-xs text-gray-500">
                                  {arch.compatible_datasets.length} compatible
                                  datasets
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {filteredArchitectures.length === 0 && (
                  <div className="p-8 text-center">
                    <Search className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">
                      No architectures found
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Panel - Architecture Details */}
          <div className="flex-1">
            <AnimatePresence mode="wait">
              {selectedArchitecture ? (
                <motion.div
                  key={selectedArchitecture.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* Architecture Header */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="p-3 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
                          <Network className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h2 className="text-2xl font-bold text-gray-900">
                              {selectedArchitecture.name}
                            </h2>
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                              {selectedArchitecture.model_type}
                            </span>
                            {inUseArchitectures.has(
                              selectedArchitecture.name,
                            ) && (
                              <span className="px-3 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full flex items-center">
                                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full mr-1" />
                                In Use
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600">
                            {selectedArchitecture.description}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                          <Eye className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                          <Download className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                          <Share2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => setActionMenuOpen(true)}
                          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <MoreVertical className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Architecture Visualization */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <Grid3X3 className="w-5 h-5 mr-2 text-blue-600" />
                        Architecture Visualization
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Split className="w-4 h-4" />
                        <span>Interactive 3D View</span>
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-gray-100 to-gray-100 dark:from-gray-900 dark:to-gray-800 rounded-xl p-8 h-80 relative overflow-hidden group">
                      {/* Animated grid background */}
                      <div className="absolute inset-0 opacity-20">
                        <div
                          className="absolute inset-0"
                          style={{
                            backgroundImage:
                              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
                            backgroundSize: "40px 40px",
                          }}
                        />
                      </div>

                      {/* Layer visualization */}
                      <div className="relative h-full flex items-center justify-center">
                        <div className="flex items-center space-x-2">
                          {[1, 2, 3, 4, 5].map((layer, i) => (
                            <motion.div
                              key={layer}
                              initial={{ height: 60 }}
                              animate={{
                                height: [60, 100, 60],
                                opacity: [0.5, 1, 0.5],
                              }}
                              transition={{
                                duration: 3,
                                repeat: Infinity,
                                delay: i * 0.2,
                              }}
                              className="w-16 bg-gradient-to-t from-blue-500 to-indigo-500 rounded-lg"
                              style={{ height: 60 + i * 15 }}
                            />
                          ))}
                        </div>

                        {/* Connection lines */}
                        <svg className="absolute inset-0 w-full h-full pointer-events-none">
                          <motion.path
                            d="M 100 150 Q 200 100, 300 150"
                            stroke="rgba(59, 130, 246, 0.3)"
                            strokeWidth="2"
                            fill="none"
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: 1 }}
                            transition={{ duration: 2, repeat: Infinity }}
                          />
                        </svg>
                      </div>

                      {/* Hover overlay */}
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <button className="px-4 py-2 bg-white text-gray-900 rounded-lg font-medium text-sm">
                          Open in Architecture Studio
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Architecture Details Grid */}
                  <div className="grid grid-cols-3 gap-6">
                    {/* Compatible Datasets */}
                    <div className="col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
                        <HardDrive className="w-5 h-5 mr-2 text-emerald-600" />
                        Compatible Datasets
                      </h3>

                      {selectedArchitecture.compatible_datasets.length > 0 ? (
                        <div className="grid grid-cols-2 gap-3">
                          {selectedArchitecture.compatible_datasets.map(
                            (dataset, index) => (
                              <motion.div
                                key={index}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: index * 0.05 }}
                                className="flex items-center p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
                              >
                                <div className="p-2 bg-emerald-100 rounded-lg mr-3">
                                  <HardDrive className="w-4 h-4 text-emerald-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">
                                    {dataset}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    Medical Imaging
                                  </p>
                                </div>
                                <ArrowRight className="w-4 h-4 text-gray-400 ml-auto" />
                              </motion.div>
                            ),
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center justify-center p-8 bg-gray-50 rounded-xl">
                          <CheckCircle2 className="w-8 h-8 text-green-500 mr-3" />
                          <p className="text-gray-600">
                            Compatible with all datasets
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Architecture Stats */}
                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
                        <Cpu className="w-5 h-5 mr-2 text-purple-600" />
                        Architecture Stats
                      </h3>

                      <div className="space-y-4">
                        {[
                          {
                            label: "Parameters",
                            value: "24.2M",
                            change: "+2.1M",
                          },
                          {
                            label: "Layers",
                            value: "50",
                            change: "ResNet-based",
                          },
                          {
                            label: "Input Size",
                            value: "224x224x3",
                            change: "RGB",
                          },
                          {
                            label: "FLOPs",
                            value: "3.8B",
                            change: "per forward",
                          },
                        ].map((stat, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                          >
                            <div>
                              <p className="text-xs text-gray-500">
                                {stat.label}
                              </p>
                              <p className="text-sm font-semibold text-gray-900">
                                {stat.value}
                              </p>
                            </div>
                            <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              {stat.change}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Configuration Code */}
                  <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <Code2 className="w-5 h-5 mr-2 text-amber-600" />
                        Configuration
                      </h3>
                      <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                        Copy JSON
                      </button>
                    </div>

                    <div className="bg-gray-900 rounded-xl overflow-hidden">
                      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
                        <div className="flex items-center space-x-2">
                          <div className="w-3 h-3 bg-red-500 rounded-full" />
                          <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                          <div className="w-3 h-3 bg-green-500 rounded-full" />
                        </div>
                        <span className="text-xs text-gray-400">
                          architecture.json
                        </span>
                      </div>
                      <pre className="text-sm text-gray-300 p-4 overflow-x-auto">
                        <code>
                          {JSON.stringify(
                            {
                              name: selectedArchitecture.name,
                              type: selectedArchitecture.model_type,
                              compatible_datasets:
                                selectedArchitecture.compatible_datasets,
                              description: selectedArchitecture.description,
                              config: {
                                input_shape: [224, 224, 3],
                                num_classes: 1000,
                                pretrained: true,
                              },
                            },
                            null,
                            2,
                          )}
                        </code>
                      </pre>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-end gap-3">
                    <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium">
                      Export Configuration
                    </button>
                    <button className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all text-sm font-medium shadow-lg shadow-blue-600/20">
                      Use in Experiment
                    </button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center"
                >
                  <div className="bg-gray-50 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
                    <Layers className="w-12 h-12 text-gray-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No Architecture Selected
                  </h3>
                  <p className="text-gray-500 mb-6">
                    Choose an architecture from the list to view its details
                  </p>
                  {architectures.length > 0 && (
                    <button
                      onClick={() => setSelectedArchitecture(architectures[0])}
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all"
                    >
                      Browse Architectures
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </button>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
