import { FaSpinner } from 'react-icons/fa'

export default function Loading({ message = 'Loading...' }) {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
      <div className="text-center">
        <FaSpinner className="animate-spin text-blue-600 text-3xl mx-auto mb-4" />
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  )
}