import { useState, useEffect } from 'react'
import { architectureService } from '../services/api'
import { FaProjectDiagram, FaSpinner, FaExclamationTriangle, FaCode, FaInfoCircle, FaPlus } from 'react-icons/fa'
import { RenderJSONView } from '../components/jsonRenderer'
import { Link } from 'react-router-dom'

export default function Architectures() {
    const [architectures, setArchitectures] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedArchitecture, setSelectedArchitecture] = useState(null)

    useEffect(() => {
        const fetchArchitectures = async () => {
            try {
                setLoading(true)
                const response = await architectureService.getAll() //.getRegistry()
                setArchitectures(response.data)
                setLoading(false)
            } catch (err) {
                console.error('Error fetching architectures:', err)
                setError('Failed to load architectures. Please try again later.')
                setLoading(false)
            }
        }

        fetchArchitectures()
    }, [])

    const handleArchitectureClick = (architecture) => {
        setSelectedArchitecture(architecture)
    }

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow p-6 text-center">
                <FaSpinner className="animate-spin text-blue-600 text-2xl mx-auto mb-4" />
                <p className="text-gray-600">Loading architectures...</p>
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

                    <h2 className="text-2xl font-bold text-gray-800">Model Architectures</h2>
                    <Link
                        to="/architectures/new"
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                    >
                        <FaPlus className="mr-2" />
                        <span>New Architecture</span>
                    </Link>
                </div>
                <p className="text-gray-600 mt-2">
                    Browse and manage model architectures for federated learning
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Architectures list */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow p-4">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Available Architectures</h3>
                        <div className="space-y-2">
                            {architectures.map((arch) => (
                                <div
                                    key={arch.name}
                                    className={`p-3 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${selectedArchitecture?.name === arch.name ? 'bg-blue-50 border border-blue-200' : ''
                                        }`}
                                    onClick={() => handleArchitectureClick(arch)}
                                >
                                    <div className="flex items-center">
                                        <FaProjectDiagram className="text-blue-600 mr-3" />
                                        <div>
                                            <p className="font-medium text-gray-900">{arch.name}</p>
                                            <p className="text-sm text-gray-500">{arch.model_type}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Architecture details */}
                <div className="lg:col-span-2">
                    {selectedArchitecture ? (
                        <div className="bg-white rounded-lg shadow p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-bold text-gray-800 flex items-center">
                                        <FaProjectDiagram className="text-blue-600 mr-2" />
                                        {selectedArchitecture.name}
                                    </h3>
                                    <p className="text-gray-600 mt-1">{selectedArchitecture.description}</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${selectedArchitecture.compatible_datasets.length > 0
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                    }`}>
                                    {selectedArchitecture.model_type}
                                </span>
                            </div>

                            {/* Architecture info */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                                        <FaInfoCircle className="text-gray-600 mr-2" />
                                        Compatible Datasets
                                    </h4>
                                    <div className="space-y-1">
                                        {selectedArchitecture.compatible_datasets.length > 0 ? (
                                            selectedArchitecture.compatible_datasets.map((dataset, index) => (
                                                <div key={index} className="bg-white rounded px-2 py-1 text-sm">
                                                    {dataset}
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-sm text-gray-500">All datasets</p>
                                        )}
                                    </div>
                                </div>

                                <div className="bg-gray-50 rounded-lg p-4">
                                    <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                                        <FaCode className="text-gray-600 mr-2" />
                                        Architecture Type
                                    </h4>
                                    <p className="text-sm">{selectedArchitecture.model_type}</p>
                                </div>
                            </div>

                            {/* Architecture visualization placeholder */}
                            <div className="bg-gray-50 rounded-lg p-6 text-center mb-6">
                                <p className="text-gray-600 mb-4">Architecture Visualization</p>
                                <div className="bg-white rounded-lg p-8 border-2 border-dashed border-gray-300">
                                    <FaProjectDiagram className="text-gray-400 text-4xl mx-auto" />
                                    <p className="text-gray-500 mt-2">Interactive architecture diagram will be displayed here</p>
                                </div>
                            </div>

                            {/* Configuration details */}
                            <div className="bg-gray-50 rounded-lg p-4">
                                <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                                    <FaCode className="text-gray-600 mr-2" />
                                    Configuration Details
                                </h4>
                                <div className="overflow-x-auto">
                                    <RenderJSONView config={selectedArchitecture} />
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white rounded-lg shadow p-6 text-center">
                            <FaProjectDiagram className="text-gray-400 text-3xl mx-auto mb-4" />
                            <p className="text-gray-600">Select an architecture to view details</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
