import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { experimentService, datasetService, architectureService } from '../services/api'
import { FaFlask, FaPlus, FaSearch, FaSpinner, FaExclamationTriangle, FaPlay, FaStop, FaTrash, FaRedo, FaCheck, FaTimes } from 'react-icons/fa'

export default function Experiments() {
    const [experiments, setExperiments] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [datasets, setDatasets] = useState([])
    const [architectures, setArchitectures] = useState([])
    const [selectedExperiments, setSelectedExperiments] = useState([])
    const [actionMenuOpen, setActionMenuOpen] = useState(false)
    const [actionLoading, setActionLoading] = useState(false)
    const [actionResult, setActionResult] = useState(null)

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

    const toggleExperimentSelection = (experimentId) => {
        setSelectedExperiments(prev => {
            if (prev.includes(experimentId)) {
                return prev.filter(id => id !== experimentId)
            } else {
                return [...prev, experimentId]
            }
        })
    }

    const selectAll = () => {
        if (selectedExperiments.length === filteredExperiments.length) {
            setSelectedExperiments([])
        } else {
            setSelectedExperiments(filteredExperiments.map(exp => exp.id))
        }
    }

    const getAvailableActions = () => {
        if (selectedExperiments.length === 0) return []
        
        const selected = experiments.filter(exp => selectedExperiments.includes(exp.id))
        const hasRunning = selected.some(exp => exp.status === 'running')
        const hasPending = selected.some(exp => exp.status === 'pending')
        const hasCompleted = selected.some(exp => exp.status === 'completed')
        const hasCancelled = selected.some(exp => exp.status === 'cancelled')
        const hasFailed = selected.some(exp => exp.status === 'failed')
        
        const actions = []
        
        if (hasRunning || hasPending) {
            actions.push({ id: 'cancel', label: 'Cancel', icon: FaStop, color: 'text-yellow-600', bg: 'bg-yellow-50' })
        }
        
        if (hasCompleted || hasCancelled || hasFailed) {
            actions.push({ id: 'restart', label: 'Restart', icon: FaRedo, color: 'text-blue-600', bg: 'bg-blue-50' })
        }
        
        if (!hasRunning) {
            actions.push({ id: 'run', label: 'Run', icon: FaPlay, color: 'text-green-600', bg: 'bg-green-50' })
        }
        
        if (!hasRunning) {
            actions.push({ id: 'delete', label: 'Delete', icon: FaTrash, color: 'text-red-600', bg: 'bg-red-50' })
        }
        
        return actions
    }

    const performAction = async (action) => {
        setActionLoading(true)
        setActionResult(null)
        
        try {
            const response = await experimentService.batchActions({
                action: action.id,
                experiment_ids: selectedExperiments
            })
            
            setActionResult({
                type: 'success',
                message: `${action.label} ${response.successful} experiment(s) successfully`,
                errors: response.errors
            })
            
            // Refresh experiments list
            const experimentsResponse = await experimentService.getAll()
            setExperiments(experimentsResponse.data)
            setSelectedExperiments([])
            
        } catch (error) {
            console.error(`Error performing ${action.id} action:`, error)
            setActionResult({
                type: 'error',
                message: `Failed to perform ${action.label} action`
            })
        } finally {
            setActionLoading(false)
            setActionMenuOpen(false)
        }
    }

    const performSingleAction = async (experimentId, actionType) => {
        try {
            let response
            switch (actionType) {
                case 'run':
                    response = await experimentService.run(experimentId)
                    break
                case 'cancel':
                    response = await experimentService.cancel(experimentId)
                    break
                case 'delete':
                    response = await experimentService.delete(experimentId)
                    break
                case 'restart':
                    response = await experimentService.restart(experimentId)
                    break
                default:
                    return
            }
            
            // Refresh experiments list
            const experimentsResponse = await experimentService.getAll()
            setExperiments(experimentsResponse.data)
            
            return response
        } catch (error) {
            console.error(`Error performing ${actionType} action:`, error)
            throw error
        }
    }

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
                    <div className="flex items-center">
                        <h2 className="text-2xl font-bold text-gray-800">Experiments</h2>
                        {filteredExperiments.length > 0 && (
                            <button
                                onClick={selectAll}
                                className="ml-4 text-sm text-blue-600 hover:text-blue-700 flex items-center"
                            >
                                <FaCheck className="mr-1" />
                                {selectedExperiments.length === filteredExperiments.length ? 'Deselect All' : 'Select All'}
                            </button>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        {selectedExperiments.length > 0 && (
                            <button
                                onClick={() => setActionMenuOpen(!actionMenuOpen)}
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                            >
                                <span>Actions</span>
                                <span className="ml-2 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                    {selectedExperiments.length}
                                </span>
                            </button>
                        )}
                        <Link
                            to="/experiments/new"
                            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center"
                        >
                            <FaPlus className="mr-2" />
                            <span>New Experiment</span>
                        </Link>
                    </div>
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

            {/* Action Menu */}
            {actionMenuOpen && selectedExperiments.length > 0 && (
                <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">Actions for {selectedExperiments.length} experiment(s)</h3>
                            <button onClick={() => setActionMenuOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <FaTimes className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="space-y-3">
                            {getAvailableActions().map((action) => (
                                <button
                                    key={action.id}
                                    onClick={() => performAction(action)}
                                    disabled={actionLoading}
                                    className={`w-full flex items-center p-3 rounded-lg ${action.bg} hover:opacity-80 transition-opacity ${actionLoading ? 'opacity-50' : ''}`}
                                >
                                    <action.icon className={`w-5 h-5 ${action.color} mr-3`} />
                                    <span className="font-medium text-gray-900">{action.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Action Result Notification */}
            {actionResult && (
                <div className={`fixed top-4 right-4 z-50 bg-${actionResult.type === 'success' ? 'green' : 'red'}-100 border border-${actionResult.type === 'success' ? 'green' : 'red'}-400 text-${actionResult.type === 'success' ? 'green' : 'red'}-700 px-4 py-3 rounded-lg flex items-center`}>
                    <FaCheck className={`mr-2 ${actionResult.type === 'success' ? 'text-green-600' : 'text-red-600'}`} />
                    <span>{actionResult.message}</span>
                    {actionResult.errors && actionResult.errors.length > 0 && (
                        <button onClick={() => setActionResult(null)} className="ml-2 text-xs underline">Dismiss</button>
                    )}
                </div>
            )}

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
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                                        <input
                                            type="checkbox"
                                            checked={selectedExperiments.length === filteredExperiments.length && filteredExperiments.length > 0}
                                            onChange={selectAll}
                                            className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                                        />
                                    </th>
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
                                        <td className="px-4 py-4 whitespace-nowrap w-12">
                                            <input
                                                type="checkbox"
                                                checked={selectedExperiments.includes(experiment.id)}
                                                onChange={() => toggleExperimentSelection(experiment.id)}
                                                className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                                            />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <FaFlask className="text-blue-500 mr-2" />
                                                <Link to={`/experiments/${experiment.id}`} className="text-blue-600 hover:text-blue-800 font-medium">
                                                    {experiment.name}
                                                </Link>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{getDatasetName(experiment.dataset_name)}</div>
                                            <div className="text-xs text-gray-500">{experiment.dataset_name}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">{getArchitectureName(experiment.architecture_name)}</div>
                                            <div className="text-xs text-gray-500">{experiment.architecture_name}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-900">{experiment.num_clients}</span>
                                            <span className="text-xs text-gray-500 ml-1">
                                                ({experiment.iid ? 'IID' : 'Non-IID'})
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getStatusBadge(experiment.status)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="text-sm text-gray-900">
                                                {new Date(experiment.created_at).toLocaleDateString()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2">
                                                <Link
                                                    to={`/experiments/${experiment.id}`}
                                                    className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
                                                >
                                                    <span>View</span>
                                                </Link>
                                                {experiment.status === 'pending' && (
                                                    <button
                                                        onClick={() => performSingleAction(experiment.id, 'run')}
                                                        className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center"
                                                    >
                                                        <FaPlay className="mr-1" />
                                                        <span>Run</span>
                                                    </button>
                                                )}
                                                {experiment.status === 'running' && (
                                                    <button
                                                        onClick={() => performSingleAction(experiment.id, 'cancel')}
                                                        className="text-yellow-600 hover:text-yellow-700 text-sm font-medium flex items-center"
                                                    >
                                                        <FaStop className="mr-1" />
                                                        <span>Cancel</span>
                                                    </button>
                                                )}
                                                {(experiment.status === 'completed' || experiment.status === 'cancelled' || experiment.status === 'failed') && (
                                                    <button
                                                        onClick={() => performSingleAction(experiment.id, 'restart')}
                                                        className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
                                                    >
                                                        <FaRedo className="mr-1" />
                                                        <span>Restart</span>
                                                    </button>
                                                )}
                                                {experiment.status !== 'running' && (
                                                    <button
                                                        onClick={() => performSingleAction(experiment.id, 'delete')}
                                                        className="text-red-600 hover:text-red-700 text-sm font-medium flex items-center"
                                                    >
                                                        <FaTrash className="mr-1" />
                                                        <span>Delete</span>
                                                    </button>
                                                )}
                                            </div>
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
