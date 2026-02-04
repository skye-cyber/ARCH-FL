import { useEffect, useState } from 'react'
import { healthService, experimentService, datasetService } from '../services/api'
import { FaFlask, FaDatabase, FaProjectDiagram, FaChartLine } from 'react-icons/fa'

export default function Home() {
    const [stats, setStats] = useState({
        experiments: 0,
        datasets: 0,
        architectures: 0,
        status: 'loading'
    })

    useEffect(() => {
        const fetchStats = async () => {
            try {
                // Check backend health
                const healthResponse = await healthService.check()

                // Get experiments count
                const experimentsResponse = await experimentService.getAll()

                // Get datasets
                const datasetsResponse = await datasetService.getAll()

                setStats({
                    experiments: experimentsResponse.data.length,
                    datasets: datasetsResponse.data.length,
                    architectures: 4, // Will be dynamic later
                    status: healthResponse.data.status
                })
            } catch (error) {
                console.error('Error fetching stats:', error)
                setStats({ ...stats, status: 'error' })
            }
        }

        fetchStats()
    }, [])

    return (
        <div className="space-y-6">
            {/* Page header */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-800">ARCH-FL Dashboard</h2>
                <p className="text-gray-600 mt-2">
                    Federated Learning Platform for Medical Imaging
                </p>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow p-6 card-hover">
                    <div className="flex items-center">
                        <div className="bg-blue-100 p-3 rounded-full">
                            <FaFlask className="text-blue-600 text-xl" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-gray-500">Experiments</p>
                            <p className="text-2xl font-bold text-gray-800">{stats.experiments}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 card-hover">
                    <div className="flex items-center">
                        <div className="bg-green-100 p-3 rounded-full">
                            <FaDatabase className="text-green-600 text-xl" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-gray-500">Datasets</p>
                            <p className="text-2xl font-bold text-gray-800">{stats.datasets}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 card-hover">
                    <div className="flex items-center">
                        <div className="bg-purple-100 p-3 rounded-full">
                            <FaProjectDiagram className="text-purple-600 text-xl" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-gray-500">Architectures</p>
                            <p className="text-2xl font-bold text-gray-800">{stats.architectures}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 card-hover">
                    <div className="flex items-center">
                        <div className={`p-3 rounded-full ${stats.status === 'healthy' ? 'bg-green-100' : 'bg-yellow-100'}`}>
                            <FaChartLine className={`text-xl ${stats.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'}`} />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm text-gray-500">System Status</p>
                            <p className="text-2xl font-bold text-gray-800 capitalize">{stats.status}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Quick actions */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center hover:bg-blue-100 transition-colors cursor-pointer">
                        <FaFlask className="text-blue-600 text-2xl mx-auto mb-2" />
                        <p className="font-medium text-blue-800">Create Experiment</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center hover:bg-green-100 transition-colors cursor-pointer">
                        <FaProjectDiagram className="text-green-600 text-2xl mx-auto mb-2" />
                        <p className="font-medium text-green-800">Design Architecture</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center hover:bg-purple-100 transition-colors cursor-pointer">
                        <FaDatabase className="text-purple-600 text-2xl mx-auto mb-2" />
                        <p className="font-medium text-purple-800">Explore Datasets</p>
                    </div>
                </div>
            </div>

            {/* About section */}
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">About ARCH-FL</h3>
                <div className="space-y-4 text-gray-600">
                    <p>
                        ARCH-FL (Adaptive Resource-Constrained Healthcare Federated Learning) is a
                        platform designed for federated learning in medical imaging scenarios.
                    </p>
                    <p>
                        This dashboard provides a user-friendly interface to configure, monitor, and
                        analyze federated learning experiments across multiple clients while
                        preserving data privacy.
                    </p>
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-800 mb-2">Key Features:</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                            <li>Experiment configuration and management</li>
                            <li>Real-time monitoring of federated training</li>
                            <li>Interactive architecture design</li>
                            <li>Dataset exploration and visualization</li>
                            <li>Results comparison and analysis</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}
