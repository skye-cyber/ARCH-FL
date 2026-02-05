import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { architectureService } from '../services/api'
import { FaProjectDiagram, FaPlus, FaSave, FaCode, FaInfoCircle, FaDatabase } from 'react-icons/fa'

export default function ArchitectureCreate() {
  const navigate = useNavigate()
  const [architecture, setArchitecture] = useState({
    name: '',
    description: '',
    model_type: 'ConfigurableCNN',
    compatible_datasets: [],
    config: {
      input_channels: 1,
      conv_layers: [
        { out_channels: 32, kernel_size: 3, stride: 1, padding: 1 },
        { out_channels: 64, kernel_size: 3, stride: 1, padding: 1 }
      ],
      fc_layers: [
        { out_features: 128 },
        { out_features: 2 }
      ],
      activation: 'ReLU',
      pooling: 'MaxPool2d',
      pool_kernel: 2,
      dropout: 0.5
    }
  })
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    
    if (name === 'compatible_datasets') {
      const options = e.target.options
      const selected = []
      for (let i = 0; i < options.length; i++) {
        if (options[i].selected) {
          selected.push(options[i].value)
        }
      }
      setArchitecture(prev => ({ ...prev, [name]: selected }))
    } else if (name.startsWith('config.')) {
      const parts = name.split('.')
      if (parts.length === 2) {
        setArchitecture(prev => ({
          ...prev,
          config: { ...prev.config, [parts[1]]: value }
        }))
      } else if (parts.length === 3) {
        // Handle nested config like conv_layers[0].out_channels
        const [_, arrayName, index] = parts
        setArchitecture(prev => {
          const newConfig = { ...prev.config }
          const newArray = [...newConfig[arrayName]]
          newArray[index] = { ...newArray[index], [e.target.dataset.field]: value }
          newConfig[arrayName] = newArray
          return { ...prev, config: newConfig }
        })
      }
    } else {
      setArchitecture(prev => ({ ...prev, [name]: value }))
    }
  }

  const addConvLayer = () => {
    setArchitecture(prev => ({
      ...prev,
      config: {
        ...prev.config,
        conv_layers: [
          ...prev.config.conv_layers,
          { out_channels: 64, kernel_size: 3, stride: 1, padding: 1 }
        ]
      }
    }))
  }

  const removeConvLayer = (index) => {
    if (architecture.config.conv_layers.length > 1) {
      setArchitecture(prev => {
        const newConfig = { ...prev.config }
        const newLayers = prev.config.conv_layers.filter((_, i) => i !== index)
        newConfig.conv_layers = newLayers
        return { ...prev, config: newConfig }
      })
    }
  }

  const addFcLayer = () => {
    setArchitecture(prev => ({
      ...prev,
      config: {
        ...prev.config,
        fc_layers: [
          ...prev.config.fc_layers,
          { out_features: 64 }
        ]
      }
    }))
  }

  const removeFcLayer = (index) => {
    if (architecture.config.fc_layers.length > 1) {
      setArchitecture(prev => {
        const newConfig = { ...prev.config }
        const newLayers = prev.config.fc_layers.filter((_, i) => i !== index)
        newConfig.fc_layers = newLayers
        return { ...prev, config: newConfig }
      })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      const response = await architectureService.create(architecture)
      console.log('Architecture created:', response.data)
      setSuccess(true)
      
      // Reset form after 2 seconds
      setTimeout(() => {
        setSuccess(false)
        navigate('/architectures')
      }, 2000)
      
    } catch (err) {
      console.error('Error creating architecture:', err)
      setError('Failed to create architecture. Please check your inputs and try again.')
    }
  }

  const availableDatasets = [
    'pneumoniamnist',
    'mimic_cxr',
    'chexpert'
  ]

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <FaProjectDiagram className="text-blue-600 mr-2" />
          Create New Architecture
        </h2>
        <p className="text-gray-600 mt-2">Define a custom model architecture for federated learning</p>
      </div>

      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-center">
          <FaSave className="text-green-600 mr-2" />
          <span>Architecture created successfully! Redirecting...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex items-center">
          <FaExclamationTriangle className="text-red-600 mr-2" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <FaInfoCircle className="text-gray-600 mr-2" />
            Basic Information
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Architecture Name*
              </label>
              <input
                type="text"
                name="name"
                value={architecture.name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., CustomCNN"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={architecture.description}
                onChange={handleChange}
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Brief description of this architecture"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model Type*
              </label>
              <select
                name="model_type"
                value={architecture.model_type}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ConfigurableCNN">ConfigurableCNN</option>
                <option value="SimpleCNN">SimpleCNN</option>
                <option value="CustomCNN">CustomCNN</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Compatible Datasets
              </label>
              <select
                name="compatible_datasets"
                multiple
                value={architecture.compatible_datasets}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                size="3"
              >
                {availableDatasets.map(dataset => (
                  <option key={dataset} value={dataset}>
                    {dataset}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Hold Ctrl/Cmd to select multiple datasets. Leave empty for all datasets.
              </p>
            </div>
          </div>
        </div>

        {/* Architecture Configuration */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <FaCode className="text-gray-600 mr-2" />
            Architecture Configuration
          </h3>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Input Channels
              </label>
              <input
                type="number"
                name="config.input_channels"
                value={architecture.config.input_channels}
                onChange={handleChange}
                min="1"
                max="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Activation Function
              </label>
              <select
                name="config.activation"
                value={architecture.config.activation}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ReLU">ReLU</option>
                <option value="LeakyReLU">LeakyReLU</option>
                <option value="Sigmoid">Sigmoid</option>
                <option value="Tanh">Tanh</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pooling
              </label>
              <select
                name="config.pooling"
                value={architecture.config.pooling}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="MaxPool2d">MaxPool2d</option>
                <option value="AvgPool2d">AvgPool2d</option>
                <option value="None">None</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pool Kernel Size
              </label>
              <input
                type="number"
                name="config.pool_kernel"
                value={architecture.config.pool_kernel}
                onChange={handleChange}
                min="2"
                max="4"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dropout
              </label>
              <input
                type="number"
                name="config.dropout"
                value={architecture.config.dropout}
                onChange={handleChange}
                min="0"
                max="0.9"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Convolutional Layers */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Convolutional Layers
                </label>
                <button
                  type="button"
                  onClick={addConvLayer}
                  className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                >
                  <FaPlus className="mr-1" /> Add Layer
                </button>
              </div>
              <div className="space-y-3">
                {architecture.config.conv_layers.map((layer, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-800">Layer {index + 1}</h4>
                      {architecture.config.conv_layers.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeConvLayer(index)}
                          className="text-red-600 hover:text-red-800 text-xs"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <label className="block text-gray-600 text-xs mb-1">Out Channels</label>
                        <input
                          type="number"
                          name={`config.conv_layers.${index}`}
                          data-field="out_channels"
                          value={layer.out_channels}
                          onChange={handleChange}
                          min="16"
                          max="512"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </div>
                      <div>
                        <label className="block text-gray-600 text-xs mb-1">Kernel Size</label>
                        <input
                          type="number"
                          name={`config.conv_layers.${index}`}
                          data-field="kernel_size"
                          value={layer.kernel_size}
                          onChange={handleChange}
                          min="1"
                          max="7"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </div>
                      <div>
                        <label className="block text-gray-600 text-xs mb-1">Stride</label>
                        <input
                          type="number"
                          name={`config.conv_layers.${index}`}
                          data-field="stride"
                          value={layer.stride}
                          onChange={handleChange}
                          min="1"
                          max="3"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </div>
                      <div>
                        <label className="block text-gray-600 text-xs mb-1">Padding</label>
                        <input
                          type="number"
                          name={`config.conv_layers.${index}`}
                          data-field="padding"
                          value={layer.padding}
                          onChange={handleChange}
                          min="0"
                          max="3"
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Fully Connected Layers */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Fully Connected Layers
                </label>
                <button
                  type="button"
                  onClick={addFcLayer}
                  className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                >
                  <FaPlus className="mr-1" /> Add Layer
                </button>
              </div>
              <div className="space-y-3">
                {architecture.config.fc_layers.map((layer, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-800">Layer {index + 1}</h4>
                      {architecture.config.fc_layers.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeFcLayer(index)}
                          className="text-red-600 hover:text-red-800 text-xs"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                    <div className="text-sm">
                      <label className="block text-gray-600 text-xs mb-1">Out Features</label>
                      <input
                        type="number"
                        name={`config.fc_layers.${index}`}
                        data-field="out_features"
                        value={layer.out_features}
                        onChange={handleChange}
                        min="16"
                        max="4096"
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={() => navigate('/architectures')}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              <FaSave className="mr-2" />
              <span>Save Architecture</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}