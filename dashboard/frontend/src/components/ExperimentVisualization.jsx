import { FaServer, FaDatabase, FaProjectDiagram, FaChartLine, FaSyncAlt } from 'react-icons/fa'

export default function ExperimentVisualization({ experiment }) {
  if (!experiment) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <FaProjectDiagram className="text-gray-400 text-3xl mx-auto mb-4" />
        <p className="text-gray-600">Select an experiment to view visualization</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <FaProjectDiagram className="text-blue-600 mr-2" />
        Experiment Visualization
      </h3>

      <div className="space-y-6">
        {/* Federated Learning Process */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-800 mb-3">Federated Learning Process</h4>
          <div className="flex items-center justify-center space-x-8">
            {/* Global Model */}
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                <FaServer className="text-blue-600 text-xl" />
              </div>
              <p className="text-sm font-medium">Global Model</p>
            </div>

            {/* Arrow */}
            <div className="flex items-center">
              <FaSyncAlt className="text-gray-400 text-xl mx-4" />
            </div>

            {/* Clients */}
            <div className="flex space-x-4">
              {[1, 2, 3].map((client) => (
                <div key={client} className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-1">
                    <FaDatabase className="text-green-600 text-lg" />
                  </div>
                  <p className="text-xs font-medium">Client {client}</p>
                </div>
              ))}
              {experiment.num_clients > 3 && (
                <div className="text-center">
                  <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-1">
                    <span className="text-gray-600 font-medium">+{experiment.num_clients - 3}</span>
                  </div>
                  <p className="text-xs font-medium">More</p>
                </div>
              )}
            </div>

            {/* Arrow */}
            <div className="flex items-center">
              <FaSyncAlt className="text-gray-400 text-xl mx-4" />
            </div>

            {/* Updated Model */}
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                <FaChartLine className="text-blue-600 text-xl" />
              </div>
              <p className="text-sm font-medium">Updated Model</p>
            </div>
          </div>
        </div>

        {/* Experiment Info Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <p className="text-xs text-blue-600 uppercase tracking-wide mb-1">Dataset</p>
            <p className="font-medium text-blue-800">{experiment.dataset_name}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <p className="text-xs text-green-600 uppercase tracking-wide mb-1">Architecture</p>
            <p className="font-medium text-green-800">{experiment.architecture_name}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3 text-center">
            <p className="text-xs text-purple-600 uppercase tracking-wide mb-1">Clients</p>
            <p className="font-medium text-purple-800">{experiment.num_clients}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-3 text-center">
            <p className="text-xs text-yellow-600 uppercase tracking-wide mb-1">Distribution</p>
            <p className="font-medium text-yellow-800">{experiment.iid ? 'IID' : 'Non-IID'}</p>
          </div>
        </div>

        {/* Training Parameters */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-800 mb-3">Training Parameters</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Epochs:</span>
              <span className="font-medium">{experiment.parameters?.epochs || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Batch Size:</span>
              <span className="font-medium">{experiment.parameters?.batch_size || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Learning Rate:</span>
              <span className="font-medium">{experiment.parameters?.learning_rate || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-600 mb-2">Current Status</p>
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
            experiment.status === 'completed' ? 'bg-green-100 text-green-800' :
            experiment.status === 'running' ? 'bg-blue-100 text-blue-800' :
            experiment.status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {experiment.status === 'completed' && '✅ Completed'}
            {experiment.status === 'running' && '⏳ Running'}
            {experiment.status === 'failed' && '❌ Failed'}
            {experiment.status === 'pending' && '⏰ Pending'}
          </div>
        </div>
      </div>
    </div>
  )
}