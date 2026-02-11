import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { experimentService, datasetService, architectureService } from '../services/api'
import { FaFlask, FaPlus, FaSearch, FaSpinner, FaExclamationTriangle } from 'react-icons/fa'

export default function Experiments() {
    const [experiments, setExperiments] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [datasets, setDatasets] = useState([])
    const [architectures, setArchitectures] = useState([])

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)

                // Fetch experiments
                const experimentsResponse = await experimentService.getAll()
                setExperiments(experimentsResponse.data)

                // Fetch datasets
                const datasetsResponse = await datasetService.getAll()
                setDatasets(datasetsResponse.data)

                // Fetch architectures
                const architecturesResponse = await architectureService.getRegistry()
                setArchitectures(architecturesResponse.data)

                setLoading(false)
            } catch (err) {
                console.error('Error fetching experiments:', err)
                setError('Failed to load experiments. Please try again later.')
                setLoading(false)
            }
        }

        fetchData()
    }, [])

    const filteredExperiments = experiments.filter(experiment =>
        experiment.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        experiment.dataset_name.toLowerCase().includes(searchTerm.toLowerCase())
    )

    // Get dataset and architecture names for display
    const getDatasetName = (datasetName) => {
        const dataset = datasets.find(d => d.name === datasetName)
        return dataset ? dataset.description : datasetName
    }

    const getArchitectureName = (archName) => {
        const arch = architectures.find(a => a.name === archName)
        return arch ? arch.description : archName
    }

    const getStatusBadge = (status) => {
        const statusClasses = {
            pending: 'bg-yellow-100 text-yellow-800',
            running: 'bg-blue-100 text-blue-800',
            completed: 'bg-green-100 text-green-800',
            failed: 'bg-red-100 text-red-800'
        }

        return (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClasses[status] || 'bg-gray-100 text-gray-800'}`}>
                {status}
            </span>
        )
    }

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow p-6 text-center">
                <FaSpinner className="animate-spin text-blue-600 text-2xl mx-auto mb-4" />
                <p className="text-gray-600">Loading experiments...</p>
            </div>
        )
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
        )
    }

    return (
        <div className="space-y-6">
            {/* Page header */}
            <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-2xl font-bold text-gray-800">Experiments</h2>
                    <Link
                        to="/experiments/new"
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                    >
                        <FaPlus className="mr-2" />
                        <span>New Experiment</span>
                    </Link>
                </div>
                <p className="text-gray-600 mt-2">Manage and monitor your federated learning experiments</p>
            </div>

            {/* Search and filters */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center">
                    <div className="relative flex-1">
                        <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search experiments..."
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* Experiments list */}
            <div className="bg-white rounded-lg shadow">
                {filteredExperiments.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">
                        <FaFlask className="text-3xl mx-auto mb-4 text-gray-300" />
                        <p>No experiments found</p>
                        {searchTerm && (
                            <p className="text-sm mt-2">Try clearing your search or creating a new experiment</p>
                        )}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Architecture</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Clients</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredExperiments.map((experiment) => (
                                    <tr key={experiment.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <div className="flex items-center">
                                                <FaFlask className="text-blue-500 mr-2" />
                                                <Link to={`/experiments/${experiment.id}`} className="text-blue-600 hover:text-blue-800 font-medium">
                                                    {experiment.name}
                                                </Link>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <div className="text-sm text-gray-900">{getDatasetName(experiment.dataset_name)}</div>
                                            <div className="text-xs text-gray-500">{experiment.dataset_name}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <div className="text-sm text-gray-900">{getArchitectureName(experiment.architecture_name)}</div>
                                            <div className="text-xs text-gray-500">{experiment.architecture_name}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <span className="text-sm text-gray-900">{experiment.num_clients}</span>
                                            <span className="text-xs text-gray-500 ml-1">
                                                ({experiment.iid ? 'IID' : 'Non-IID'})
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            {getStatusBadge(experiment.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <span className="text-sm text-gray-900">
                                                {new Date(experiment.created_at).toLocaleDateString()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-wrap">
                                            <Link
                                                to={`/experiments/${experiment.id}`}
                                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                            >
                                                View Details
                                            </Link>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
