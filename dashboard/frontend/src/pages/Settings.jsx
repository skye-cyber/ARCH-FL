import { useState } from "react";
import { motion } from "framer-motion";
import {
  Settings as SettingsIcon,
  Save,
  User,
  Palette,
  Moon,
  Sun,
  Database,
  BarChart3,
  Bell,
  RefreshCw,
  Globe,
  Shield,
  Sliders,
  ChevronRight,
  Monitor,
  Smartphone,
  Tablet,
  Eye,
  Clock,
  Layers,
  Download,
  Users,
  Gauge,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { useTheme } from "../components/Themes/useThemeHeadless";

export default function Settings() {
  const { isDark, toggleTheme, setTheme } = useTheme();

  const [settings, setSettings] = useState({
    theme: isDark ? "dark" : "light",
    notifications: true,
    autoRefresh: true,
    refreshInterval: 30,
    showTutorials: true,
    defaultClients: 5,
    defaultEpochs: 10,
    chartType: "line",
    compactMode: false,
    dataRetention: 30,
    emailReports: false,
  });

  const [activeTab, setActiveTab] = useState("general");
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    console.log(name, value);
    if (name === "theme") {
      if (["dark", "light"].includes(value)) setTheme(value);
    }
    setSettings((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));

    setIsSaving(false);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);

    console.log("Settings saved:", settings);
  };

  const tabs = [
    { id: "general", label: "General", icon: User },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "data", label: "Data & Storage", icon: Database },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "advanced", label: "Advanced", icon: Sliders },
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
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-20 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-600/20">
                <SettingsIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Settings
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">
                  Configure your ARCH-FL preferences
                </p>
              </div>
            </div>

            {/* Save indicator */}
            <div className="flex items-center gap-4">
              {showSuccess && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center text-green-600 bg-green-50 px-3 py-2 rounded-lg"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">Settings saved!</span>
                </motion.div>
              )}

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={isSaving}
                className="inline-flex items-center px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm hover:shadow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                      className="mr-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </motion.div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    <span>Save Changes</span>
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar Navigation */}
          <div className="w-64 shrink-0">
            <div className="bg-white rounded-2xl border border-gray-100 p-4 sticky top-24">
              <nav className="space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${
                      activeTab === tab.id
                        ? "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-100"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                  >
                    <div className="flex items-center">
                      <tab.icon
                        className={`w-4 h-4 mr-3 ${
                          activeTab === tab.id
                            ? "text-blue-600"
                            : "text-gray-400"
                        }`}
                      />
                      <span className="text-sm font-medium">{tab.label}</span>
                    </div>
                    {activeTab === tab.id && (
                      <ChevronRight className="w-4 h-4 text-blue-600" />
                    )}
                  </button>
                ))}
              </nav>

              {/* Quick Stats */}
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-xs text-gray-500 mb-3">
                    Configuration Summary
                  </p>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Theme</span>
                      <span className="font-medium text-gray-900 capitalize">
                        {settings.theme}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Chart Type</span>
                      <span className="font-medium text-gray-900 capitalize">
                        {settings.chartType}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Auto-refresh</span>
                      <span className="font-medium text-gray-900">
                        {settings.autoRefresh ? "On" : "Off"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <motion.div
              key={activeTab}
              variants={container}
              initial="hidden"
              animate="show"
              className="space-y-6"
            >
              {/* General Settings */}
              {activeTab === "general" && (
                <>
                  <motion.div
                    variants={item}
                    className="bg-white rounded-2xl border border-gray-100 overflow-hidden"
                  >
                    <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-transparent">
                      <div className="flex items-center">
                        <User className="w-5 h-5 text-blue-600 mr-2" />
                        <h2 className="text-lg font-semibold text-gray-900">
                          General Preferences
                        </h2>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Configure default experiment and client settings
                      </p>
                    </div>

                    <div className="p-6 space-y-6">
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Default Clients
                          </label>
                          <div className="relative">
                            <Users className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                              type="number"
                              name="defaultClients"
                              value={settings.defaultClients}
                              onChange={handleChange}
                              min="2"
                              max="20"
                              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Number of clients for new experiments
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Default Epochs
                          </label>
                          <div className="relative">
                            <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                              type="number"
                              name="defaultEpochs"
                              value={settings.defaultEpochs}
                              onChange={handleChange}
                              min="1"
                              max="100"
                              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Training epochs per experiment
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                        <div className="flex items-start space-x-3">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Eye className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              Show tutorial tips
                            </p>
                            <p className="text-xs text-gray-500">
                              Display helpful hints throughout the interface
                            </p>
                          </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            name="showTutorials"
                            checked={settings.showTutorials}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </motion.div>
                </>
              )}

              {/* Appearance Settings */}
              {activeTab === "appearance" && (
                <motion.div
                  variants={item}
                  className="bg-white rounded-2xl border border-gray-100 overflow-hidden"
                >
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-transparent">
                    <div className="flex items-center">
                      <Palette className="w-5 h-5 text-purple-600 mr-2" />
                      <h2 className="text-lg font-semibold text-gray-900">
                        Appearance
                      </h2>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Customize the look and feel of your dashboard
                    </p>
                  </div>

                  <div className="p-6 space-y-8">
                    {/* Theme Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Theme
                      </label>
                      <div className="grid grid-cols-3 gap-4">
                        {[
                          {
                            id: "light",
                            icon: Sun,
                            label: "Light",
                            color: "yellow",
                          },
                          {
                            id: "dark",
                            icon: Moon,
                            label: "Dark",
                            color: "indigo",
                          },
                          {
                            id: "system",
                            icon: Monitor,
                            label: "System",
                            color: "gray",
                          },
                        ].map((theme) => (
                          <label
                            key={theme.id}
                            className={`relative flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all ${
                              settings.theme === theme.id
                                ? "border-blue-500 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                            }`}
                          >
                            <input
                              type="radio"
                              name="theme"
                              value={theme.id}
                              checked={settings.theme === theme.id}
                              onChange={handleChange}
                              className="sr-only"
                            />
                            <theme.icon
                              className={`w-6 h-6 mb-2 ${
                                settings.theme === theme.id
                                  ? `text-${theme.color}-600`
                                  : "text-gray-400"
                              }`}
                            />
                            <span
                              className={`text-sm font-medium ${
                                settings.theme === theme.id
                                  ? "text-blue-700"
                                  : "text-gray-700"
                              }`}
                            >
                              {theme.label}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Chart Type */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Default Chart Type
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { value: "line", icon: BarChart3, label: "Line" },
                          { value: "bar", icon: BarChart3, label: "Bar" },
                          { value: "area", icon: Layers, label: "Area" },
                        ].map((chart) => (
                          <label
                            key={chart.value}
                            className={`relative flex items-center justify-center p-3 rounded-xl border-2 cursor-pointer transition-all ${
                              settings.chartType === chart.value
                                ? "border-blue-500 bg-blue-50"
                                : "border-gray-200 hover:border-gray-300"
                            }`}
                          >
                            <input
                              type="radio"
                              name="chartType"
                              value={chart.value}
                              checked={settings.chartType === chart.value}
                              onChange={handleChange}
                              className="sr-only"
                            />
                            <chart.icon
                              className={`w-4 h-4 mr-2 ${
                                settings.chartType === chart.value
                                  ? "text-blue-600"
                                  : "text-gray-400"
                              }`}
                            />
                            <span
                              className={`text-sm ${
                                settings.chartType === chart.value
                                  ? "text-blue-700 font-medium"
                                  : "text-gray-600"
                              }`}
                            >
                              {chart.label}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Compact Mode */}
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-start space-x-3">
                        <div className="p-2 bg-purple-100 rounded-lg">
                          <Gauge className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Compact Mode
                          </p>
                          <p className="text-xs text-gray-500">
                            Reduce spacing for more content density
                          </p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          name="compactMode"
                          checked={settings.compactMode}
                          onChange={handleChange}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                      </label>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Data Settings */}
              {activeTab === "data" && (
                <motion.div
                  variants={item}
                  className="bg-white rounded-2xl border border-gray-100 overflow-hidden"
                >
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-transparent">
                    <div className="flex items-center">
                      <Database className="w-5 h-5 text-emerald-600 mr-2" />
                      <h2 className="text-lg font-semibold text-gray-900">
                        Data & Storage
                      </h2>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Manage data refresh and retention settings
                    </p>
                  </div>

                  <div className="p-6 space-y-6">
                    {/* Auto-refresh toggle */}
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-start space-x-3">
                        <div className="p-2 bg-emerald-100 rounded-lg">
                          <RefreshCw className="w-4 h-4 text-emerald-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Auto-refresh experiment data
                          </p>
                          <p className="text-xs text-gray-500">
                            Automatically fetch latest experiment results
                          </p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          name="autoRefresh"
                          checked={settings.autoRefresh}
                          onChange={handleChange}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                      </label>
                    </div>

                    {/* Conditional refresh interval */}
                    {settings.autoRefresh && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="pl-14"
                      >
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Refresh Interval (seconds)
                        </label>
                        <div className="relative">
                          <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="number"
                            name="refreshInterval"
                            value={settings.refreshInterval}
                            onChange={handleChange}
                            min="10"
                            max="300"
                            className="w-64 pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                      </motion.div>
                    )}

                    {/* Data Retention */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Data Retention (days)
                      </label>
                      <div className="relative inline-block">
                        <Database className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <select
                          name="dataRetention"
                          value={settings.dataRetention}
                          onChange={handleChange}
                          className="w-64 pl-10 pr-8 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
                        >
                          <option value={7}>7 days</option>
                          <option value={30}>30 days</option>
                          <option value={60}>60 days</option>
                          <option value={90}>90 days</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Notifications Settings */}
              {activeTab === "notifications" && (
                <motion.div
                  variants={item}
                  className="bg-white rounded-2xl border border-gray-100 overflow-hidden"
                >
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-transparent">
                    <div className="flex items-center">
                      <Bell className="w-5 h-5 text-amber-600 mr-2" />
                      <h2 className="text-lg font-semibold text-gray-900">
                        Notifications
                      </h2>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Configure how and when you receive alerts
                    </p>
                  </div>

                  <div className="p-6 space-y-4">
                    {[
                      {
                        name: "notifications",
                        label: "Experiment completion",
                        description: "Get notified when experiments finish",
                        icon: CheckCircle2,
                        color: "amber",
                      },
                      {
                        name: "emailReports",
                        label: "Email reports",
                        description: "Receive daily summary via email",
                        icon: Globe,
                        color: "blue",
                      },
                    ].map((item) => (
                      <div
                        key={item.name}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
                      >
                        <div className="flex items-start space-x-3">
                          <div
                            className={`p-2 bg-${item.color}-100 rounded-lg`}
                          >
                            <item.icon
                              className={`w-4 h-4 text-${item.color}-600`}
                            />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {item.label}
                            </p>
                            <p className="text-xs text-gray-500">
                              {item.description}
                            </p>
                          </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            name={item.name}
                            checked={settings[item.name]}
                            onChange={handleChange}
                            className="sr-only peer"
                          />
                          <div
                            className={`w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-${item.color}-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-${item.color}-600`}
                          ></div>
                        </label>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Advanced Settings */}
              {activeTab === "advanced" && (
                <motion.div
                  variants={item}
                  className="bg-white rounded-2xl border border-gray-100 overflow-hidden"
                >
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-transparent">
                    <div className="flex items-center">
                      <Shield className="w-5 h-5 text-rose-600 mr-2" />
                      <h2 className="text-lg font-semibold text-gray-900">
                        Advanced Settings
                      </h2>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Configure advanced platform options
                    </p>
                  </div>

                  <div className="p-6">
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                      <div className="flex items-start">
                        <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-amber-800">
                            Warning
                          </p>
                          <p className="text-xs text-amber-700 mt-1">
                            These settings may affect platform performance.
                            Please proceed with caution.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <button className="w-full text-left p-4 border border-gray-200 rounded-xl hover:border-gray-300 hover:bg-gray-50 transition-colors">
                        <p className="text-sm font-medium text-gray-900">
                          Export all data
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Download all experiments and configurations
                        </p>
                      </button>

                      <button className="w-full text-left p-4 border border-gray-200 rounded-xl hover:border-red-300 hover:bg-red-50 transition-colors">
                        <p className="text-sm font-medium text-red-600">
                          Reset to defaults
                        </p>
                        <p className="text-xs text-red-500 mt-1">
                          Restore all settings to factory defaults
                        </p>
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
