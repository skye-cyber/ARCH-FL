import { useState, useEffect, useRef } from "react";
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
    FaShieldAlt,
    FaChartLine,
    FaSlidersH,
} from "react-icons/fa";

export default function ExperimentCreate() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [datasets, setDatasets] = useState([]);
    const [architectures, setArchitectures] = useState([]);
    const [privacyStrength, setPrivacyStrength] = useState("moderate");
    const prevStep = useRef(null)
    const nextStep = useRef(null)

    const [experiment, setExperiment] = useState({
        name: "",
        description: "",
        dataset_name: "",
        architecture_name: "",
        num_clients: 5,
        iid: true,
        dp_enabled: false,
        epsilon: 1.0,
        delta: 0.00001,
        noise_mechanism: "gaussian",
        max_grad_norm: 1.0,
        parameters: {
            epochs: 10,
            batch_size: 32,
            learning_rate: 0.001,
        },
    });

    const noise_mechanisms = [
        {
            name: "gaussian",
            description: "Gaussian (ε,δ)-DP",
            icon: "📊",
            strength: "balanced",
        },
        {
            name: "laplace",
            description: "Laplace ε-DP",
            icon: "📈",
            strength: "strict",
        },
    ];

    // Privacy presets
    const privacyPresets = {
        strict: {
            epsilon: 0.5,
            delta: 1e-6,
            max_grad_norm: 0.5,
            description: "Maximum privacy, lower accuracy",
        },
        moderate: {
            epsilon: 1.0,
            delta: 1e-5,
            max_grad_norm: 1.0,
            description: "Balanced privacy and utility",
        },
        mild: {
            epsilon: 3.0,
            delta: 1e-4,
            max_grad_norm: 2.0,
            description: "Light privacy, higher accuracy",
        },
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [datasetsResponse, architecturesResponse] = await Promise.all([
                    datasetService.getAll(),
                    architectureService.getRegistry(),
                ]);
                setDatasets(datasetsResponse.data);
                setArchitectures(architecturesResponse.data);
            } catch (err) {
                console.error("Error fetching data:", err);
                setError("Failed to load data. Please try again later.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handlePrivacyPreset = (strength) => {
        setPrivacyStrength(strength);
        const preset = privacyPresets[strength];
        setExperiment((prev) => ({
            ...prev,
            epsilon: preset.epsilon,
            delta: preset.delta,
            max_grad_norm: preset.max_grad_norm,
        }));
    };

    const validateDataType = (name, value) => {
        const float_fields = ["delta", "epsilon", "max_grad_norm", "learning_rate"];
        if (float_fields.includes(name)) {
            return parseFloat(value);
        }
        if (["epochs", "batch_size", "num_clients"].includes(name)) {
            return parseInt(value, 10);
        }
        return value;
    };

    const handleChange = (e) => {
        let { name, value, type, checked } = e.target;
        value = validateDataType(name, value);

        if (name.startsWith("parameters.")) {
            const paramName = name.split(".")[1];
            setExperiment((prev) => ({
                ...prev,
                parameters: {
                    ...prev.parameters,
                    [paramName]: type === "checkbox" ? checked : value,
                },
            }));
        } else {
            setExperiment((prev) => ({
                ...prev,
                [name]: type === "checkbox" ? checked : value,
            }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await experimentService.create(experiment);
            navigate(`/experiments/${response.data.id}`);
        } catch (err) {
            console.error("Error creating experiment:", err);
            setError(
                "Failed to create experiment. Please check your inputs and try again.",
            );
            setTimeout(() => setError(null), 4000);
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
                    {/* Side panel */}
                    <div className="hidden md:block w-[24%] lg:w-[20%] bg-white rounded-lg shadow-sm border border-gray-200 p-4 h-fit sticky top-4">
                        <h2 className="text-center text-gray-800 font-semibold text-lg mb-6 flex items-center justify-center gap-2">
                            <FaChartLine className="text-gray-600" />
                            Steps
                        </h2>

                        <div className="space-y-2">
                            {[
                                { step: 1, title: "Basic Info" },
                                { step: 2, title: "Configuration" },
                                { step: 3, title: "Review" },
                            ].map((item) => (
                                <div
                                    key={item.step}
                                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${step === item.step
                                        ? "bg-blue-50 border border-blue-200"
                                        : "hover:bg-gray-50 border border-transparent"
                                        }`}
                                    onClick={() => {
                                        if (item.step > step) {
                                            nextStep.current.click()
                                        } else if (item.step < step) {
                                            prevStep.current.click()
                                        }
                                    }}
                                >
                                    <div
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center`}
                                    >
                                        {item.step === 1 && (
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
                                        )}
                                        {item.step === 2 && (
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
                                        )}
                                        {item.step === 3 && (
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
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs text-gray-400">Step {item.step}</p>
                                        <p
                                            className={`text-sm font-medium ${step === item.step ? "text-blue-700" : "text-gray-700"
                                                }`}
                                        >
                                            {item.title}
                                        </p>
                                    </div>
                                    {step === item.step && (
                                        <div className="w-1.5 h-1.5 rounded-full bg-blue-600"></div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Progress Indicator */}
                        <div className="mt-6 pt-4 border-t border-gray-200">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-xs font-medium text-gray-500">
                                    Overall Progress
                                </span>
                                <span className="text-xs font-semibold text-blue-600">
                                    {Math.floor((step / 3) * 100)}%
                                </span>
                            </div>
                            <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    style={{ width: `${Math.floor((step / 3) * 100)}%` }}
                                    className="h-full bg-blue-600 rounded-full transition-all duration-300"
                                ></div>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 space-y-4 w-full max-w-full">
                        {/* Step 1: Basic Info */}
                        {step === 1 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <span className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mr-2">
                                        1
                                    </span>
                                    Basic Information
                                </h3>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Experiment Name <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            name="name"
                                            value={experiment.name}
                                            onChange={handleChange}
                                            required
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
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
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                                Dataset <span className="text-red-500">*</span>
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
                                                Model Architecture{" "}
                                                <span className="text-red-500">*</span>
                                            </label>
                                            <select
                                                name="architecture_name"
                                                value={experiment.architecture_name}
                                                onChange={handleChange}
                                                required
                                                disabled={!experiment.dataset_name}
                                                className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${!experiment.dataset_name
                                                    ? "bg-gray-100 cursor-not-allowed"
                                                    : ""
                                                    }`}
                                            >
                                                <option value="">Select an architecture</option>
                                                {getCompatibleArchitectures().map((arch) => (
                                                    <option key={arch.name} value={arch.name}>
                                                        {arch.description} ({arch.name})
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex justify-end mt-6">
                                    <button
                                        ref={nextStep}
                                        onClick={() => setStep(2)}
                                        disabled={
                                            !experiment.name ||
                                            !experiment.dataset_name ||
                                            !experiment.architecture_name
                                        }
                                        className={`inline-flex items-center px-6 py-2 rounded-lg transition-all ${experiment.name &&
                                            experiment.dataset_name &&
                                            experiment.architecture_name
                                            ? "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg"
                                            : "bg-gray-300 text-gray-500 cursor-not-allowed"
                                            }`}
                                    >
                                        <span>Continue</span>
                                        <FaChevronRight className="ml-2" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 2: Configuration */}
                        {step === 2 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <span className="w-8 h-8 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mr-2">
                                        2
                                    </span>
                                    Experiment Configuration
                                </h3>

                                <div className="space-y-6">
                                    {/* Training Configuration */}
                                    <div className="border-b pb-4">
                                        <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                                            <FaSlidersH className="mr-2 text-gray-500" />
                                            Training Parameters
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Number of Clients
                                                </label>
                                                <input
                                                    type="number"
                                                    name="num_clients"
                                                    value={experiment.num_clients}
                                                    onChange={handleChange}
                                                    min="2"
                                                    max="100"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Training Epochs
                                                </label>
                                                <input
                                                    type="number"
                                                    name="parameters.epochs"
                                                    value={experiment.parameters.epochs}
                                                    onChange={handleChange}
                                                    min="1"
                                                    max="100"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Learning Rate
                                                </label>
                                                <input
                                                    type="number"
                                                    name="parameters.learning_rate"
                                                    value={experiment.parameters.learning_rate}
                                                    onChange={handleChange}
                                                    min="0.0001"
                                                    max="0.1"
                                                    step="0.0001"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Batch Size
                                                </label>
                                                <input
                                                    type="number"
                                                    name="parameters.batch_size"
                                                    value={experiment.parameters.batch_size}
                                                    onChange={handleChange}
                                                    min="1"
                                                    max="512"
                                                    step="8"
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Data Distribution
                                                </label>
                                                <div className="flex space-x-2">
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            setExperiment((prev) => ({ ...prev, iid: true }))
                                                        }
                                                        className={`flex-1 px-3 py-2 rounded-lg border-2 transition-all ${experiment.iid
                                                            ? "border-blue-500 bg-blue-50 text-blue-700"
                                                            : "border-gray-200 text-gray-600 hover:border-gray-300"
                                                            }`}
                                                    >
                                                        IID
                                                    </button>
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            setExperiment((prev) => ({ ...prev, iid: false }))
                                                        }
                                                        className={`flex-1 px-3 py-2 rounded-lg border-2 transition-all ${!experiment.iid
                                                            ? "border-blue-500 bg-blue-50 text-blue-700"
                                                            : "border-gray-200 text-gray-600 hover:border-gray-300"
                                                            }`}
                                                    >
                                                        Non-IID
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* DP Configuration */}
                                    <div>
                                        <div className="flex items-center justify-between mb-4">
                                            <h4 className="font-medium text-gray-700 flex items-center">
                                                <FaShieldAlt className="mr-2 text-green-600" />
                                                Differential Privacy
                                            </h4>
                                            <label className="relative inline-flex items-center cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    name="dp_enabled"
                                                    checked={experiment.dp_enabled}
                                                    onChange={handleChange}
                                                    className="sr-only peer"
                                                />
                                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                                <span className="ml-3 text-sm font-medium text-gray-700">
                                                    {experiment.dp_enabled ? "Enabled" : "Disabled"}
                                                </span>
                                            </label>
                                        </div>

                                        {experiment.dp_enabled && (
                                            <div className="space-y-4 pl-4 border-l-4 border-green-200">
                                                {/* Privacy Presets */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                                        Privacy Level
                                                    </label>
                                                    <div className="grid grid-cols-3 gap-2">
                                                        {Object.entries(privacyPresets).map(
                                                            ([key, preset]) => (
                                                                <button
                                                                    key={key}
                                                                    type="button"
                                                                    onClick={() => handlePrivacyPreset(key)}
                                                                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${privacyStrength === key
                                                                        ? "bg-green-600 text-white shadow-md"
                                                                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                                                                        }`}
                                                                >
                                                                    {key.charAt(0).toUpperCase() + key.slice(1)}
                                                                    <div className="text-xs opacity-75 mt-1">
                                                                        {preset.description}
                                                                    </div>
                                                                </button>
                                                            ),
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                                            Epsilon (ε) - Privacy Budget
                                                            <span
                                                                className="ml-1 text-xs text-gray-500 cursor-help"
                                                                title="Smaller = stronger privacy, typical range: 0.1-10.0"
                                                            >
                                                                ⓘ
                                                            </span>
                                                        </label>
                                                        <input
                                                            type="range"
                                                            name="epsilon"
                                                            value={experiment.epsilon}
                                                            onChange={handleChange}
                                                            min="0.1"
                                                            max="10.0"
                                                            step="0.1"
                                                            className="w-full"
                                                        />
                                                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                            <span>Strong (0.1)</span>
                                                            <span className="font-bold text-blue-600">
                                                                {experiment.epsilon.toFixed(1)}
                                                            </span>
                                                            <span>Weak (10.0)</span>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                                            Delta (δ) - Failure Probability
                                                            <span
                                                                className="ml-1 text-xs text-gray-500 cursor-help"
                                                                title="Typical: 1e-5 to 1e-7"
                                                            >
                                                                ⓘ
                                                            </span>
                                                        </label>
                                                        <input
                                                            type="range"
                                                            name="delta"
                                                            value={-Math.log10(experiment.delta)}
                                                            onChange={(e) => {
                                                                const deltaValue = Math.pow(
                                                                    10,
                                                                    -parseFloat(e.target.value),
                                                                );
                                                                setExperiment((prev) => ({
                                                                    ...prev,
                                                                    delta: deltaValue,
                                                                }));
                                                            }}
                                                            min="4"
                                                            max="7"
                                                            step="0.1"
                                                            className="w-full"
                                                        />
                                                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                            <span>1e-4 (lenient)</span>
                                                            <span className="font-bold text-blue-600">
                                                                {experiment.delta.toExponential(1)}
                                                            </span>
                                                            <span>1e-7 (strict)</span>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                                            Max Grad Norm (C) - Clipping Bound
                                                            <span
                                                                className="ml-1 text-xs text-gray-500 cursor-help"
                                                                title="Typical range: 0.1-10.0"
                                                            >
                                                                ⓘ
                                                            </span>
                                                        </label>
                                                        <input
                                                            type="range"
                                                            name="max_grad_norm"
                                                            value={experiment.max_grad_norm}
                                                            onChange={handleChange}
                                                            min="0.1"
                                                            max="10.0"
                                                            step="0.1"
                                                            className="w-full"
                                                        />
                                                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                            <span>Conservative (0.1)</span>
                                                            <span className="font-bold text-blue-600">
                                                                {experiment.max_grad_norm.toFixed(1)}
                                                            </span>
                                                            <span>Permissive (10.0)</span>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                                            Noise Mechanism
                                                        </label>
                                                        <select
                                                            name="noise_mechanism"
                                                            value={experiment.noise_mechanism}
                                                            onChange={handleChange}
                                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                                        >
                                                            {noise_mechanisms.map((mechanism) => (
                                                                <option
                                                                    key={mechanism.name}
                                                                    value={mechanism.name}
                                                                >
                                                                    {mechanism.description}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                </div>

                                                {/* Privacy Budget Indicator */}
                                                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                                                    <div className="flex justify-between text-sm mb-1">
                                                        <span className="text-gray-600">
                                                            Privacy Budget Usage
                                                        </span>
                                                        <span className="text-gray-600">
                                                            {experiment.epsilon} / 10.0
                                                        </span>
                                                    </div>
                                                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full transition-all ${experiment.epsilon <= 1
                                                                ? "bg-green-500"
                                                                : experiment.epsilon <= 3
                                                                    ? "bg-yellow-500"
                                                                    : "bg-red-500"
                                                                }`}
                                                            style={{
                                                                width: `${(experiment.epsilon / 10) * 100}%`,
                                                            }}
                                                        ></div>
                                                    </div>
                                                    <p className="text-xs text-gray-500 mt-2">
                                                        {experiment.epsilon <= 1
                                                            ? "🔒 Strong privacy protection"
                                                            : experiment.epsilon <= 3
                                                                ? "⚖️ Balanced privacy-utility trade-off"
                                                                : "⚠️ Weak privacy protection"}
                                                    </p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex justify-between mt-6">
                                    <button
                                        ref={prevStep}
                                        onClick={() => setStep(1)}
                                        className="inline-flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                    >
                                        <FaChevronRight className="mr-2 transform rotate-180" />
                                        Back
                                    </button>
                                    <button
                                        onClick={() => setStep(3)}
                                        className="inline-flex items-center bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-all hover:shadow-lg"
                                    >
                                        Review
                                        <FaChevronRight className="ml-2" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Review */}
                        {step === 3 && (
                            <div className="bg-white rounded-lg shadow p-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                                    <span className="w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center mr-2">
                                        3
                                    </span>
                                    Review & Create
                                </h3>

                                <div className="space-y-4">
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-medium text-gray-800 mb-3">
                                            Experiment Details
                                        </h4>
                                        <div className="grid grid-cols-2 gap-3 text-sm">
                                            <div>
                                                <span className="text-gray-500">Name:</span>{" "}
                                                <span className="font-medium">{experiment.name}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Dataset:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.dataset_name}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Architecture:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.architecture_name}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Clients:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.num_clients}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Distribution:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.iid ? "IID" : "Non-IID"}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Epochs:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.parameters.epochs}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Learning Rate:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.parameters.learning_rate}
                                                </span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Batch Size:</span>{" "}
                                                <span className="font-medium">
                                                    {experiment.parameters.batch_size}
                                                </span>
                                            </div>
                                            {experiment.dp_enabled && (
                                                <>
                                                    <div>
                                                        <span className="text-gray-500">DP Enabled:</span>{" "}
                                                        <span className="font-medium text-green-600">
                                                            Yes
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <span className="text-gray-500">Epsilon (ε):</span>{" "}
                                                        <span className="font-medium">
                                                            {experiment.epsilon}
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <span className="text-gray-500">Delta (δ):</span>{" "}
                                                        <span className="font-medium">
                                                            {experiment.delta.toExponential()}
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <span className="text-gray-500">
                                                            Max Grad Norm:
                                                        </span>{" "}
                                                        <span className="font-medium">
                                                            {experiment.max_grad_norm}
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <span className="text-gray-500">
                                                            Noise Mechanism:
                                                        </span>{" "}
                                                        <span className="font-medium">
                                                            {experiment.noise_mechanism}
                                                        </span>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex justify-between mt-6">
                                    <button
                                        onClick={() => setStep(2)}
                                        className="inline-flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                                    >
                                        <FaChevronRight className="mr-2 transform rotate-180" />
                                        Back
                                    </button>
                                    <div className="flex space-x-3">
                                        <button
                                            onClick={() => navigate("/experiments")}
                                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleSubmit}
                                            className="inline-flex items-center bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-all hover:shadow-lg"
                                        >
                                            <FaPlus className="mr-2" />
                                            Create Experiment
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
