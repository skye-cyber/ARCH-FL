import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import {
    healthService,
    experimentService,
    datasetService,
    architectureService,
    systemInfoService,
} from "../services/api";

import {
    FlaskConical,
    Database,
    Network,
    Activity,
    Plus,
    ChevronRight,
    Clock,
    TrendingUp,
    Users,
    HardDrive,
    BarChart3,
    Sparkles,
    ArrowUpRight,
    Github,
    BookOpen,
} from "lucide-react";

export default function Home() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        experiments: 0,
        datasets: 0,
        architectures: 0,
        status: "loading",
    });
    const [recentExperiments, setRecentExperiments] = useState([]);
    const [systemInfo, setSystemInfo] = useState({
        system_info: {
            cpu: { percent: 0 },
            memory: {
                used: 0,
                used_human: 0,
                avilable: 0,
                available_human: 0,
                percent: 0,
            },
            disk: {
                used: 0,
                used_human: 0,
                available: 0,
                available_human: 0,
                percent: 0,
            },
            uptime: "-",
        },
        version: '-',
        network: 0,
    });
    const [overviewStats, setOverviewStats] = useState({
        activeClients: 0,
        avgAccuracy: "-",
    });
    const [footerMetrics, setFooterMetrics] = useState({
        trainingHours: "-",
        modelsDeployed: "-",
        activeCollaborators: "-",
        successRate: "-",
    });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            setIsLoading(true);
            try {
                const [
                    healthResponse,
                    experimentsResponse,
                    datasetsResponse,
                    architecturesResponse,
                    systemInfoResponse,
                    experimentResultResponse,
                ] = await Promise.all([
                    healthService.check(),
                    experimentService.getAll(),
                    datasetService.getAll(),
                    architectureService.getRegistry(),
                    systemInfoService.get(),
                    experimentService.getAllResults()
                ]);

                setStats({
                    experiments: experimentsResponse.data.length,
                    datasets: datasetsResponse.data.length,
                    architectures: architecturesResponse.data.length,
                    status: healthResponse.data.status,
                });

                // Get recent experiments (last 3)
                const sortedExperiments = [...experimentResultResponse.data].sort(
                    (a, b) => new Date(b.created_at) - new Date(a.created_at),
                ).slice(0, 3);
                try {
                    for (const exp of sortedExperiments) {
                        const metrics = exp?.metrics
                        if (metrics) {
                            const metricsOBJ = JSON.parse(metrics)
                            if (metricsOBJ) exp.metrics = metricsOBJ
                        }
                    }
                } catch (err) { }
                setRecentExperiments(sortedExperiments);
                console.log(sortedExperiments)
                //Calculate overview stats
                //                 const completedExperiments = experimentResultResponse.data.filter(
                //                     (exp) => exp.status === "completed",
                //                 );

                const avgAccuracy =
                    experimentResultResponse.data.length > 0
                        ? experimentResultResponse.data.reduce((sum, exp) => {
                            return sum + (exp.accuracy || 0);
                        }, 0) / experimentResultResponse.data.length
                        : 0;

                setOverviewStats({
                    activeClients: experimentsResponse.data.reduce(
                        (sum, exp) => sum + exp.num_clients,
                        0,
                    ),
                    avgAccuracy: `${(avgAccuracy).toFixed(1)}%`,
                });
                setFooterMetrics({ successRate: `${(avgAccuracy).toFixed(1)}%` })

                // Set system metrics real data
                setSystemInfo(systemInfoResponse.data);
                // Set footer metrics(upcomin)
            } catch (error) {
                console.error("Error fetching stats:", error);
                setStats((prev) => ({ ...prev, status: "error" }));
            } finally {
                setIsLoading(false);
            }
        };

        fetchStats();
    }, []);

    const statCards = [
        {
            title: "Experiments",
            value: stats.experiments,
            icon: FlaskConical,
            change: "+12%",
            trend: "up",
            color: "blue",
            bgLight: "bg-blue-50",
            iconColor: "text-blue-600",
            borderColor: "border-blue-100",
        },
        {
            title: "Datasets",
            value: stats.datasets,
            icon: Database,
            change: "+5%",
            trend: "up",
            color: "emerald",
            bgLight: "bg-emerald-50",
            iconColor: "text-emerald-600",
            borderColor: "border-emerald-100",
        },
        {
            title: "Architectures",
            value: stats.architectures,
            icon: Network,
            change: "0%",
            trend: "neutral",
            color: "violet",
            bgLight: "bg-violet-50",
            iconColor: "text-violet-600",
            borderColor: "border-violet-100",
        },
        {
            title: "System Status",
            value:
                stats.status === "healthy"
                    ? "Operational"
                    : stats.status === "loading"
                        ? "Checking"
                        : "Attention",
            icon: Activity,
            subtext: stats.status === "healthy" ? "All systems go" : "Partial outage",
            change: stats.status === "healthy" ? "99.9%" : "—",
            trend: stats.status === "healthy" ? "up" : "neutral",
            color: stats.status === "healthy" ? "green" : "amber",
            bgLight: stats.status === "healthy" ? "bg-green-50" : "bg-amber-50",
            iconColor:
                stats.status === "healthy" ? "text-green-600" : "text-amber-600",
            borderColor:
                stats.status === "healthy" ? "border-green-100" : "border-amber-100",
        },
    ];

    const quickActions = [
        {
            label: "New Experiment",
            icon: FlaskConical,
            description: "Start a federated learning run",
            color: "blue",
            gradient: "from-blue-500 to-blue-600",
            lightBg: "bg-blue-50",
            path: "/experiments/new",
        },
        {
            label: "Add Dataset",
            icon: Database,
            description: "Upload medical imaging data",
            color: "emerald",
            gradient: "from-emerald-500 to-emerald-600",
            lightBg: "bg-emerald-50",
            path: "/datasets",
        },
        {
            label: "Design Architecture",
            icon: Network,
            description: "Create custom neural networks",
            color: "violet",
            gradient: "from-violet-500 to-violet-600",
            lightBg: "bg-violet-50",
            path: "/architectures",
        },
    ];

    const features = [
        "Real-time federated learning monitoring",
        "Privacy-preserving data handling",
        "Multi-client orchestration",
        "Interactive visualization tools",
        "Model versioning & comparison",
    ];

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: { staggerChildren: 0.1 },
        },
    };

    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 },
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100/50">
            {/* Header with subtle gradient */}
            <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="p-2.5 bg-gradient-to-br from-blue-600 to-violet-600 rounded-xl shadow-lg shadow-blue-600/20">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-semibold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                                    ARCH-FL Dashboard
                                </h1>
                                <p className="text-sm text-gray-500 flex items-center mt-0.5">
                                    Federated Learning Platform
                                    <span className="mx-2 w-1 h-1 bg-gray-300 rounded-full" />
                                    <span className="text-blue-600">{systemInfo.version}</span>
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                                <BookOpen className="w-5 h-5" />
                            </button>
                            <Link
                                target="_blank"
                                to="https://github.com/skye-cyber/ARCH-FL.git"
                                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Github className="w-5 h-5" />
                            </Link>
                            <button
                                onClick={() => navigate("experiments/new")}
                                className="ml-2 inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-all shadow-sm hover:shadow"
                            >
                                <Plus className="w-4 h-4 mr-2" />
                                New Project
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <motion.div
                    variants={container}
                    initial="hidden"
                    animate="show"
                    className="space-y-8"
                >
                    {/* Stats Grid */}
                    <motion.div
                        variants={item}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
                    >
                        {statCards.map((stat) => (
                            <motion.div
                                key={stat.title}
                                whileHover={{ y: -2 }}
                                className="group bg-white rounded-2xl p-4 border border-gray-100 hover:border-gray-200 shadow-md hover:shadow-lg hover:translate-y-2 transition-all duration-100"
                            >
                                <div className="flex items-start justify-between mb-1">
                                    <div
                                        className={`p-3 ${stat.bgLight} rounded-xl group-hover:scale-110 transition-transform`}
                                    >
                                        <stat.icon className={`w-5 h-5 ${stat.iconColor}`} />
                                    </div>
                                    {stat.change && (
                                        <span
                                            className={`inline-flex items-center px-1 py-1 rounded-full text-xs font-normal ${stat.trend === "up"
                                                ? "bg-green-50 text-green-700"
                                                : stat.trend === "down"
                                                    ? "bg-red-50 text-red-700"
                                                    : "bg-gray-50 text-gray-600"
                                                }`}
                                        >
                                            {stat.trend === "up" && (
                                                <ArrowUpRight className="w-3 h-3 mr-0.5" />
                                            )}
                                            {stat.change}
                                        </span>
                                    )}
                                </div>

                                {isLoading ? (
                                    <div className="space-y-4">
                                        <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
                                        <div className="h-8 w-24 bg-gray-200 rounded animate-pulse" />
                                    </div>
                                ) : (
                                    <>
                                        <p className="text-xs text-gray-500 mb-1">{stat.title}</p>
                                        <p className="text-2xl font-semibold text-gray-900">
                                            {stat.value}
                                        </p>
                                        {stat.subtext && (
                                            <p className="text-xs text-gray-400 mt-1">
                                                {stat.subtext}
                                            </p>
                                        )}
                                    </>
                                )}

                                {/* Mini progress for system status */}
                                {stat.title === "System Status" &&
                                    stats.status === "healthy" && (
                                        <div className="mt-4 h-1 bg-green-100 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: "0%" }}
                                                animate={{ width: "100%" }}
                                                transition={{ duration: 1, delay: 0.5 }}
                                                className="h-full bg-green-500 rounded-full"
                                            />
                                        </div>
                                    )}
                            </motion.div>
                        ))}
                    </motion.div>

                    {/* Quick Actions Section */}
                    <motion.div
                        variants={item}
                        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
                    >
                        {/* Quick Actions Cards */}
                        <div className="lg:col-span-2">
                            <div className="bg-white rounded-2xl border border-gray-100 p-6">
                                <div className="flex items-center justify-between mb-5">
                                    <h2 className="text-lg font-semibold text-gray-900">
                                        Quick Actions
                                    </h2>
                                    <button className="text-sm text-gray-400 hover:text-gray-600 flex items-center">
                                        View all
                                        <ChevronRight className="w-4 h-4 ml-1" />
                                    </button>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {quickActions.map((action) => (
                                        <Link
                                            key={action.label}
                                            to={action.path}
                                            className="group relative p-5 rounded-xl border border-gray-100 hover:border-gray-200 transition-all text-left overflow-hidden"
                                        >
                                            {/* Hover gradient */}
                                            <div
                                                className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-5 transition-opacity`}
                                            />

                                            <div
                                                className={`p-2.5 ${action.lightBg} rounded-lg w-fit mb-4 group-hover:scale-110 transition-transform`}
                                            >
                                                <action.icon
                                                    className={`w-5 h-5 text-${action.color}-600`}
                                                />
                                            </div>
                                            <h3 className="font-medium text-gray-900 mb-1">
                                                {action.label}
                                            </h3>
                                            <p className="text-xs text-gray-500">
                                                {action.description}
                                            </p>

                                            <div className="mt-4 flex items-center text-xs font-medium text-gray-400 group-hover:text-gray-600">
                                                Start
                                                <ChevronRight className="w-3 h-3 ml-1 group-hover:translate-x-1 transition-transform" />
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* System Health Card */}
                        <div className="bg-white dark:bg-gray-900 dark:to-gray-800 border shadow-lg  rounded-2xl p-6 text-white">
                            <div className="flex items-center space-x-2 mb-4">
                                <Activity className="w-5 h-5 text-emerald-400" />
                                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                                    System Health
                                </span>
                            </div>
                            <div className="space-y-4">
                                {[
                                    {
                                        label: "CPU",
                                        value: systemInfo.system_info.cpu.percent || "-",
                                        color: "bg-emerald-400",
                                    },
                                    {
                                        label: "Memory",
                                        value: systemInfo.system_info.memory.used_human || "-GB",
                                        total: systemInfo.system_info.memory.total_human || "-",
                                        color: "bg-blue-400",
                                    },
                                    {
                                        label: "Storage",
                                        value: systemInfo.system_info.disk.used_human || "-GB",
                                        total: systemInfo.system_info.disk.total_human || "-",
                                        color: "bg-violet-400",
                                    },
                                ].map((metric) => (
                                    <div key={metric.label}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-800 dark:text-gray-300">
                                                {metric.label}
                                            </span>
                                            <span className="text-gray-800 dark:text-gray-200">
                                                {metric.label === "CPU"
                                                    ? `${metric.value}%`
                                                    : metric.label === "Memory"
                                                        ? `${metric.value?.replace("GB", "")}/${metric.total}`
                                                        : `${metric.value?.replace("GB", "")}/${metric.total}`}
                                            </span>
                                        </div>
                                        <div className="h-1.5 bg-gray-300 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: "0%" }}
                                                animate={{
                                                    width: `${metric.label === "CPU"
                                                        ? metric.value
                                                        : metric.label === "Memory"
                                                            ? systemInfo.system_info.memory.percent
                                                            : systemInfo.system_info.disk.percent
                                                        }%`,
                                                }}
                                                transition={{ duration: 1, delay: 0.3 }}
                                                className={`h-full ${metric.color} rounded-full`}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>

                    {/* Experiments & Info Grid */}
                    <motion.div
                        variants={item}
                        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
                    >
                        {/* Recent Experiments - Takes 2 columns */}
                        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-6">
                            <div className="flex items-center justify-between mb-5">
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Recent Experiments
                                </h2>
                                <Link to={'/experiments'} className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center" >
                                    View all
                                    <ChevronRight className="w-4 h-4 ml-1" />
                                </Link>
                            </div>
                            <div className="space-y-3">
                                {recentExperiments.length > 0 ? (
                                    recentExperiments.map((exp, idx) => {
                                        // Calculate progress based on status
                                        let progress = 0;
                                        let timeDisplay = "";

                                        if (exp.metrics.status === "completed") {
                                            progress = 100;
                                            const createdAt = new Date(exp.timestamp);
                                            const now = new Date();
                                            const diffMinutes = Math.floor(
                                                (now - createdAt) / (1000 * 60),
                                            );
                                            timeDisplay =
                                                diffMinutes < 60
                                                    ? `${diffMinutes}m ago`
                                                    : `${Math.floor(diffMinutes / 60)}h ago`;
                                        } else if (exp.metrics.status === "running") {
                                            progress = (exp.rounds_completed / exp.total_rounds) * 100 || 75;
                                            timeDisplay = "In progress";
                                        } else {
                                            progress = 0;
                                            timeDisplay = "Pending";
                                        }

                                        return (
                                            <Link
                                                key={exp.id}
                                                to={`/experiments/${exp.id}`}
                                                className="flex items-center justify-between p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                                            >
                                                <div className="flex-1">
                                                    <div className="flex items-center mb-2">
                                                        <p className="text-sm font-medium text-gray-900">
                                                            {exp.name}
                                                        </p>
                                                        <span
                                                            className={`ml-2 text-xs px-2 py-0.5 rounded-full ${exp.metrics.status === "running"
                                                                ? "bg-blue-100 text-blue-700"
                                                                : exp.metrics.status === "completed"
                                                                    ? "bg-green-100 text-green-700"
                                                                    : "bg-yellow-100 text-yellow-700"
                                                                }`}
                                                        >
                                                            {exp.metrics.status}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <div className="flex-1 max-w-md">
                                                            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                                                <motion.div
                                                                    initial={{ width: "0%" }}
                                                                    animate={{ width: `${progress}%` }}
                                                                    transition={{ duration: 1, delay: 0.2 }}
                                                                    className={`h-full rounded-full ${exp.metrics.status === "running"
                                                                        ? "bg-blue-600"
                                                                        : exp.metrics.status === "completed"
                                                                            ? "bg-green-600"
                                                                            : "bg-yellow-600"
                                                                        }`}
                                                                />
                                                            </div>
                                                        </div>
                                                        <span className="text-xs text-gray-500">
                                                            {timeDisplay}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="ml-4 text-right">
                                                    <p className="text-sm font-semibold text-gray-900">
                                                        {exp.client_count}
                                                    </p>
                                                    <p className="text-xs text-gray-500">clients</p>
                                                </div>
                                            </Link>
                                        );
                                    })
                                ) : (
                                    <div className="p-8 text-center text-gray-500">
                                        <FlaskConical className="text-3xl mx-auto mb-4 text-gray-300" />
                                        <p>No recent experiments found</p>
                                        <p className="text-sm mt-2">
                                            Create your first experiment to get started
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Right Column - Info & Stats */}
                        <div className="space-y-6">
                            {/* Quick Stats */}
                            <div className="bg-white rounded-2xl border border-gray-100 p-6">
                                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
                                    Overview
                                </h3>
                                <div className="space-y-3">
                                    {[
                                        {
                                            icon: Users,
                                            label: "Active Clients",
                                            value: overviewStats.activeClients,
                                        },
                                        {
                                            icon: HardDrive,
                                            label: "Storage Used",
                                            value: systemInfo.system_info.disk.used_human,
                                        },
                                        {
                                            icon: BarChart3,
                                            label: "Avg. Accuracy",
                                            value: overviewStats.avgAccuracy,
                                        },
                                        {
                                            icon: Clock,
                                            label: "Uptime",
                                            value: systemInfo.uptime,
                                        },
                                    ].map((stat) => (
                                        <div
                                            key={stat.label}
                                            className="flex items-center justify-between p-2"
                                        >
                                            <div className="flex items-center text-gray-600">
                                                <stat.icon className="w-4 h-4 mr-3" />
                                                <span className="text-sm">{stat.label}</span>
                                            </div>
                                            <span className="text-sm font-semibold text-gray-900">
                                                {stat.value}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Features Card */}
                            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                                <h3 className="text-sm font-medium text-blue-900 mb-3">
                                    Key Features
                                </h3>
                                <ul className="space-y-2">
                                    {features.map((feature, idx) => (
                                        <li
                                            key={idx}
                                            className="flex items-start text-sm text-blue-800"
                                        >
                                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-1.5 mr-2" />
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                                <Link
                                    to="https://github.com/skye-cyber/ARCH-FL.git"
                                    target="_blank"
                                    className="mt-4 text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center"
                                >
                                    Learn more about ARCH-FL
                                    <ChevronRight className="w-3 h-3 ml-1" />
                                </Link>
                            </div>

                            {/* Tip Card */}
                            <div className="bg-amber-50 rounded-2xl p-4 border border-amber-100">
                                <p className="text-xs text-amber-800 font-medium mb-1 flex items-center">
                                    <Sparkles className="w-3 h-3 mr-1" />
                                    Pro tip (upcoming update)
                                </p>
                                <p className="text-xs text-amber-700">
                                    Drag and drop datasets directly into an experiment to start
                                    training instantly.
                                </p>
                            </div>
                        </div>
                    </motion.div>

                    {/* Footer Metrics */}
                    <motion.div
                        variants={item}
                        className="grid grid-cols-2 md:grid-cols-4 gap-4"
                    >
                        {[
                            {
                                label: "Total Training Hours",
                                value: footerMetrics.trainingHours,
                                change: "-%",
                            },
                            {
                                label: "Models Deployed",
                                value: footerMetrics.modelsDeployed,
                                change: "-",
                            },
                            {
                                label: "Active Collaborators",
                                value: footerMetrics.activeCollaborators,
                                change: "-",
                            },
                            {
                                label: "Success Rate",
                                value: footerMetrics.successRate || m,
                                change: "-%",
                            },
                        ].map((metric) => (
                            <div
                                key={metric.label}
                                className="bg-white rounded-xl p-5 border border-gray-100"
                            >
                                <p className="text-xs text-gray-500 mb-1">{metric.label}</p>
                                <div className="flex items-end justify-between">
                                    <p className="text-xl font-semibold text-gray-900">
                                        {metric.value}
                                    </p>
                                    <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
                                        {metric.change}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </motion.div>
                </motion.div>
            </div>
        </div>
    );
}
