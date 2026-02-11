import { useState } from 'react'
import { FaCog, FaSave, FaUser, FaPalette, FaMoon, FaSun, FaDatabase, FaChartBar } from 'react-icons/fa'
import { useTheme } from '../components/Themes/useThemeHeadless'

export default function Settings() {
    const { isDark, toggleTheme, setTheme } = useTheme();

    const [settings, setSettings] = useState({
        theme: isDark ? 'dark' : 'light',
        notifications: true,
        autoRefresh: true,
        refreshInterval: 30,
        showTutorials: true,
        defaultClients: 5,
        defaultEpochs: 10,
        chartType: 'line'
    })

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target
        setSettings(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }))
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        // Save settings logic would go here
        console.log('Settings saved:', settings)
        alert('Settings saved successfully!')
    }

    return (
        <div className="space-y-6">
            {/* Page header */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                    <FaCog className="text-blue-600 mr-2" />
                    Settings
                </h2>
                <p className="text-gray-600 mt-2">Configure your dashboard preferences</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main settings form */}
                <div className="lg:col-span-2 space-y-6">
                    {/* General Settings */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <FaUser className="text-gray-600 mr-2" />
                            General Settings
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Default Number of Clients
                                </label>
                                <input
                                    type="number"
                                    name="defaultClients"
                                    value={settings.defaultClients}
                                    onChange={handleChange}
                                    min="2"
                                    max="20"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Default Training Epochs
                                </label>
                                <input
                                    type="number"
                                    name="defaultEpochs"
                                    value={settings.defaultEpochs}
                                    onChange={handleChange}
                                    min="1"
                                    max="100"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="showTutorials"
                                    checked={settings.showTutorials}
                                    onChange={handleChange}
                                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                />
                                <label className="ml-2 block text-sm text-gray-700">
                                    Show tutorial tips
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Display Settings */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <FaPalette className="text-gray-600 mr-2" />
                            Display Settings
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Theme
                                </label>
                                <div className="flex space-x-4">
                                    <label className="flex items-center cursor-pointer">
                                        <input
                                            type="radio"
                                            name="theme"
                                            value="light"
                                            checked={settings.theme === 'light'}
                                            onChange={(e) => {
                                                handleChange(e)
                                                setTheme('light')
                                            }}
                                            className="sr-only"
                                        />
                                        <div className={`flex items-center px-4 py-2 rounded-lg border-2 ${settings.theme === 'light' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                                            <FaSun className="text-yellow-500 mr-2" />
                                            <span>Light</span>
                                        </div>
                                    </label>
                                    <label className="flex items-center cursor-pointer">
                                        <input
                                            type="radio"
                                            name="theme"
                                            value="dark"
                                            checked={settings.theme === 'dark'}
                                            onChange={(e) => {
                                                handleChange(e)
                                                setTheme('dark')
                                            }} className="sr-only"
                                        />
                                        <div className={`flex items-center px-4 py-2 rounded-lg border-2 ${settings.theme === 'dark' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                                            <FaMoon className="text-gray-600 mr-2" />
                                            <span>Dark</span>
                                        </div>
                                    </label>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Default Chart Type
                                </label>
                                <select
                                    name="chartType"
                                    value={settings.chartType}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="line">Line Chart</option>
                                    <option value="bar">Bar Chart</option>
                                    <option value="area">Area Chart</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Data Settings */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <FaDatabase className="text-gray-600 mr-2" />
                            Data Settings
                        </h3>
                        <div className="space-y-4">
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="autoRefresh"
                                    checked={settings.autoRefresh}
                                    onChange={handleChange}
                                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                />
                                <label className="ml-2 block text-sm text-gray-700">
                                    Auto-refresh experiment data
                                </label>
                            </div>
                            {settings.autoRefresh && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Refresh Interval (seconds)
                                    </label>
                                    <input
                                        type="number"
                                        name="refreshInterval"
                                        value={settings.refreshInterval}
                                        onChange={handleChange}
                                        min="10"
                                        max="300"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            )}
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="notifications"
                                    checked={settings.notifications}
                                    onChange={handleChange}
                                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                />
                                <label className="ml-2 block text-sm text-gray-700">
                                    Enable experiment completion notifications
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Save button */}
                    <div className="bg-white rounded-lg shadow p-6 text-right">
                        <button
                            onClick={handleSubmit}
                            className="inline-flex items-center bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        >
                            <FaSave className="mr-2" />
                            <span>Save Settings</span>
                        </button>
                    </div>
                </div>

                {/* Settings sidebar */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow p-6 sticky top-14">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <FaCog className="text-gray-600 mr-2" />
                            Quick Settings
                        </h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                                <div className="flex items-center">
                                    <FaChartBar className="text-blue-600 mr-3" />
                                    <span className="text-sm">Chart Preferences</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                                <div className="flex items-center">
                                    <FaDatabase className="text-green-600 mr-3" />
                                    <span className="text-sm">Data Export</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                                <div className="flex items-center">
                                    <FaUser className="text-purple-600 mr-3" />
                                    <span className="text-sm">User Profile</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
