import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    experimentService,
    datasetService,
    architectureService,
} from "../services/api";
import {
    FaFlask,
    FaPlus,
    FaSpinner,
    FaExclamationTriangle,
    FaChevronRight,
    FaInfoCircle,
} from "react-icons/fa";

export default function ExperimentCreate() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [datasets, setDatasets] = useState([]);
    const [architectures, setArchitectures] = useState([]);

    const [experiment, setExperiment] = useState({
        name: "",
        description: "",
        dataset_name: "",
        architecture_name: "",
        num_clients: 5,
        iid: true,
        dp_enabled: false,
        epsilon: null,
        delta: null,
        sensitivity: null,
        noise_scale: null,
        noise_mechanism: null,
        max_grad_norm: null,
        parameters: {
            epochs: 10,
            batch_size: 32,
            learning_rate: 0.001,
        },
    });

    const noise_mechanism = [
        { name: "gaussian", description: "Gaussian Noise Mechanism" },
        { name: "laplace", description: "Laplace Noise Mechanism" }
    ]
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                // Fetch datasets
                const datasetsResponse = await datasetService.getAll();
                setDatasets(datasetsResponse.data);

                // Fetch architectures
                const architecturesResponse = await architectureService.getRegistry();
                setArchitectures(architecturesResponse.data);

                setLoading(false);
            } catch (err) {
                console.error("Error fetching data:", err);
                setError("Failed to load data. Please try again later.");
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        if (name.startsWith("parameters.")) {
            const paramName = name.split(".")[1];
            setExperiment((prev) => ({
                ...prev,
                parameters: {
                    ...prev.parameters,
                    [paramName]:
                        type === "checkbox"
                            ? checked
                            : type === "radio"
                                ? value === "on"
                                : value,
                },
            }));
        } else {
            setExperiment((prev) => ({
                ...prev,
                [name]:
                    type === "checkbox"
                        ? checked
                        : type === "radio"
                            ? value === "on"
                            : value,
            }));
            console.log(experiment.iid);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await experimentService.create(experiment);
            console.log("Experiment created:", response.data);

            // Navigate to the new experiment
            navigate(`/experiments/${response.data.id}`);
        } catch (err) {
            console.error("Error creating experiment:", err);
            setError(
                "Failed to create experiment. Please check your inputs and try again.",
            );
        }
    };

    const getCompatibleArchitectures = () => {
        if (!experiment.dataset_name) return architectures;

        return architectures.filter(
            (arch) =>
                arch.compatible_datasets.length === 0 ||
                arch.compatible_datasets.includes(
                    experiment.dataset_name.toLowerCase(),
                ),
        );
    };

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow p-6 text-center">
                <FaSpinner className="animate-spin text-blue-600 text-2xl mx-auto mb-4" />
                <p className="text-gray-600">Loading data...</p>
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

    return (
        <section className="lg:container mx-auto w-full justify-center">
            <div className="space-y-4">
                {/* Page header */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                        <FaFlask className="text-blue-600 mr-2" />
                        Create New Experiment
                    </h2>
                    <p className="text-gray-600 mt-2">
                        Configure your federated learning experiment
                    </p>
                </div>

                <div className="flex flex-cols lg:flex-row gap-1 md:gap-4 w-full">
                    {/*Side panel*/}
                    <div className="hidden md:block w-[24%] lg:w-[20%] bg-white min-h-full rounded-md shadow-md p-4">
                        <h2 className="text-center text-gray-700 font-bold text-xl mb-6 flex items-center justify-center gap-2">
                            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                            Steps
                            <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                        </h2>

                        <div className="space-y-4">
                            {/* Step 1 - Basic Info */}
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-300"></div>
                                <div className="relative flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-100 hover:border-transparent transition-all duration-300 cursor-pointer">
                                    <div className="size-10 md:size-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                        <svg
                                            className="w-4 h-4 md:w-5 md:h-5 text-white"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth="2"
                                                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                            ></path>
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-400">Step 1</p>
                                        <p className="text-base font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent whitespace-nowrap truncate">
                                            Basic Info
                                        </p>
                                    </div>
                                    <div
                                        className={`w-2 h-2 rounded-full ${step === 1 ? "bg-green-400 animate-pulse" : "bg-gray-300"}`}
                                    ></div>
                                </div>
                            </div>

                            {/* Step 2 - Configuration */}
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-300"></div>
                                <div className="relative flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-100 hover:border-transparent transition-all duration-300 cursor-pointer">
                                    <div className="size-10 md:size-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                        <svg
                                            className="w-4 h-4 md:w-5 md:h-5 text-white"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth="2"
                                                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                                            ></path>
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth="2"
                                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                            ></path>
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-400">Step 2</p>
                                        <p className="text-base font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                                            <span className="flex">
                                                Config<span className="hidden lg:flex">uration</span>
                                            </span>
                                        </p>
                                    </div>
                                    <div
                                        className={`w-2 h-2 rounded-full ${step === 2 ? "bg-green-400 animate-pulse" : "bg-gray-300"}`}
                                    ></div>
                                </div>
                            </div>

                            {/* Step 3 - Review */}
                            <div className="relative group">
                                <div className="absolute -inset-1 bg-gradient-to-r from-amber-600 to-orange-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-300"></div>
                                <div className="relative flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-100 hover:border-transparent transition-all duration-300 cursor-pointer">
                                    <div className="size-10 md:size-8 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                        <svg
                                            className="size-4 md:size-5 text-white"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth="2"
                                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                            ></path>
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-400">Step 3</p>
                                        <p className="text-base font-bold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">
                                            Review
                                        </p>
                                    </div>
                                    <div
                                        className={`w-2 h-2 rounded-full ${step === 3 ? "bg-green-400 animate-pulse" : "bg-gray-300"}`}
                                    ></div>
                                </div>
                            </div>
                        </div>

                        {/* Progress Indicator */}
                        <div className="mt-8 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium text-gray-600">
                                    Overall Progress
                                </span>
                                <span className="text-sm font-bold text-blue-600">
                                    {Math.floor((step / 3) * 100)}%
                                </span>
                            </div>
                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    style={{ width: `${Math.floor((step / 3) * 100)}%` }}
                                    className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full animate-pulse"
                                ></div>
                            </div>
                        </div>
                    </div>
                    <div className="flex-1 space-y-4 w-full max-w-full">
                        {/* Progress steps */}
                        <div className="w-full max-w-full lg:max-w-7xl bg-white rounded-lg shadow p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                    <div
                                        className={`flex items-center justify-center w-8 h-8 rounded-full ${step >= 1 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"}`}
                                    >
                                        <span className="text-sm font-medium">1</span>
                                    </div>
                                    <span
                                        className={`ml-3 text-sm font-medium ${step >= 1 ? "text-blue-600" : "text-gray-500"}`}
                                    >
                                        Basic Info
                                    </span>
                                </div>
                                <FaChevronRight className="text-gray-300" />
                                <div className="flex items-center">
                                    <div
                                        className={`flex items-center justify-center w-8 h-8 rounded-full ${step >= 2 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"}`}
                                    >
                                        <span className="text-sm font-medium">2</span>
                                    </div>
                                    <span
                                        className={`ml-3 text-sm font-medium ${step >= 2 ? "text-blue-600" : "text-gray-500"}`}
                                    >
                                        Configuration
                                    </span>
                                </div>
                                <FaChevronRight className="text-gray-300" />
                                <div className="flex items-center">
                                    <div
                                        className={`flex items-center justify-center w-8 h-8 rounded-full ${step >= 3 ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"}`}
                                    >
                                        <span className="text-sm font-medium">3</span>
                                    </div>
                                    <span
                                        className={`ml-3 text-sm font-medium ${step >= 3 ? "text-blue-600" : "text-gray-500"}`}
                                    >
                                        Review
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Step 1: Basic Info */}
                        {step === 1 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                                    Basic Information
                                </h3>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Experiment Name*
                                        </label>
                                        <input
                                            type="text"
                                            name="name"
                                            value={experiment.name}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            placeholder="e.g., PneumoniaMNIST Baseline"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Description
                                        </label>
                                        <textarea
                                            name="description"
                                            value={experiment.description}
                                            onChange={handleChange}
                                            rows="3"
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            placeholder="Brief description of this experiment"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Dataset*
                                        </label>
                                        <select
                                            name="dataset_name"
                                            value={experiment.dataset_name}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        >
                                            <option value="">Select a dataset</option>
                                            {datasets.map((dataset) => (
                                                <option key={dataset.name} value={dataset.name}>
                                                    {dataset.description} ({dataset.name})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Model Architecture*
                                        </label>
                                        <select
                                            name="architecture_name"
                                            value={experiment.architecture_name}
                                            onChange={handleChange}
                                            required
                                            disabled={!experiment.dataset_name}
                                            className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${!experiment.dataset_name ? "bg-gray-100 cursor-not-allowed" : ""}`}
                                        >
                                            <option value="">Select an architecture</option>
                                            {getCompatibleArchitectures().map((arch) => (
                                                <option key={arch.name} value={arch.name}>
                                                    {arch.description} ({arch.name})
                                                </option>
                                            ))}
                                        </select>
                                        {experiment.dataset_name &&
                                            getCompatibleArchitectures().length === 0 && (
                                                <p className="text-sm text-yellow-600 mt-1">
                                                    No compatible architectures found for this dataset
                                                </p>
                                            )}
                                    </div>
                                </div>
                                <div className="flex justify-end mt-6">
                                    <button
                                        onClick={() => setStep(2)}
                                        disabled={
                                            experiment.name ||
                                            experiment.dataset_name ||
                                            experiment.architecture_name
                                        }
                                        className={`inline-flex items-center px-4 py-2 rounded-lg transition-colors ${experiment.name &&
                                            experiment.dataset_name &&
                                            experiment.architecture_name
                                            ? "bg-blue-600 text-white hover:bg-blue-700"
                                            : "bg-gray-300 text-gray-500 cursor-not-allowed"
                                            }`}
                                    >
                                        <span>Next</span>
                                        <FaChevronRight className="ml-2" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 2: Configuration */}
                        {step === 2 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                                    Experiment Configuration
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-4">
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Noise Scale <span className="text-[11.5px] text-gray-600 font-medium">(Privacy Failure Probability)</span>
                                                </label>
                                                <select
                                                    name="dataset_name"
                                                    value={experiment.noise_mechanism}
                                                    onChange={handleChange}
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                >
                                                    <option value="">Select a Noise Mechanism</option>
                                                    {noise_mechanism.map((mechanism) => (
                                                        <option key={mechanism.name} value={mechanism.name}>
                                                            {mechanism.description} ({mechanism.name})
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}
                                        <div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Number of Clients*
                                                </label>
                                                <input
                                                    type="number"
                                                    name="num_clients"
                                                    value={experiment.num_clients}
                                                    onChange={handleChange}
                                                    min="2"
                                                    max="20"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Training Epochs*
                                                </label>
                                                <input
                                                    type="number"
                                                    name="parameters.epochs"
                                                    value={experiment.parameters.epochs}
                                                    onChange={handleChange}
                                                    min="1"
                                                    max="100"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Batch Size*
                                            </label>
                                            <input
                                                type="number"
                                                name="parameters.batch_size"
                                                value={experiment.parameters.batch_size}
                                                onChange={handleChange}
                                                min="8"
                                                max="256"
                                                step="8"
                                                required
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Learning Rate*
                                            </label>
                                            <input
                                                type="number"
                                                name="parameters.learning_rate"
                                                value={experiment.parameters.learning_rate}
                                                onChange={handleChange}
                                                min="0.0001"
                                                max="0.1"
                                                step="0.0001"
                                                required
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        <section className="flex gap-8 items-center">
                                            <div className="text-gray-700 text-sm font-medium">
                                                Differential Privacy
                                                <div className="flex items-center gap-2 text-gray-700 mb-2 text-sm font-normal mt-2" title="differential privacy">
                                                    Enable DP
                                                    <label className="relative inline-flex items-center cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            name="dp_enabled"
                                                            checked={experiment.dp_enabled}
                                                            onChange={handleChange}
                                                            className="sr-only peer"
                                                        />
                                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                    </label>
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Data Distribution*
                                                </label>
                                                <div className="flex space-x-4">
                                                    <label className="flex items-center cursor-pointer">
                                                        <input
                                                            type="radio"
                                                            name="iid"
                                                            value={experiment.iid === true}
                                                            defaultChecked={experiment.iid === true}
                                                            onChange={handleChange}
                                                            className="sr-only"
                                                        />
                                                        <div
                                                            className={`flex items-center px-4 py-2 rounded-lg border-2 ${experiment.iid === true ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
                                                        >
                                                            <span className="text-sm">IID</span>
                                                        </div>
                                                    </label>
                                                    <label className="flex items-center cursor-pointer">
                                                        <input
                                                            type="radio"
                                                            name="iid"
                                                            defaultChecked={experiment.iid === false}
                                                            onChange={handleChange}
                                                            className="sr-only"
                                                        />
                                                        <div
                                                            className={`flex items-center px-4 py-2 rounded-lg border-2 ${experiment.iid === false ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
                                                        >
                                                            <span className="text-sm">Non-IID</span>
                                                        </div>
                                                    </label>
                                                </div>
                                            </div>
                                        </section>
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Epsilon <span className="text-[11.5px] text-gray-600 font-medium">(Privacy Budget-allowable privacy loss)</span>
                                                </label>
                                                <input
                                                    type="number"
                                                    name="epsilon"
                                                    value={experiment.epsilon}
                                                    onChange={(e) => {
                                                        if (e.target.value > 1) e.target.value = 0.9
                                                        handleChange()
                                                    }}
                                                    min="0"
                                                    step="0.1"
                                                    max="1"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        )}
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Delta <span className="text-[11.5px] text-gray-600 font-medium">(Privacy Failure Probability)</span>
                                                </label>
                                                <input
                                                    type="number"
                                                    name="delta"
                                                    value={experiment.delta}
                                                    onChange={(e) => {
                                                        if (e.target.value > 1) e.target.value = 0.9
                                                        handleChange()
                                                    }}
                                                    min="0"
                                                    step="0.1"
                                                    max="1"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        )}
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Sensitivity <span className="text-[11.5px] text-gray-600 font-medium">(Maximum influence for one record)</span>
                                                </label>
                                                <input
                                                    type="number"
                                                    name="sensitivity"
                                                    value={experiment.sensitivity}
                                                    onChange={(e) => {
                                                        if (e.target.value > 1) e.target.value = 0.9
                                                        handleChange()
                                                    }}
                                                    min="0"
                                                    step="0.1"
                                                    max="1"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        )}
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Noise Scale <span className="text-[11.5px] text-gray-600 font-medium">(Increase randomness decrease accuracy)</span>
                                                </label>
                                                <input
                                                    type="number"
                                                    name="noise_scale"
                                                    value={experiment.noise_scale}
                                                    onChange={(e) => {
                                                        if (e.target.value > 1) e.target.value = 0.9
                                                        handleChange()
                                                    }}
                                                    min="0"
                                                    step="0.1"
                                                    max="1"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        )}
                                        {experiment.dp_enabled && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Maximum Grad Norm <span className="text-[11.5px] text-gray-600 font-medium">(Clipper threshold for gradient norms)</span>
                                                </label>
                                                <input
                                                    type="number"
                                                    name="max_grad_norm"
                                                    value={experiment.max_grad_norm}
                                                    onChange={(e) => {
                                                        if (e.target.value > 1) e.target.value = 0.9
                                                        handleChange()
                                                    }}
                                                    min="0"
                                                    step="0.1"
                                                    max="1"
                                                    required
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex justify-between mt-6">
                                    <button
                                        onClick={() => setStep(1)}
                                        className="inline-flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                    >
                                        <FaChevronRight className="mr-2 transform rotate-180" />
                                        <span>Back</span>
                                    </button>
                                    <button
                                        onClick={() => setStep(3)}
                                        className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        <span>Next</span>
                                        <FaChevronRight className="ml-2" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Review */}
                        {step === 3 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                                    Review Experiment Configuration
                                </h3>

                                <div className="space-y-6">
                                    {/* Basic Info */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                                            <FaInfoCircle className="text-gray-600 mr-2" />
                                            Basic Information
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                            <div>
                                                <p className="text-gray-500">Name</p>
                                                <p className="font-medium">{experiment.name}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Description</p>
                                                <p className="font-medium">
                                                    {experiment.description || "N/A"}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Dataset</p>
                                                <p className="font-medium">{experiment.dataset_name}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Architecture</p>
                                                <p className="font-medium">
                                                    {experiment.architecture_name}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Configuration */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                                            <FaInfoCircle className="text-gray-600 mr-2" />
                                            Experiment Configuration
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                            <div>
                                                <p className="text-gray-500">Number of Clients</p>
                                                <p className="font-medium">{experiment.num_clients}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Data Distribution</p>
                                                <p className="font-medium">
                                                    {experiment.iid ? "IID" : "Non-IID"}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Training Epochs</p>
                                                <p className="font-medium">
                                                    {experiment.parameters.epochs}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Batch Size</p>
                                                <p className="font-medium">
                                                    {experiment.parameters.batch_size}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Learning Rate</p>
                                                <p className="font-medium">
                                                    {experiment.parameters.learning_rate}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-between mt-6">
                                    <button
                                        onClick={() => setStep(2)}
                                        className="inline-flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                    >
                                        <FaChevronRight className="mr-2 transform rotate-180" />
                                        <span>Back</span>
                                    </button>
                                    <div className="flex space-x-3">
                                        <button
                                            onClick={() => navigate("/experiments")}
                                            className="inline-flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                        >
                                            <span>Cancel</span>
                                        </button>
                                        <button
                                            onClick={handleSubmit}
                                            className="inline-flex items-center bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                                        >
                                            <FaPlus className="mr-2" />
                                            <span>Create Experiment</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
